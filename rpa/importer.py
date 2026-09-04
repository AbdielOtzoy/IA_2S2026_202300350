"""Adaptador RPA para archivos JSON o TXT cuyo contenido es JSON.

Acepta dos representaciones aisladas aquí, sin afectar el endpoint ni el CLI:

1. Formato oficial del docente: una lista JSON de enfermedades con los campos
   ``nombre_enfermedad``, ``descripcion``, ``sintomas_asociados``,
   ``tratamiento_recomendado``, ``medicamentos_contraindicados`` y
   ``sistema_cuerpo``.
2. Formato interno de desarrollo: un objeto JSON con ``enfermedades`` y
   opcionalmente ``sintomas`` y ``medicamentos``.

El formato oficial se convierte al contrato interno: se generan los
identificadores, se registran automáticamente los síntomas y medicamentos
referenciados y las contraindicaciones de la enfermedad.
"""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.knowledge import KnowledgeRepository
from backend.models import Contraindication, Disease, KnowledgeBase, Medication, Symptom


RPA_INPUT_EXTENSIONS = {".json", ".txt"}
OFFICIAL_REQUIRED_FIELDS = (
    "nombre_enfermedad",
    "descripcion",
    "sintomas_asociados",
    "tratamiento_recomendado",
    "medicamentos_contraindicados",
    "sistema_cuerpo",
)


class RpaImportError(ValueError):
    pass


@dataclass(frozen=True)
class RpaImportResult:
    created_diseases: int
    updated_diseases: int
    created_symptoms: int
    created_medications: int
    created_contraindications: int
    log_file: str
    source_format: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_format": self.source_format,
            "created_diseases": self.created_diseases,
            "updated_diseases": self.updated_diseases,
            "created_symptoms": self.created_symptoms,
            "created_medications": self.created_medications,
            "created_contraindications": self.created_contraindications,
            "log_file": self.log_file,
        }


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    stripped = "".join(char for char in normalized if not unicodedata.combining(char)).lower()
    slug = "".join(char if char.isalnum() else "_" for char in stripped)
    slug = "_".join(part for part in slug.split("_") if part)
    if not slug:
        raise RpaImportError(f"No se pudo generar un identificador para '{value}'")
    return slug


def _humanize(identifier: str) -> str:
    return identifier.replace("_", " ").capitalize()


def _ensure_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise RpaImportError(f"El campo {label} debe ser una lista de textos")
    return value


