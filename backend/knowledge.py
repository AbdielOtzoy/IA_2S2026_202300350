"""Persistencia validada, generación atómica y recarga del conocimiento."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock

from .models import ConflictType, KnowledgeBase
from .prolog_generator import render_prolog, validate_prolog_file


class KnowledgeValidationError(ValueError):
    pass


class KnowledgeReloadError(RuntimeError):
    pass


def validate_knowledge(kb: KnowledgeBase) -> None:
    symptom_ids = [item.id for item in kb.symptoms]
    disease_ids = [item.id for item in kb.diseases]
    medication_ids = [item.id for item in kb.medications]
    for label, values in (("síntomas", symptom_ids), ("enfermedades", disease_ids), ("medicamentos", medication_ids)):
        if len(values) != len(set(values)):
            raise KnowledgeValidationError(f"Hay identificadores repetidos en {label}")
    symptom_set, disease_set, medication_set = set(symptom_ids), set(disease_ids), set(medication_ids)
    for disease in kb.diseases:
        missing_symptoms = sorted(set(disease.symptoms) - symptom_set)
        missing_meds = sorted(set(disease.medications) - medication_set)
        if missing_symptoms:
            raise KnowledgeValidationError(f"La enfermedad {disease.id} referencia síntomas inexistentes: {missing_symptoms}")
        if missing_meds:
            raise KnowledgeValidationError(f"La enfermedad {disease.id} referencia medicamentos inexistentes: {missing_meds}")
    if len({(c.medication_id, c.conflict_type, c.reference_id) for c in kb.contraindications}) != len(kb.contraindications):
        raise KnowledgeValidationError("Hay contraindicaciones repetidas")
    for conflict in kb.contraindications:
        if conflict.medication_id not in medication_set:
            raise KnowledgeValidationError(f"El medicamento de la contraindicación no existe: {conflict.medication_id}")
        if conflict.conflict_type is ConflictType.CHRONIC_CONDITION:
            condition = next((d for d in kb.diseases if d.id == conflict.reference_id), None)
            if condition is None or not condition.is_background:
                raise KnowledgeValidationError(
                    f"La condición crónica {conflict.reference_id} debe existir y estar marcada como antecedente"
                )
        elif conflict.conflict_type is ConflictType.DISEASE and conflict.reference_id not in disease_set:
            raise KnowledgeValidationError(f"La enfermedad de la contraindicación no existe: {conflict.reference_id}")
        elif conflict.conflict_type is ConflictType.TREATMENT and conflict.reference_id not in medication_set:
            raise KnowledgeValidationError(f"El tratamiento de la contraindicación no existe: {conflict.reference_id}")


class KnowledgeRepository:
    def __init__(self, data_file: Path, prolog_file: Path, log_file: Path, engine) -> None:
        self.data_file = Path(data_file)
        self.prolog_file = Path(prolog_file)
        self.log_file = Path(log_file)
        self.engine = engine
        self.lock = RLock()

    def initialize(self) -> KnowledgeBase:
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.prolog_file.parent.mkdir(parents=True, exist_ok=True)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        kb = self.load()
        validate_knowledge(kb)
        rendered = render_prolog(kb).encode("utf-8")
        if not self.prolog_file.exists() or self.prolog_file.read_bytes() != rendered:
            temporary = self._temporary_file(self.prolog_file, rendered)
            validate_prolog_file(temporary)
            os.replace(temporary, self.prolog_file)
        self.engine.reload()
        return kb

    def load(self) -> KnowledgeBase:
        try:
            raw = json.loads(self.data_file.read_text(encoding="utf-8"))
            kb = KnowledgeBase.model_validate(raw)
            validate_knowledge(kb)
            return kb
        except FileNotFoundError as exc:
            raise KnowledgeValidationError(f"No existe la base de conocimiento: {self.data_file}") from exc
        except json.JSONDecodeError as exc:
            raise KnowledgeValidationError(f"JSON inválido en la base de conocimiento: {exc}") from exc

    def prolog_text(self) -> str:
        return self.prolog_file.read_text(encoding="utf-8")

    def mutate(self, operation: str, mutator: Callable[[KnowledgeBase], KnowledgeBase]) -> KnowledgeBase:
        with self.lock:
            current = self.load()
            candidate = mutator(current.model_copy(deep=True))
            validate_knowledge(candidate)
            json_bytes = json.dumps(candidate.model_dump(mode="json"), ensure_ascii=False, indent=2).encode("utf-8")
            prolog_bytes = render_prolog(candidate).encode("utf-8")
            json_tmp = self._temporary_file(self.data_file, json_bytes)
            prolog_tmp = self._temporary_file(self.prolog_file, prolog_bytes)
            old_json = self.data_file.read_bytes()
            old_prolog = self.prolog_file.read_bytes() if self.prolog_file.exists() else None
            try:
                validate_prolog_file(prolog_tmp)
                os.replace(json_tmp, self.data_file)
                os.replace(prolog_tmp, self.prolog_file)
                try:
                    self.engine.reload()
                except Exception as exc:  # pragma: no cover - depends on SWI runtime
                    self._restore(old_json, old_prolog)
                    raise KnowledgeReloadError(f"No se pudo recargar Prolog: {exc}") from exc
                self._append_log(operation, candidate)
                return candidate
            except Exception:
                for path in (json_tmp, prolog_tmp):
                    try:
                        path.unlink()
                    except FileNotFoundError:
                        pass
                raise

    def _restore(self, old_json: bytes, old_prolog: bytes | None) -> None:
        self._write_atomic(self.data_file, old_json)
        if old_prolog is not None:
            self._write_atomic(self.prolog_file, old_prolog)
        self.engine.reload()

    @staticmethod
    def _temporary_file(target: Path, content: bytes) -> Path:
        with tempfile.NamedTemporaryFile(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent, delete=False) as stream:
            stream.write(content)
            return Path(stream.name)

    @staticmethod
    def _write_atomic(target: Path, content: bytes) -> None:
        temporary = KnowledgeRepository._temporary_file(target, content)
        os.replace(temporary, target)

    def _append_log(self, operation: str, kb: KnowledgeBase) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        summary = (
            f"{timestamp}\t{operation}\t"
            f"enfermedades={len(kb.diseases)} sintomas={len(kb.symptoms)} "
            f"medicamentos={len(kb.medications)} contraindicaciones={len(kb.contraindications)}\n"
        )
        with self.log_file.open("a", encoding="utf-8") as stream:
            stream.write(summary)
