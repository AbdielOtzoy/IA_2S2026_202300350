"""Puente entre Python y SWI-Prolog mediante pyswip."""

from __future__ import annotations

from pathlib import Path
from threading import RLock
from typing import Any

try:  # pyswip se instala junto con SWI-Prolog según requirements.txt.
    from pyswip import Prolog
except ImportError:  # permite importar módulos de validación sin motor instalado
    Prolog = None  # type: ignore[assignment,misc]

from .models import AnalysisRequest, KnowledgeBase


class PrologUnavailableError(RuntimeError):
    pass


def _atom(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)


def _number(value: Any) -> float | int:
    if isinstance(value, (int, float)):
        return value
    number = float(value)
    return int(number) if number.is_integer() else number


def _quote_path(path: Path) -> str:
    return "'" + str(path.resolve()).replace("\\", "\\\\").replace("'", "\\'") + "'"


def _term_list(items: list[str]) -> str:
    return "[" + ",".join(items) + "]"


RULE_TEXT = {
    "coincidencia_de_sintomas": "La enfermedad tiene uno o más síntomas presentes en el perfil.",
    "puntos_ponderados": "Se sumaron los pesos Prolog: leve=1, moderado=2 y severo=3.",
    "severidad_ponderada": "La severidad declarada aportó peso a cada coincidencia.",
    "regla_de_urgencia": "La urgencia se determinó con las reglas de severidad y banderas de alarma.",
    "medicamento_seguro": "Se encontró al menos un candidato sin conflicto según las reglas de seguridad.",
    "opcion_segura_disponible": "El candidato pasó las comprobaciones de seguridad.",
}


