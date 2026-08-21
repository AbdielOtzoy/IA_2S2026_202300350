"""Genera los manuales PDF de la entrega con ReportLab."""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Flowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "output" / "pdf"
NAVY = colors.HexColor("#16324F")
TEAL = colors.HexColor("#0B7285")
MINT = colors.HexColor("#E8F3F5")
TEXT = colors.HexColor("#243B53")
MUTED = colors.HexColor("#627D98")


class ArchitectureDiagram(Flowable):
    def __init__(self, width=7.2 * inch, height=2.2 * inch):
        super().__init__()
        self.width = width
        self.height = height

    def draw(self):
        canvas = self.canv
        boxes = [
            (0.05, 0.58, 0.18, 0.25, "React\nVite"),
            (0.30, 0.58, 0.18, 0.25, "FastAPI"),
            (0.55, 0.58, 0.20, 0.25, "pyswip\nProlog"),
            (0.81, 0.58, 0.15, 0.25, "medilogic\n.pl"),
        ]
        canvas.setFont("Helvetica-Bold", 8)
        for x, y, w, h, label in boxes:
            canvas.setFillColor(MINT)
            canvas.setStrokeColor(TEAL)
            canvas.roundRect(self.width * x, self.height * y, self.width * w, self.height * h, 7, fill=1, stroke=1)
            canvas.setFillColor(NAVY)
            lines = label.split("\n")
            for index, line in enumerate(lines):
                canvas.drawCentredString(self.width * (x + w / 2), self.height * (y + h / 2) + (4 if index == 0 and len(lines) > 1 else -3), line)
        canvas.setStrokeColor(TEAL)
        canvas.setLineWidth(1.2)
        for start, end in [(0.23, 0.30), (0.48, 0.55), (0.75, 0.81)]:
            canvas.line(self.width * start, self.height * .705, self.width * end, self.height * .705)
            canvas.line(self.width * end - 4, self.height * .705 + 3, self.width * end, self.height * .705)
            canvas.line(self.width * end - 4, self.height * .705 - 3, self.width * end, self.height * .705)
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica", 8)
        canvas.drawCentredString(self.width * .5, self.height * .28, "JSON estructurado + regeneración y recarga bajo bloqueo")


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("MLTitle", parent=base["Title"], fontName="Helvetica-Bold", fontSize=25, leading=29, textColor=NAVY, alignment=TA_CENTER, spaceAfter=8),
        "subtitle": ParagraphStyle("MLSubtitle", parent=base["Normal"], fontName="Helvetica", fontSize=11, leading=15, textColor=MUTED, alignment=TA_CENTER, spaceAfter=22),
        "h1": ParagraphStyle("MLH1", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=17, leading=21, textColor=NAVY, spaceBefore=12, spaceAfter=8),
        "h2": ParagraphStyle("MLH2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=12, leading=15, textColor=TEAL, spaceBefore=8, spaceAfter=5),
        "body": ParagraphStyle("MLBody", parent=base["BodyText"], fontName="Helvetica", fontSize=9.5, leading=14, textColor=TEXT, spaceAfter=7),
        "small": ParagraphStyle("MLSmall", parent=base["BodyText"], fontName="Helvetica", fontSize=8, leading=11, textColor=MUTED, spaceAfter=5),
        "callout": ParagraphStyle("MLCallout", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=9.5, leading=14, textColor=colors.HexColor("#315C65"), backColor=MINT, borderColor=colors.HexColor("#C7E7E7"), borderWidth=0.6, borderPadding=9, spaceBefore=5, spaceAfter=10),
    }


def p(text, style):
    return Paragraph(escape(text).replace("\n", "<br/>"), style)


def rich(text, style):
    return Paragraph(text, style)


def footer(canvas, document):
    canvas.saveState()
    canvas.setStrokeColor(TEAL)
    canvas.setLineWidth(.5)
    canvas.line(.55 * inch, .55 * inch, 7.95 * inch, .55 * inch)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(.55 * inch, .37 * inch, "MediLogic - documentación académica")
    canvas.drawRightString(7.95 * inch, .37 * inch, f"Página {document.page}")
    canvas.restoreState()


