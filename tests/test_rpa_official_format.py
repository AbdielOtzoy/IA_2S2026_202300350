from pathlib import Path

import pytest

from backend.models import AnalysisRequest, PatientSymptom
from rpa.importer import RpaImportError, import_file, parse_txt

OFFICIAL_FILE = Path("rpa/examples/formato_oficial_tutor.txt")


def test_official_format_import_updates_knowledge(repository):
    result = import_file(repository, OFFICIAL_FILE)
    assert result.source_format == "formato_oficial"
    assert result.created_diseases == 3
    assert result.updated_diseases == 1
    assert result.created_symptoms == 10
    assert result.created_medications == 12
    assert result.created_contraindications == 6

    kb = repository.load()
    hipertension = next(disease for disease in kb.diseases if disease.id == "hipertension")
    assert hipertension.is_background is True
    assert "enalapril" in hipertension.medications
    asma = next(disease for disease in kb.diseases if disease.id == "asma_bronquial")
    assert asma.medications == ["salbutamol", "fluticasona"]
    assert asma.system == "respiratorio"
    gastro = next(disease for disease in kb.diseases if disease.id == "gastroenteritis_aguda")
    assert "suero_oral" in gastro.medications
    assert any(
        conflict.medication_id == "aspirina"
        and conflict.conflict_type.value == "disease"
        and conflict.reference_id == "asma_bronquial"
        for conflict in kb.contraindications
    )

    log = Path(result.log_file).read_text(encoding="utf-8")
    assert "formato_oficial" in log
    assert "Contraindicaciones creadas: 6" in log
    assert "Validación Prolog: exitosa" in log


def test_official_import_enables_analysis_with_treatments(repository):
    import_file(repository, OFFICIAL_FILE)
    kb = repository.load()
    request = AnalysisRequest(
        sintomas=[
            PatientSymptom(id="dificultad_respiratoria", severity="severo"),
            PatientSymptom(id="silbido_pecho", severity="moderado"),
        ],
        alergias=["salbutamol"],
        enfermedades_cronicas=[],
        tratamientos_actuales=[],
    )
    response = repository.engine.analyze(request, kb)
    top = response["diagnoses"][0]
    assert top["disease_id"] == "asma_bronquial"
    assert top["points_obtained"] == 5
    assert top["points_maximum"] == 9
    discarded = {item["medication_id"] for item in top["discarded_medications"]}
    assert "salbutamol" in discarded
    safe = {item["medication_id"] for item in top["safe_medications"]}
    assert "fluticasona" in safe


def test_legacy_internal_format_still_supported(repository):
    result = import_file(repository, Path("rpa/examples/carga_tres_enfermedades.txt"))
    assert result.source_format == "formato_interno"
    assert result.created_diseases == 3
    assert result.created_contraindications == 0


def test_official_format_validation_errors():
    with pytest.raises(RpaImportError):
        parse_txt(b"[]", "carga.txt")
    with pytest.raises(RpaImportError):
        parse_txt(b'[{"nombre_enfermedad": "Gripe"}]', "carga.txt")
    with pytest.raises(RpaImportError):
        parse_txt(b'[{"nombre_enfermedad": "Gripe", "sistema_cuerpo": "respiratorio", "sintomas_asociados": ["tos"], "tratamiento_recomendado": [], "medicamentos_contraindicados": []}]', "informe.json")
    duplicated = b"""[
      {"nombre_enfermedad": "Gripe", "sistema_cuerpo": "respiratorio", "sintomas_asociados": ["tos"]},
      {"nombre_enfermedad": "Gripe", "sistema_cuerpo": "respiratorio", "sintomas_asociados": ["fiebre"]}
    ]"""
    with pytest.raises(RpaImportError, match="más de una vez"):
        parse_txt(duplicated, "carga.txt")