class PrologEngine:
    _known_files: set[Path] = set()

    def __init__(self, prolog_file: Path) -> None:
        if Prolog is None:
            raise PrologUnavailableError("pyswip no está instalado. Ejecute: pip install -r requirements.txt")
        self.prolog_file = Path(prolog_file)
        self._prolog = Prolog()
        self._lock = RLock()
        self._loaded = False
        self._detach_previous_module()

    def _detach_previous_module(self) -> None:
        """Aísla instancias creadas en pruebas o procesos embebidos.

        pyswip mantiene un único estado SWI-Prolog por proceso. La aplicación
        normal crea un solo motor; esta limpieza permite además crear otra
        instancia con un archivo temporal sin chocar con el módulo anterior.
        """
        for previous_file in list(self._known_files):
            try:
                list(self._prolog.query(f"unload_file({_quote_path(previous_file)})"))
            except Exception:
                pass
        try:
            list(self._prolog.query("delete_module(medilogic)"))
        except Exception:
            pass
        self._known_files.add(self.prolog_file.resolve())

    def reload(self) -> None:
        with self._lock:
            self.prolog_file = self.prolog_file.resolve()
            if not self._loaded:
                list(self._prolog.query(f"consult({_quote_path(self.prolog_file)})"))
                self._loaded = True
            else:
                # make/0 relies on source timestamps. The JSON/.pl transaction
                # replaces the inode atomically, so force a reload of this
                # consulted file to make the update visible immediately.
                list(self._prolog.query(
                    f"load_files({_quote_path(self.prolog_file)}, [if(true), silent(true)])"
                ))

    def _query(self, goal: str) -> list[dict[str, Any]]:
        with self._lock:
            if not self._loaded:
                self.reload()
            return list(self._prolog.query(goal))

    @staticmethod
    def _patient_terms(request: AnalysisRequest) -> str:
        return _term_list([f"sintoma('{item.id}','{item.severity.value}')" for item in request.sintomas])

    @staticmethod
    def _atoms(values: list[str]) -> str:
        return _term_list([f"'{value}'" for value in values])

    def analyze(self, request: AnalysisRequest, kb: KnowledgeBase) -> dict[str, Any]:
        patient_terms = self._patient_terms(request)
        allergies = self._atoms(request.alergias)
        chronic = self._atoms(request.enfermedades_cronicas)
        treatments = self._atoms(request.tratamientos_actuales)
        global_urgency_row = self._query(
            f"medilogic:urgency({patient_terms}, Level, Action, Rule)"
        )[0]
        global_urgency = self._urgency(global_urgency_row)

        symptom_by_id = {item.id: item for item in kb.symptoms}
        medication_by_id = {item.id: item for item in kb.medications}
        conflict_by_key = {
            (item.medication_id, item.conflict_type.value, item.reference_id): item
            for item in kb.contraindications
        }
        diagnoses: list[dict[str, Any]] = []

        for disease in kb.diseases:
            metrics = self._query(
                f"medilogic:diagnosis_metrics('{disease.id}', {patient_terms}, Points, MaxPoints, Affinity, MatchCount)"
            )
            if not metrics:
                continue
            metric = metrics[0]
            match_count = int(_number(metric["MatchCount"]))
            if match_count == 0:
                continue
            matches = []
            for row in self._query(
                f"medilogic:matched_symptom('{disease.id}', {patient_terms}, Symptom, Severity, Weight)"
            ):
                symptom_id = _atom(row["Symptom"])
                symptom = symptom_by_id[symptom_id]
                matches.append(
                    {
                        "symptom_id": symptom_id,
                        "symptom_name": symptom.name,
                        "severity": _atom(row["Severity"]),
                        "weight": int(_number(row["Weight"])),
                    }
                )

            urgency_row = self._query(
                f"medilogic:urgency({patient_terms}, Level, Action, Rule)"
            )[0]
            safe_medications = []
            discarded_medications = []
            candidate_rows = self._query(
                f"medilogic:disease_medication('{disease.id}', Medication)"
            )
            for candidate_row in candidate_rows:
                medication_id = _atom(candidate_row["Medication"])
                medication = medication_by_id[medication_id]
                decision_rows = self._query(
                    "medilogic:medication_evaluation(" 
                    f"'{medication_id}', '{disease.id}', {allergies}, {chronic}, {treatments}, Status, Reason, Reference)"
                )
                if not decision_rows:
                    continue
                decision = decision_rows[0]
                status = _atom(decision["Status"])
                reason_code = _atom(decision["Reason"])
                reference_id = _atom(decision["Reference"])
                if status == "seguro":
                    safe_medications.append(
                        {
                            "medication_id": medication.id,
                            "medication_name": medication.name,
                            "description": medication.description,
                        }
                    )
                else:
                    conflict = conflict_by_key.get((medication_id, reason_code, reference_id))
                    reason = self._discard_reason(reason_code, reference_id, conflict.reason if conflict else None)
                    discarded_medications.append(
                        {
                            "medication_id": medication.id,
                            "medication_name": medication.name,
                            "reason_code": reason_code,
                            "reason": reason,
                            "reference_id": reference_id,
                        }
                    )

            rules: list[dict[str, str]] = []
            for rule_row in self._query(
                f"medilogic:activated_rule('{disease.id}', {patient_terms}, Rule, Explanation)"
            ):
                rule_id = _atom(rule_row["Rule"])
                explanation_id = _atom(rule_row["Explanation"])
                description = RULE_TEXT.get(explanation_id, RULE_TEXT.get(rule_id, explanation_id))
                item = {"rule": rule_id, "explanation": description}
                if item not in rules:
                    rules.append(item)
            if safe_medications and not any(item["rule"] == "medicamento_seguro" for item in rules):
                rules.append({"rule": "medicamento_seguro", "explanation": RULE_TEXT["medicamento_seguro"]})

            points = int(_number(metric["Points"]))
            maximum = int(_number(metric["MaxPoints"]))
            affinity = round(float(metric["Affinity"]), 2)
            diagnoses.append(
                {
                    "disease_id": disease.id,
                    "disease_name": disease.name,
                    "description": disease.description,
                    "system": disease.system,
                    "type": disease.type,
                    "points_obtained": points,
                    "points_maximum": maximum,
                    "affinity": min(100.0, affinity),
                    "coincidences": matches,
                    "urgency": self._urgency(urgency_row),
                    "recommended_medication": safe_medications[0] if safe_medications else None,
                    "safe_medications": safe_medications,
                    "discarded_medications": discarded_medications,
                    "activated_rules": rules,
                }
            )
        diagnoses.sort(key=lambda item: (-item["affinity"], item["disease_name"]))
        return {"diagnoses": diagnoses, "global_urgency": global_urgency}

    @staticmethod
    def _urgency(row: dict[str, Any]) -> dict[str, str]:
        level = _atom(row["Level"])
        action = _atom(row["Action"])
        rule = _atom(row["Rule"])
        labels = {
            "inmediata": "Consulta médica inmediata sugerida",
            "observacion": "Observación recomendada",
            "automanejo": "Posible automanejo orientativo",
            "sin_datos": "Se requieren más datos",
        }
        return {"level": level, "action": labels.get(level, action), "rule": rule}

    @staticmethod
    def _discard_reason(code: str, reference: str, configured_reason: str | None) -> str:
        if configured_reason:
            return configured_reason
        if code == "alergia":
            return "El paciente indicó alergia a este medicamento."
        if code == "chronic_condition":
            return f"Existe una contraindicación con el antecedente {reference}."
        if code == "disease":
            return f"Existe una contraindicación con la enfermedad {reference}."
        if code == "treatment":
            return f"Existe una incompatibilidad con el tratamiento {reference}."
        return "El motor Prolog descartó el medicamento por seguridad."