def cover(title, subtitle, style):
    return [Spacer(1, 1.0 * inch), rich('<font color="#0B7285"><b>MEDILOGIC</b></font>', style["subtitle"]), p(title, style["title"]), p(subtitle, style["subtitle"]), ArchitectureDiagram(), Spacer(1, .45 * inch), rich('<b>Advertencia:</b> prototipo académico de orientación preliminar. No es diagnóstico ni prescripción.', style["callout"]), PageBreak()]


def build_manual_tecnico():
    s = styles()
    story = cover("Manual técnico", "Arquitectura, reglas Prolog, seguridad, RPA y decisiones de implementación", s)
    story += [p("1. Propósito y alcance", s["h1"]), p("MediLogic recibe síntomas sintéticos, severidades, alergias, antecedentes y tratamientos actuales. La API coordina un archivo JSON estructurado y una representación Prolog generada. El resultado conserva las coincidencias, los pesos, la urgencia, las reglas y los medicamentos descartados.", s["body"]), p("La herramienta es educativa. No debe usarse para diagnosticar, prescribir ni reemplazar atención profesional.", s["callout"]), p("2. Componentes", s["h1"]), p("React/Vite presenta el flujo de paciente y el panel administrativo. FastAPI valida el contrato HTTP y protege las rutas administrativas. KnowledgeRepository ejecuta transacciones de persistencia y PrologEngine consulta SWI-Prolog mediante pyswip. ReportLab crea informes PDF y rpa/importer.py procesa el TXT provisional.", s["body"]), p("3. Modelo de conocimiento", s["h1"]), rich("<b>Entidades:</b> síntomas (id, nombre, descripción, alarma), enfermedades (clasificación, antecedentes, síntomas y medicamentos), medicamentos y contraindicaciones. El JSON es la fuente CRUD; el archivo .pl se regenera completo para mantener una estructura controlada.", s["body"]), p("4. Fórmula de afinidad", s["h1"])]
    formula = Table([["Elemento", "Regla"], ["Peso", "leve=1 · moderado=2 · severo=3"], ["Máximo", "cantidad de síntomas de la enfermedad * 3"], ["Afinidad", "puntos_obtenidos / puntos_maximos * 100"]], colWidths=[1.35 * inch, 5.75 * inch])
    formula.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), .3, colors.HexColor("#CBD5E0")), ("BACKGROUND", (0, 1), (-1, -1), MINT), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTNAME", (0, 1), (-1, -1), "Helvetica"), ("FONTSIZE", (0, 0), (-1, -1), 8.5), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    story += [formula, Spacer(1, 8), p("El cálculo vive en Prolog, se redondea a dos decimales y se limita a 100%. La aplicación no mezcla puntos con porcentajes.", s["body"]), p("5. Reglas de inferencia", s["h1"]), p("diagnosis_metrics/6 obtiene coincidencias y suma pesos. matched_symptom/5 conserva el detalle. urgency/4 prioriza síntomas severos y banderas de alarma; después evalúa síntomas moderados y finalmente un perfil compuesto solo por síntomas leves.", s["body"]), p("medication_evaluation/8 descarta en este orden: alergia directa, condición crónica, contraindicación con la enfermedad diagnosticada e incompatibilidad con un tratamiento actual. Si no queda un candidato, la respuesta conserva una advertencia y no inventa una opción.", s["body"]), PageBreak(), p("6. Actualización y rollback", s["h1"]), p("Una operación administrativa valida el modelo Pydantic y las referencias. Luego genera archivos temporales, compila el .pl con SWI-Prolog, reemplaza JSON y Prolog de forma atómica y ejecuta load_files/2 con recarga forzada bajo un RLock. Si la recarga falla, restaura los bytes anteriores y registra el error para evitar un estado parcial.", s["body"]), p("7. Autenticación", s["h1"]), p("El usuario y un hash PBKDF2 se leen desde variables de entorno. El login entrega un token temporal almacenado solo en memoria. Todas las rutas administrativas exigen Authorization: Bearer. CORS usa orígenes explícitos.", s["body"]), p("8. RPA", s["h1"]), p("La primera versión acepta un TXT UTF-8 con JSON. El adaptador valida extensión, tamaño, contenido, identificadores y relaciones. La carga de ejemplo agrega tres enfermedades, clasifica por sistema/tipo, regenera el conocimiento, recarga el motor y crea logs/rpa_*.txt. PyAutoGUI y TagUI quedan pendientes de confirmación docente.", s["body"]), p("9. Verificación", s["h1"]), rich('<b>Backend:</b> <font name="Courier">pytest</font><br/><b>Frontend:</b> <font name="Courier">cd frontend &amp;&amp; npm run build</font><br/><b>Prolog:</b> <font name="Courier">python -m scripts.generate_prolog</font>', s["body"]), p("10. Despliegue pendiente", s["h1"]), p("GitHub Pages no ejecuta FastAPI, SWI-Prolog ni pyswip. El repositorio mantiene la decisión local-first hasta confirmar con el docente si el frontend se publicará en Pages y el backend en otro entorno permitido.", s["callout"])]
    return story


