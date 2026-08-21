"""Adaptador RPA para archivos TXT cuyo contenido es JSON.

El formato queda aislado aquí para sustituirlo cuando el docente entregue el
formato definitivo. El endpoint y el CLI no dependen de la representación.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.knowledge import KnowledgeRepository
from backend.models import Disease, KnowledgeBase, Medication, Symptom


class RpaImportError(ValueError):
    pass


@dataclass(frozen=True)
class RpaImportResult:
    created_diseases: int
    updated_diseases: int
    created_symptoms: int
    created_medications: int
    log_file: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "created_diseases": self.created_diseases,
            "updated_diseases": self.updated_diseases,
            "created_symptoms": self.created_symptoms,
            "created_medications": self.created_medications,
            "log_file": self.log_file,
        }


def parse_txt(content: bytes, filename: str = "carga.txt") -> dict[str, Any]:
    if not filename.lower().endswith(".txt"):
        raise RpaImportError("El RPA solo acepta archivos con extensión .txt")
    if not content:
        raise RpaImportError("El archivo TXT está vacío")
    if len(content) > 1_000_000:
        raise RpaImportError("El archivo TXT supera el límite de 1 MB")
    try:
        payload = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RpaImportError("El TXT debe contener JSON UTF-8 válido") from exc
    if not isinstance(payload, dict):
        raise RpaImportError("El JSON raíz debe ser un objeto")
    diseases = payload.get("enfermedades", payload.get("diseases"))
    if not isinstance(diseases, list) or len(diseases) < 1:
        raise RpaImportError("El archivo debe incluir una lista enfermedades con al menos un registro")
    return payload


def merge_payload(current: KnowledgeBase, payload: dict[str, Any]) -> tuple[KnowledgeBase, dict[str, int]]:
    candidate = current.model_copy(deep=True)
    symptom_rows = payload.get("sintomas", payload.get("symptoms", []))
    medication_rows = payload.get("medicamentos", payload.get("medications", []))
    if not isinstance(symptom_rows, list) or not isinstance(medication_rows, list):
        raise RpaImportError("sintomas y medicamentos deben ser listas")

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
            candidate.diseases[index] = disease
            updated_diseases += 1
        else:
            candidate.diseases.append(disease)
            created_diseases += 1
    return candidate, {
        "created_diseases": created_diseases,
        "updated_diseases": updated_diseases,
        "created_symptoms": created_symptoms,
        "created_medications": created_medications,
    }


def import_payload(repository: KnowledgeRepository, content: bytes, filename: str = "carga.txt") -> RpaImportResult:
    payload = parse_txt(content, filename)
    counters: dict[str, int] = {}

    def mutate(current: KnowledgeBase) -> KnowledgeBase:
        nonlocal counters
        candidate, counters = merge_payload(current, payload)
        return candidate

    repository.mutate(f"RPA importación {filename}", mutate)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = repository.log_file.parent / f"rpa_{timestamp}.txt"
    lines = [
        "MediLogic - bitácora de automatización RPA",
        f"Fecha UTC: {datetime.now(timezone.utc).isoformat()}",
        f"Archivo: {filename}",
        "Resultado: carga completada",
        f"Enfermedades creadas: {counters['created_diseases']}",
        f"Enfermedades actualizadas: {counters['updated_diseases']}",
        f"Síntomas creados: {counters['created_symptoms']}",
        f"Medicamentos creados: {counters['created_medications']}",
        "Validación Prolog: exitosa",
        "Recarga del motor: exitosa",
    ]
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return RpaImportResult(log_file=str(log_path), **counters)


def import_file(repository: KnowledgeRepository, path: Path) -> RpaImportResult:
    return import_payload(repository, path.read_bytes(), path.name)

