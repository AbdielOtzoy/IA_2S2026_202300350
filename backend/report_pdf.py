"""Generación de informes PDF con trazabilidad del análisis."""

from __future__ import annotations

from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


NAVY = colors.HexColor("#16324F")
TEAL = colors.HexColor("#0B7285")
PALE = colors.HexColor("#E8F3F5")
GRAY = colors.HexColor("#52606D")


def _text(value: Any) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_analysis_pdf(response: dict[str, Any]) -> bytes:
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="MLTitle", parent=styles["Title"], fontName="Helvetica-Bold", textColor=NAVY, fontSize=22, leading=26, alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="MLHeading", parent=styles["Heading2"], fontName="Helvetica-Bold", textColor=NAVY, fontSize=13, leading=16, spaceBefore=10, spaceAfter=6))
    styles.add(ParagraphStyle(name="MLBody", parent=styles["BodyText"], fontName="Helvetica", textColor=colors.HexColor("#243B53"), fontSize=9, leading=13))
    styles.add(ParagraphStyle(name="MLSmall", parent=styles["BodyText"], fontName="Helvetica", textColor=GRAY, fontSize=8, leading=10))
    styles.add(ParagraphStyle(name="MLWarning", parent=styles["BodyText"], fontName="Helvetica-Bold", textColor=colors.HexColor("#7A4E00"), fontSize=9, leading=12))

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title="Informe MediLogic",
        author="MediLogic",
    )
    story = [
        Paragraph("MediLogic", styles["MLTitle"]),
        Paragraph("Informe de orientación preliminar", styles["MLBody"]),
        Spacer(1, 8),
        HRFlowable(width="100%", thickness=1, color=TEAL),
        Spacer(1, 10),
        Paragraph(f"<b>Identificador:</b> {_text(response['analysis_id'])}<br/><b>Fecha UTC:</b> {_text(response['created_at'])}", styles["MLBody"]),
        Spacer(1, 8),
        Paragraph("Advertencia médica", styles["MLHeading"]),
        Paragraph("Este documento es un prototipo académico de orientación preliminar. No es un diagnóstico, no sustituye a un profesional de la salud y no constituye una prescripción. Ante síntomas severos o de alarma, busque atención inmediata.", styles["MLWarning"]),
        Spacer(1, 8),
        Paragraph("Criterio de afinidad", styles["MLHeading"]),
        Paragraph(_text(response["formula"]), styles["MLBody"]),
        Paragraph(f"<b>Urgencia global:</b> {_text(response['global_urgency']['action'])}", styles["MLBody"]),
    ]

    diagnoses = response.get("diagnoses", [])
    story.append(Paragraph("Diagnósticos sugeridos", styles["MLHeading"]))
    if not diagnoses:
        story.append(Paragraph("No se encontraron coincidencias suficientes en la base de conocimiento.", styles["MLBody"]))
    for index, diagnosis in enumerate(diagnoses, start=1):
        story.extend(
            [
                Paragraph(f"{index}. {_text(diagnosis['disease_name'])} - {_text(diagnosis['affinity'])}%", styles["MLHeading"]),
                Paragraph(f"{_text(diagnosis['description'])}<br/><b>Clasificación:</b> {_text(diagnosis['system'])} / {_text(diagnosis['type'])}<br/><b>Puntos:</b> {_text(diagnosis['points_obtained'])} de {_text(diagnosis['points_maximum'])}<br/><b>Urgencia:</b> {_text(diagnosis['urgency']['action'])}", styles["MLBody"]),
            ]
        )
        coincidence_rows = [["Síntoma", "Severidad", "Peso"]]
        coincidence_rows.extend([[item["symptom_name"], item["severity"], str(item["weight"])] for item in diagnosis.get("coincidences", [])])
        table = Table(coincidence_rows, colWidths=[3.8 * inch, 1.2 * inch, 0.7 * inch], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E0")),
            ("BACKGROUND", (0, 1), (-1, -1), PALE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.extend([table, Spacer(1, 5)])
        safe = diagnosis.get("safe_medications", [])
        selected = diagnosis.get("recommended_medication")
        safe_text = ", ".join(item["medication_name"] for item in safe) if safe else "No existe una opción segura registrada."
        if selected:
            safe_text += f". Candidato principal: {selected['medication_name']}."
        story.append(Paragraph(f"<b>Medicamentos seguros:</b> {_text(safe_text)}", styles["MLBody"]))
        discarded = diagnosis.get("discarded_medications", [])
        if discarded:
            discarded_text = "; ".join(f"{item['medication_name']}: {item['reason']}" for item in discarded)
            story.append(Paragraph(f"<b>Descartados:</b> {_text(discarded_text)}", styles["MLSmall"]))
        rule_text = "; ".join(f"{item['rule']}: {item['explanation']}" for item in diagnosis.get("activated_rules", []))
        story.append(Paragraph(f"<b>Reglas activadas:</b> {_text(rule_text or 'No se registraron reglas adicionales.')}", styles["MLSmall"]))
        story.append(Spacer(1, 8))

    story.append(Paragraph("Advertencias", styles["MLHeading"]))
    for warning in response.get("warnings", []):
        story.append(Paragraph(f"- {_text(warning)}", styles["MLBody"]))

    def footer(canvas, document):
        canvas.saveState()
        width, height = letter
        canvas.setStrokeColor(TEAL)
        canvas.circle(width - 0.75 * inch, 0.45 * inch, 0.19 * inch, stroke=1, fill=0)
        canvas.setFont("Helvetica-Bold", 7)
        canvas.setFillColor(TEAL)
        canvas.drawCentredString(width - 0.75 * inch, 0.42 * inch, "ML")
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(GRAY)
        canvas.drawString(0.55 * inch, 0.42 * inch, "MediLogic - prototipo académico")
        canvas.drawRightString(width - 1.1 * inch, 0.42 * inch, f"Página {document.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()

