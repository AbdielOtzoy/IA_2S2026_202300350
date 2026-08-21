"""Servicios de aplicación que coordinan persistencia, Prolog y respuestas."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from .models import AnalysisRequest, AnalysisResponse
from .prolog_engine import PrologEngine
from .knowledge import KnowledgeRepository


FORMULA = (
    "afinidad = suma de pesos de síntomas coincidentes / "
    "(cantidad de síntomas de la enfermedad * 3) * 100; "
    "leve=1, moderado=2, severo=3"
)


def perform_analysis(request: AnalysisRequest, repository: KnowledgeRepository, engine: PrologEngine) -> AnalysisResponse:
    knowledge = repository.load()
    result = engine.analyze(request, knowledge)
    warnings = [
        "MediLogic es un prototipo académico de orientación preliminar; no sustituye una consulta médica profesional.",
    ]
    if result["global_urgency"]["level"] == "inmediata":
        warnings.append("Se detectó un síntoma severo o de alarma: busque atención médica inmediata.")
    if not result["diagnoses"]:
        warnings.append("No hay coincidencias suficientes; no se recomienda automedicarse con base en este resultado.")
    for diagnosis in result["diagnoses"]:
        if not diagnosis["safe_medications"]:
            warnings.append(f"No hay un medicamento seguro registrado para {diagnosis['disease_name']}.")
    response = AnalysisResponse.model_validate(
        {
            "analysis_id": str(uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "diagnoses": result["diagnoses"],
            "global_urgency": result["global_urgency"],
            "warnings": warnings,
            "formula": FORMULA,
        }
    )
    return response