def build_manual_usuario():
    s = styles()
    story = cover("Manual de usuario", "Guía del módulo de paciente, resultados, PDF, administración y RPA", s)
    story += [p("1. Módulo de paciente", s["h1"]), p("Desde la pantalla inicial, pulse Iniciar análisis. El catálogo se carga dinámicamente desde el backend; no es una lista duplicada en la interfaz.", s["body"]), p("Paso 1 - Seleccione síntomas y elija una severidad para cada uno. Leve aporta 1 punto, moderado 2 y severo 3.", s["body"]), p("Paso 2 - Marque alergias y antecedentes si aplican. Los tratamientos actuales son opcionales, pero ayudan a detectar incompatibilidades.", s["body"]), p("Paso 3 - Ejecute el análisis. El sistema ordena enfermedades por afinidad y muestra el desglose de puntos.", s["body"]), p("2. Leer los resultados", s["h1"]), p("Cada tarjeta contiene clasificación, porcentaje, puntos máximos, síntomas coincidentes, severidad, peso y urgencia. La sección de reglas Prolog explica cómo se activó el resultado.", s["body"]), p("Una urgencia inmediata indica un síntoma severo o de alarma. Observación recomendada indica síntomas moderados. Posible automanejo orientativo solo describe el caso controlado de síntomas leves y no sustituye una consulta.", s["callout"]), p("3. Medicamentos", s["h1"]), p("Los candidatos seguros se separan de los descartados. Los descartes explican alergia, antecedente, enfermedad o tratamiento incompatible. Si no existe alternativa segura, se muestra la advertencia y el campo de recomendado queda vacío.", s["body"]), p("4. Historial y PDF", s["h1"]), p("Los resúmenes recientes se conservan únicamente durante la sesión activa en sessionStorage. Descargar PDF genera fecha, fórmula, diagnósticos, coincidencias, urgencia, medicamentos, descartes y reglas activadas.", s["body"]), PageBreak(), p("5. Panel administrativo", s["h1"]), p("Entre desde Administración. El usuario y el hash se configuran por entorno; nunca se escriben credenciales en el repositorio. El panel permite crear síntomas, medicamentos y enfermedades, revisar los registros y descargar medilogic.pl.", s["body"]), p("Cada enfermedad debe usar ids existentes en sus relaciones. El sistema rechaza eliminaciones que dejarían referencias inválidas. Después de cada cambio se valida el JSON, se recompila el Prolog, se recarga el motor y se registra la operación.", s["body"]), p("6. Ejecutar el RPA", s["h1"]), p("Seleccione un archivo .txt con JSON UTF-8 desde el panel y pulse Ejecutar RPA. También puede reproducirse por CLI: python -m rpa.cli rpa/examples/carga_tres_enfermedades.txt. La bitácora se genera en logs/rpa_*.txt.", s["body"]), p("7. Errores comunes", s["h1"]), p("Catálogo no disponible: verifique que backend y SWI-Prolog estén activos. Referencia inexistente: cree primero el registro relacionado. No se puede eliminar: quite la relación antes. Credenciales inválidas: regenere el hash con python -m backend.auth --hash.", s["body"]), p("Advertencia final", s["h1"]), p("MediLogic es un prototipo académico de orientación preliminar. Ante síntomas severos o de alarma, busque atención médica inmediata.", s["callout"])]
    return story


