"""Modelos Pydantic compartidos entre API, persistencia y RPA."""

from __future__ import annotations

import re
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


ID_PATTERN = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
Identifier = Annotated[str, Field(min_length=2, max_length=64, pattern=ID_PATTERN.pattern)]


class Severity(str, Enum):
    LEVE = "leve"
    MODERADO = "moderado"
    SEVERO = "severo"


class ConflictType(str, Enum):
    CHRONIC_CONDITION = "chronic_condition"
    DISEASE = "disease"
    TREATMENT = "treatment"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Symptom(StrictModel):
    id: Identifier
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=500)
    alarm: bool = False


class Medication(StrictModel):
    id: Identifier
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=500)


class Disease(StrictModel):
    id: Identifier
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=1000)
    system: str = Field(min_length=2, max_length=80)
    type: str = Field(min_length=2, max_length=80)
    is_background: bool = False
    symptoms: list[Identifier] = Field(default_factory=list)
    medications: list[Identifier] = Field(default_factory=list)

    @field_validator("symptoms", "medications")
    @classmethod
    def unique_references(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("Las referencias no pueden repetirse")
        return value


class Contraindication(StrictModel):
    medication_id: Identifier
    conflict_type: ConflictType
    reference_id: Identifier
    reason: str = Field(min_length=5, max_length=500)


class KnowledgeBase(StrictModel):
    version: int = Field(default=1, ge=1)
    symptoms: list[Symptom] = Field(default_factory=list)
    diseases: list[Disease] = Field(default_factory=list)
    medications: list[Medication] = Field(default_factory=list)
    contraindications: list[Contraindication] = Field(default_factory=list)


class PatientSymptom(StrictModel):
    id: Identifier
    severity: Severity


class AnalysisRequest(StrictModel):
    sintomas: list[PatientSymptom] = Field(min_length=1, max_length=100)
    alergias: list[Identifier] = Field(default_factory=list, max_length=100)
    enfermedades_cronicas: list[Identifier] = Field(default_factory=list, max_length=100)
    tratamientos_actuales: list[Identifier] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def validate_unique_ids(self) -> "AnalysisRequest":
        for field_name in ("sintomas", "alergias", "enfermedades_cronicas", "tratamientos_actuales"):
            values = getattr(self, field_name)
            ids = [item.id if isinstance(item, PatientSymptom) else item for item in values]
            if len(ids) != len(set(ids)):
                raise ValueError(f"No se permiten valores repetidos en {field_name}")
        return self


class Coincidence(StrictModel):
    symptom_id: Identifier
    symptom_name: str
    severity: Severity
    weight: int = Field(ge=1, le=3)


class DiscardedMedication(StrictModel):
    medication_id: Identifier
    medication_name: str
    reason_code: str
    reason: str
    reference_id: str | None = None


class SafeMedication(StrictModel):
    medication_id: Identifier
    medication_name: str
    description: str


class Urgency(StrictModel):
    level: str
    action: str
    rule: str


class ActivatedRule(StrictModel):
    rule: str
    explanation: str


class Diagnosis(StrictModel):
    disease_id: Identifier
    disease_name: str
    description: str
    system: str
    type: str
    points_obtained: int = Field(ge=0)
    points_maximum: int = Field(ge=0)
    affinity: float = Field(ge=0, le=100)
    coincidences: list[Coincidence] = Field(default_factory=list)
    urgency: Urgency
    recommended_medication: SafeMedication | None = None
    safe_medications: list[SafeMedication] = Field(default_factory=list)
    discarded_medications: list[DiscardedMedication] = Field(default_factory=list)
    activated_rules: list[ActivatedRule] = Field(default_factory=list)


class AnalysisResponse(StrictModel):
    analysis_id: str
    created_at: str
    diagnoses: list[Diagnosis]
    global_urgency: Urgency
    warnings: list[str]
    formula: str


class LoginRequest(StrictModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)


class TokenResponse(StrictModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class SymptomWrite(StrictModel):
    id: Identifier
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=500)
    alarm: bool = False


class MedicationWrite(StrictModel):
    id: Identifier
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=500)


class DiseaseWrite(StrictModel):
    id: Identifier
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=1000)
    system: str = Field(min_length=2, max_length=80)
    type: str = Field(min_length=2, max_length=80)
    is_background: bool = False
    symptoms: list[Identifier] = Field(default_factory=list)
    medications: list[Identifier] = Field(default_factory=list)


class ContraindicationWrite(StrictModel):
    medication_id: Identifier
    conflict_type: ConflictType
    reference_id: Identifier
    reason: str = Field(min_length=5, max_length=500)


class Catalogs(StrictModel):
    symptoms: list[Symptom]
    medications: list[Medication]
    background_conditions: list[Disease]