def convert_official_payload(rows: list[Any]) -> tuple[dict[str, Any], str]:
    """Convierte la lista oficial del docente al contrato interno."""
    if not rows or not all(isinstance(row, dict) for row in rows):
        raise RpaImportError("Cada elemento del archivo oficial debe ser un objeto JSON")

    symptoms: list[dict[str, Any]] = []
    medications: list[dict[str, Any]] = []
    diseases: list[dict[str, Any]] = []
    contraindications: list[dict[str, Any]] = []
    seen_symptoms: set[str] = set()
    seen_medications: set[str] = set()
    seen_diseases: set[str] = set()

    for index, row in enumerate(rows, start=1):
        context = f"El registro #{index}"
        nombre = row.get("nombre_enfermedad")
        if isinstance(nombre, str) and nombre.strip():
            context = f"La enfermedad {nombre.strip()}"
        if not isinstance(nombre, str) or len(nombre.strip()) < 2:
            raise RpaImportError("Cada enfermedad requiere 'nombre_enfermedad' (texto de al menos 2 caracteres)")
        missing_fields = [field for field in OFFICIAL_REQUIRED_FIELDS if field not in row]
        if missing_fields:
            fields = ", ".join(f"'{field}'" for field in missing_fields)
            raise RpaImportError(f"{context} requiere los campos oficiales: {fields}")
        disease_id = _slugify(nombre)
        if disease_id in seen_diseases:
            raise RpaImportError(f"La enfermedad '{nombre}' aparece más de una vez en el archivo")
        descripcion = row["descripcion"]
        if not isinstance(descripcion, str) or not descripcion.strip():
            raise RpaImportError(f"La descripción de {nombre} debe ser texto")
        sistema = row.get("sistema_cuerpo")
        if not isinstance(sistema, str) or len(sistema.strip()) < 2:
            raise RpaImportError(f"La enfermedad {nombre} requiere 'sistema_cuerpo'")
        tipo = row.get("tipo_enfermedad") or row.get("tipo") or "no_especificado"
        if not isinstance(tipo, str) or len(tipo.strip()) < 2:
            raise RpaImportError(f"El tipo de enfermedad de {nombre} debe ser texto")

        sintomas = _ensure_list(row["sintomas_asociados"], f"sintomas_asociados de {nombre}")
        if not sintomas:
            raise RpaImportError(f"La enfermedad {nombre} no define 'sintomas_asociados'")
        tratamientos = _ensure_list(row["tratamiento_recomendado"], f"tratamiento_recomendado de {nombre}")
        contraindicados = _ensure_list(row["medicamentos_contraindicados"], f"medicamentos_contraindicados de {nombre}")

        seen_diseases.add(disease_id)
        symptom_ids: list[str] = []
        for raw_symptom in sintomas:
            symptom_id = _slugify(raw_symptom)
            if symptom_id not in seen_symptoms:
                seen_symptoms.add(symptom_id)
                symptoms.append(
                    {
                        "id": symptom_id,
                        "name": _humanize(symptom_id),
                        "description": "Síntoma registrado automáticamente por la carga RPA.",
                    }
                )
            symptom_ids.append(symptom_id)

        medication_ids: list[str] = []
        for raw_medication in tratamientos:
            medication_id = _slugify(raw_medication)
            if medication_id not in seen_medications:
                seen_medications.add(medication_id)
                medications.append(
                    {
                        "id": medication_id,
                        "name": raw_medication.strip(),
                        "description": "Medicamento registrado automáticamente por la carga RPA.",
                    }
                )
            medication_ids.append(medication_id)

        diseases.append(
            {
                "id": disease_id,
                "name": nombre.strip(),
                "description": descripcion.strip(),
                "system": _slugify(sistema),
                "type": _slugify(tipo),
                "symptoms": symptom_ids,
                "medications": medication_ids,
            }
        )

        for raw_medication in contraindicados:
            medication_id = _slugify(raw_medication)
            if medication_id not in seen_medications:
                seen_medications.add(medication_id)
                medications.append(
                    {
                        "id": medication_id,
                        "name": raw_medication.strip(),
                        "description": "Medicamento registrado automáticamente por la carga RPA.",
                    }
                )
            contraindications.append(
                {
                    "medication_id": medication_id,
                    "conflict_type": "disease",
                    "reference_id": disease_id,
                    "reason": f"Contraindicado para {nombre.strip()} según la carga RPA oficial.",
                }
            )

    return {
        "sintomas": symptoms,
        "medicamentos": medications,
        "enfermedades": diseases,
        "contraindicaciones": contraindications,
    }, "formato_oficial"