def build_cases():
    s = styles()
    story = cover("Casos clínicos sintéticos", "Tres pruebas de coherencia y reflexión crítica sobre IA simbólica", s)
    cases = [
        ("Caso 1 - Influenza con alergia", "Entrada: tos moderada, fiebre severa y alergia a ibuprofeno. Influenza obtiene 5/12 = 41.67%; tos aporta 2 y fiebre 3. La urgencia es inmediata. Ibuprofeno se descarta por alergia y paracetamol queda como candidato sintético seguro.", "La salida es coherente con la base controlada y muestra que la severidad cambia la afinidad. El porcentaje no es una probabilidad clínica."),
        ("Caso 2 - Resfriado con antecedente", "Entrada: tos leve, antecedente de hipertensión y tratamiento actual warfarina. Resfriado común obtiene 1/12 = 8.33%. Ibuprofeno se descarta por hipertensión; el sistema conserva paracetamol y loratadina como candidatos sintéticos.", "El filtro evita el candidato conflictivo y documenta la causa. El prototipo no determina dosis ni indica iniciar un tratamiento."),
        ("Caso 3 - Rinitis parcial", "Entrada: estornudos moderados, congestión nasal leve y alergia a paracetamol. Rinitis alérgica obtiene 3/9 = 33.33%; estornudos aporta 2 y congestión 1. La urgencia es observación; loratadina queda disponible.", "La enfermedad aparece por coincidencia parcial y el informe conserva el desglose de puntos."),
    ]
    for title, result, coherence in cases:
        story += [p(title, s["h1"]), rich(f"<b>Resultado:</b> {escape(result)}", s["body"]), rich(f"<b>Coherencia:</b> {escape(coherence)}", s["body"]), Spacer(1, 8)]
    story += [PageBreak(), p("Reflexión crítica", s["h1"]), p("El enfoque simbólico de MediLogic ofrece una ventaja clara: cada conclusión puede relacionarse con un hecho y una regla visible. Se puede explicar por qué una coincidencia aportó uno, dos o tres puntos, cuál condición disparó la urgencia y por qué un medicamento fue descartado. Esta trazabilidad es valiosa en un prototipo educativo, pero no convierte el porcentaje calculado en una probabilidad médica. El motor solo conoce las relaciones escritas en el catálogo; si aparece un síntoma ambiguo, una combinación no contemplada o una presentación atípica, el resultado puede ser parcial o vacío.", s["body"]), p("Un modelo de aprendizaje automático o probabilístico podría aprender asociaciones a partir de muchos casos reales y producir una distribución condicionada por contexto, evolución y otras variables. Ese enfoque puede manejar mejor ciertas correlaciones, pero requiere datos de calidad, validación clínica, control de sesgos y explicaciones. Las reglas fijas son fáciles de auditar, aunque no estiman sensibilidad, especificidad ni riesgo poblacional. La afinidad de MediLogic es una métrica transparente de cobertura de síntomas.", s["body"]), p("La escalabilidad también cambia. Con pocas enfermedades, una persona puede revisar las relaciones del JSON y regenerar el .pl. Con miles de enfermedades, síntomas, tratamientos y excepciones, crece el costo de mantenimiento y aparecen conflictos entre expertos. Pipelines de datos, modelos probabilísticos o agentes pueden ayudar a buscar relaciones, pero la supervisión humana y la procedencia de los datos siguen siendo indispensables.", s["body"]), p("Una arquitectura híbrida podría usar reglas para restricciones de seguridad y un modelo validado para priorizar hipótesis, manteniendo una capa de explicación y rechazo de recomendaciones inseguras. Un agente autónomo podría automatizar tareas de ingestión, pero necesitaría límites, registro de decisiones y aprobación experta. MediLogic demuestra el razonamiento simbólico y sus límites; no pretende convertirse en autoridad clínica.", s["body"]), p("Conclusión", s["h1"]), p("Los tres casos muestran coherencia interna con un catálogo pequeño y controlado. También muestran por qué el resultado debe interpretarse como orientación educativa y no como diagnóstico.", s["callout"])]
    return story


def build_pdf(filename: str, story) -> None:
    output = OUTPUT / filename
    output.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(output), pagesize=letter, leftMargin=.55 * inch, rightMargin=.55 * inch, topMargin=.55 * inch, bottomMargin=.72 * inch, title=filename, author="MediLogic")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(output)


if __name__ == "__main__":
    build_pdf("manual_tecnico.pdf", build_manual_tecnico())
    build_pdf("manual_usuario.pdf", build_manual_usuario())
    build_pdf("casos_clinicos.pdf", build_cases())
