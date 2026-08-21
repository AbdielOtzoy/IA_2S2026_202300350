"""Genera el archivo Prolog completo a partir del catálogo JSON."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .models import KnowledgeBase


def atom(value: str) -> str:
    """Cita un átomo Prolog; los identificadores ya están validados por Pydantic."""
    escaped = value.replace("'", "\\'")
    return f"'{escaped}'"


def prolog_text(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def boolean(value: bool) -> str:
    return "true" if value else "false"


def render_prolog(kb: KnowledgeBase) -> str:
    lines: list[str] = [
        "% ESTE ARCHIVO ES GENERADO. Edite data/knowledge_base.json desde la aplicación.",
        "% MediLogic - base de hechos y reglas de inferencia.",
        ":- module(medilogic, [symptom/4, disease/6, medication/3, disease_symptom/2,",
        "           disease_medication/2, contraindication/4, severity_weight/2,",
        "           diagnosis_metrics/6, matched_symptom/5, urgency/4,",
        "           medication_evaluation/8, activated_rule/4]).",
        ":- use_module(library(lists)).",
        ":- dynamic symptom/4, disease/6, medication/3, disease_symptom/2,",
        "           disease_medication/2, contraindication/4.",
        "",
        "% Hechos del catálogo",
    ]

    for symptom in kb.symptoms:
        lines.append(
            "symptom({id}, {name}, {description}, {alarm}).".format(
                id=atom(symptom.id),
                name=prolog_text(symptom.name),
                description=prolog_text(symptom.description),
                alarm=boolean(symptom.alarm),
            )
        )
    lines.append("")
    for disease in kb.diseases:
        lines.append(
            "disease({id}, {name}, {description}, {system}, {type}, {background}).".format(
                id=atom(disease.id),
                name=prolog_text(disease.name),
                description=prolog_text(disease.description),
                system=atom(disease.system.lower().replace(" ", "_")),
                type=atom(disease.type.lower().replace(" ", "_")),
                background=boolean(disease.is_background),
            )
        )
    for disease in kb.diseases:
        for symptom_id in disease.symptoms:
            lines.append(f"disease_symptom({atom(disease.id)}, {atom(symptom_id)}).")
    for disease in kb.diseases:
        for medication_id in disease.medications:
            lines.append(f"disease_medication({atom(disease.id)}, {atom(medication_id)}).")
    lines.append("")
    for medication in kb.medications:
        lines.append(
            "medication({id}, {name}, {description}).".format(
                id=atom(medication.id),
                name=prolog_text(medication.name),
                description=prolog_text(medication.description),
            )
        )
    for conflict in kb.contraindications:
        lines.append(
            "contraindication({medication}, {kind}, {reference}, {reason}).".format(
                medication=atom(conflict.medication_id),
                kind=atom(conflict.conflict_type.value),
                reference=atom(conflict.reference_id),
                reason=prolog_text(conflict.reason),
            )
        )

    lines.extend(
        [
            "",
            "% Reglas de ponderación y diagnóstico",
            "severity_weight(leve, 1).",
            "severity_weight(moderado, 2).",
            "severity_weight(severo, 3).",
            "",
            "patient_symptom(PatientSymptoms, Symptom, Severity) :-",
            "    member(sintoma(Symptom, Severity), PatientSymptoms).",
            "",
            "matched_symptom(Disease, PatientSymptoms, Symptom, Severity, Weight) :-",
            "    disease_symptom(Disease, Symptom),",
            "    patient_symptom(PatientSymptoms, Symptom, Severity),",
            "    severity_weight(Severity, Weight).",
            "",
            "diagnosis_metrics(Disease, PatientSymptoms, Points, MaxPoints, Affinity, MatchCount) :-",
            "    findall(Weight, matched_symptom(Disease, PatientSymptoms, _, _, Weight), Weights),",
            "    sum_list(Weights, Points),",
            "    findall(Symptom, disease_symptom(Disease, Symptom), Symptoms),",
            "    length(Symptoms, SymptomCount),",
            "    length(Weights, MatchCount),",
            "    MaxPoints is SymptomCount * 3,",
            "    ( MaxPoints > 0 ->",
            "        RawAffinity is (Points / MaxPoints) * 100,",
            "        Rounded is round(RawAffinity * 100) / 100,",
            "        Affinity is min(100, Rounded)",
            "    ; Affinity is 0 ).",
            "",
            "% Reglas de urgencia. La bandera de alarma tiene prioridad sobre la severidad.",
            "urgency(PatientSymptoms, inmediata, consulta_inmediata, sintoma_severo_o_alarma) :-",
            "    ( member(sintoma(_, severo), PatientSymptoms) ;",
            "      ( member(sintoma(AlarmSymptom, _), PatientSymptoms),",
            "        symptom(AlarmSymptom, _, _, true) ) ), !.",
            "urgency(PatientSymptoms, observacion, observacion_recomendada, sintomas_moderados) :-",
            "    member(sintoma(_, moderado), PatientSymptoms), !.",
            "urgency(PatientSymptoms, automanejo, posible_automanejo_orientativo, solo_sintomas_leves) :-",
            "    PatientSymptoms \\= [],",
            "    forall(member(sintoma(_, Severity), PatientSymptoms), Severity = leve), !.",
            "urgency(_, sin_datos, solicitar_datos, datos_insuficientes).",
            "",
            "% Reglas de seguridad de medicamentos. El orden expresa la primera causa de descarte.",
            "medication_evaluation(Medication, _, Allergies, _, _, descartado, alergia, Medication) :-",
            "    member(Medication, Allergies), !.",
            "medication_evaluation(Medication, _, _, ChronicConditions, _, descartado, chronic_condition, Condition) :-",
            "    contraindication(Medication, chronic_condition, Condition, _),",
            "    member(Condition, ChronicConditions), !.",
            "medication_evaluation(Medication, Disease, _, _, _, descartado, disease, Disease) :-",
            "    contraindication(Medication, disease, Disease, _), !.",
            "medication_evaluation(Medication, _, _, _, Treatments, descartado, treatment, Treatment) :-",
            "    contraindication(Medication, treatment, Treatment, _),",
            "    member(Treatment, Treatments), !.",
            "medication_evaluation(_, _, _, _, _, seguro, seguro, ninguno).",
            "",
            "% Trazabilidad: cada solución se asocia a reglas legibles por la aplicación.",
            "activated_rule(Disease, PatientSymptoms, coincidencia_de_sintomas, puntos_ponderados) :-",
            "    diagnosis_metrics(Disease, PatientSymptoms, Points, _, _, _), Points > 0.",
            "activated_rule(Disease, PatientSymptoms, severidad_ponderada, severidad_aplicada) :-",
            "    matched_symptom(Disease, PatientSymptoms, _, _, _).",
            "activated_rule(_, PatientSymptoms, regla_de_urgencia, Rule) :-",
            "    urgency(PatientSymptoms, _, _, Rule).",
            "activated_rule(Disease, _, medicamento_seguro, opcion_segura_disponible) :-",
            "    disease_medication(Disease, Medication),",
            "    medication_evaluation(Medication, Disease, [], [], [], seguro, seguro, ninguno), !.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def validate_prolog_file(path: Path) -> None:
    """Compila el archivo sin modificar el motor persistente."""
    command = ["swipl", "-q", "-f", "none", "-s", str(path), "-g", "halt"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=15, check=False)
    except FileNotFoundError as exc:
        raise RuntimeError("SWI-Prolog no está instalado o no está en PATH") from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise ValueError(f"El archivo Prolog no es válido: {detail[:1000]}")