def parse_txt(content: bytes, filename: str = "carga.txt") -> tuple[dict[str, Any], str]:
    extension = Path(filename).suffix.lower()
    if extension not in RPA_INPUT_EXTENSIONS:
        raise RpaImportError("El RPA solo acepta archivos con extensión .json o .txt")
    if not content:
        raise RpaImportError("El archivo RPA está vacío")
    if len(content) > 1_000_000:
        raise RpaImportError("El archivo RPA supera el límite de 1 MB")
    try:
        payload = json.loads(content.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RpaImportError("El archivo RPA debe contener JSON UTF-8 válido") from exc
    if isinstance(payload, list):
        return convert_official_payload(payload)
    if isinstance(payload, dict):
        diseases = payload.get("enfermedades", payload.get("diseases"))
        if not isinstance(diseases, list) or len(diseases) < 1:
            raise RpaImportError("El archivo debe incluir una lista enfermedades con al menos un registro")
        return payload, "formato_interno"
    raise RpaImportError("El JSON raíz debe ser un objeto o una lista de enfermedades")


def merge_payload(current: KnowledgeBase, payload: dict[str, Any]) -> tuple[KnowledgeBase, dict[str, int]]:
    candidate = current.model_copy(deep=True)
    symptom_rows = payload.get("sintomas", payload.get("symptoms", []))
    medication_rows = payload.get("medicamentos", payload.get("medications", []))
    if not isinstance(symptom_rows, list) or not isinstance(medication_rows, list):
        raise RpaImportError("sintomas y medicamentos deben ser listas")
    contraindication_rows = payload.get("contraindicaciones", payload.get("contraindications", []))
    if not isinstance(contraindication_rows, list):
        raise RpaImportError("contraindicaciones debe ser una lista")

    existing_symptoms = {item.id: item for item in candidate.symptoms}
    created_symptoms = 0
    for raw in symptom_rows:
        symptom = Symptom.model_validate(raw)
        if symptom.id not in existing_symptoms:
            candidate.symptoms.append(symptom)
            existing_symptoms[symptom.id] = symptom
            created_symptoms += 1

    existing_medications = {item.id: item for item in candidate.medications}
    created_medications = 0
    for raw in medication_rows:
        medication = Medication.model_validate(raw)
        if medication.id not in existing_medications:
            candidate.medications.append(medication)
            existing_medications[medication.id] = medication
            created_medications += 1

    existing_diseases = {item.id: item for item in candidate.diseases}
    created_diseases = 0
    updated_diseases = 0
    for raw in payload["enfermedades"] if "enfermedades" in payload else payload["diseases"]:
        disease = Disease.model_validate(raw)
        if disease.id in existing_diseases:
            index = next(index for index, item in enumerate(candidate.diseases) if item.id == disease.id)
            previous = candidate.diseases[index]
            # El formato oficial no define is_background; se conserva el valor actual.
            background = disease.model_copy(update={"is_background": previous.is_background})
            candidate.diseases[index] = background
            updated_diseases += 1
        else:
            candidate.diseases.append(disease)
            created_diseases += 1

    existing_conflicts = {
        (item.medication_id, item.conflict_type.value, item.reference_id) for item in candidate.contraindications
    }
    created_contraindications = 0
    for raw in contraindication_rows:
        conflict = Contraindication.model_validate(raw)
        key = (conflict.medication_id, conflict.conflict_type.value, conflict.reference_id)
        if key not in existing_conflicts:
            candidate.contraindications.append(conflict)
            existing_conflicts.add(key)
            created_contraindications += 1

    return candidate, {
        "created_diseases": created_diseases,
        "updated_diseases": updated_diseases,
        "created_symptoms": created_symptoms,
        "created_medications": created_medications,
        "created_contraindications": created_contraindications,
    }


def import_payload(repository: KnowledgeRepository, content: bytes, filename: str = "carga.txt") -> RpaImportResult:
    payload, source_format = parse_txt(content, filename)
    counters: dict[str, int] = {}

    def mutate(current: KnowledgeBase) -> KnowledgeBase:
        nonlocal counters
        candidate, counters = merge_payload(current, payload)
        return candidate

    repository.mutate(f"RPA importación {filename} ({source_format})", mutate)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = repository.log_file.parent / f"rpa_{timestamp}.txt"
    disease_details = payload.get("enfermedades", [])
    lines = [
        "MediLogic - bitácora de automatización RPA",
        f"Fecha UTC: {datetime.now(timezone.utc).isoformat()}",
        f"Archivo: {filename}",
        f"Formato detectado: {source_format}",
        "Resultado: carga completada",
        f"Enfermedades creadas: {counters['created_diseases']}",
        f"Enfermedades actualizadas: {counters['updated_diseases']}",
        f"Síntomas creados: {counters['created_symptoms']}",
        f"Medicamentos creados: {counters['created_medications']}",
        f"Contraindicaciones creadas: {counters['created_contraindications']}",
        "",
        "Detalle de enfermedades procesadas:",
    ]
    for disease in disease_details:
        if isinstance(disease, dict):
            lines.append(
                f"- {disease.get('name', disease.get('id', '?'))}: "
                f"sistema={disease.get('system', '?')}, tipo={disease.get('type', '?')}, "
                f"sintomas={len(disease.get('symptoms', []))}, "
                f"medicamentos={len(disease.get('medications', []))}"
            )
    lines += [
        "",
        "Validación Prolog: exitosa",
        "Recarga del motor: exitosa",
    ]
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return RpaImportResult(
        log_file=str(log_path), source_format=source_format, **counters
    )


def import_file(repository: KnowledgeRepository, path: Path) -> RpaImportResult:
    return import_payload(repository, path.read_bytes(), path.name)
