from backend.app_services import perform_analysis
from backend.models import AnalysisRequest, Disease
from backend.prolog_engine import PrologEngine


def test_affinity_uses_severity_weights_and_orders_diagnoses(repository):
    request = AnalysisRequest.model_validate({
        "sintomas": [
            {"id": "tos", "severity": "moderado"},
            {"id": "fiebre", "severity": "severo"},
        ],
        "alergias": ["ibuprofeno"],
    })
    result = perform_analysis(request, repository, repository.engine)
    influenza = next(item for item in result.diagnoses if item.disease_id == "influenza")
    assert influenza.points_obtained == 5
    assert influenza.points_maximum == 12
    assert influenza.affinity == 41.67
    assert result.diagnoses[0].disease_id == "influenza"
    assert result.global_urgency.level == "inmediata"
    assert any(item.medication_id == "ibuprofeno" and item.reason_code == "alergia" for item in influenza.discarded_medications)
    assert any(item.rule == "regla_de_urgencia" for item in influenza.activated_rules)


def test_chronic_condition_and_treatment_conflicts_are_explained(repository):
    request = AnalysisRequest.model_validate({
        "sintomas": [{"id": "tos", "severity": "leve"}],
        "enfermedades_cronicas": ["hipertension"],
        "tratamientos_actuales": ["warfarina"],
    })
    result = perform_analysis(request, repository, repository.engine)
    cold = next(item for item in result.diagnoses if item.disease_id == "resfriado_comun")
    discarded = {item.medication_id: item for item in cold.discarded_medications}
    assert discarded["ibuprofeno"].reason_code == "chronic_condition"
    assert "hipertensión" in discarded["ibuprofeno"].reason
    assert result.global_urgency.level == "automanejo"


def test_invalid_patient_reference_is_rejected_by_model():
    from pydantic import ValidationError

    try:
        AnalysisRequest.model_validate({"sintomas": [{"id": "tos", "severity": "urgente"}]})
    except ValidationError:
        pass
    else:
        raise AssertionError("La severidad inválida debe rechazarse")


def test_no_safe_alternative_stays_empty_and_warns(repository):
    def add_disease(kb):
        kb.diseases.append(Disease(
            id="solo_ibuprofeno",
            name="Caso sin alternativa",
            description="Enfermedad sintética para probar ausencia de opción segura.",
            system="prueba",
            type="sintetico",
            symptoms=["tos"],
            medications=["ibuprofeno"],
        ))
        return kb

    repository.mutate("agregar caso sin alternativa", add_disease)
    request = AnalysisRequest.model_validate({
        "sintomas": [{"id": "tos", "severity": "leve"}],
        "alergias": ["ibuprofeno"],
    })
    result = perform_analysis(request, repository, repository.engine)
    diagnosis = next(item for item in result.diagnoses if item.disease_id == "solo_ibuprofeno")
    assert diagnosis.recommended_medication is None
    assert diagnosis.safe_medications == []
    assert any("No hay un medicamento seguro" in warning for warning in result.warnings)
