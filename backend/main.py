"""API FastAPI de MediLogic."""

from __future__ import annotations

from typing import Callable

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, Response, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from rpa.importer import RpaImportError, import_payload

from .app_services import perform_analysis
from .auth import SessionStore, verify_password
from .knowledge import KnowledgeReloadError, KnowledgeRepository, KnowledgeValidationError
from .models import (
    AnalysisRequest,
    Catalogs,
    Contraindication,
    ContraindicationWrite,
    Disease,
    DiseaseWrite,
    KnowledgeBase,
    LoginRequest,
    Medication,
    MedicationWrite,
    Symptom,
    SymptomWrite,
    TokenResponse,
)
from .prolog_engine import PrologEngine
from .report_pdf import build_analysis_pdf
from .settings import Settings


bearer = HTTPBearer(auto_error=False)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    settings.ensure_directories()
    engine = PrologEngine(settings.prolog_file)
    repository = KnowledgeRepository(settings.data_file, settings.prolog_file, settings.log_file, engine)
    repository.initialize()
    sessions = SessionStore()

    app = FastAPI(title="MediLogic API", version="0.1.0", description="Sistema experto académico de orientación preliminar")
    app.state.settings = settings
    app.state.engine = engine
    app.state.repository = repository
    app.state.sessions = sessions
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    def current_admin(
        request: Request,
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    ) -> str:
        token = credentials.credentials if credentials else None
        session = request.app.state.sessions.get(token)
        if session is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Se requiere una sesión administrativa válida")
        return session.username

    def mutate_knowledge(operation: str, mutator: Callable[[KnowledgeBase], KnowledgeBase]) -> KnowledgeBase:
        try:
            return repository.mutate(operation, mutator)
        except KnowledgeValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except KnowledgeReloadError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "medilogic"}

    @app.get("/api/catalogos", response_model=Catalogs)
    def catalogs() -> Catalogs:
        knowledge = repository.load()
        return Catalogs(
            symptoms=knowledge.symptoms,
            medications=knowledge.medications,
            background_conditions=[disease for disease in knowledge.diseases if disease.is_background],
        )

    @app.post("/api/analisis")
    def analysis(payload: AnalysisRequest):
        try:
            return perform_analysis(payload, repository, engine)
        except KeyError as exc:
            raise HTTPException(status_code=422, detail=f"Referencia inexistente en el análisis: {exc}") from exc
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"No se pudo ejecutar el motor lógico: {exc}") from exc

    @app.post("/api/informes/pdf")
    def pdf_report(payload: AnalysisRequest) -> Response:
        try:
            result = perform_analysis(payload, repository, engine)
            content = build_analysis_pdf(result.model_dump(mode="json"))
            return Response(
                content=content,
                media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="medilogic-{result.analysis_id}.pdf"'},
            )
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"No se pudo generar el PDF: {exc}") from exc

    @app.post("/api/auth/login", response_model=TokenResponse)
    def login(payload: LoginRequest) -> TokenResponse:
        if not settings.admin_password_hash:
            raise HTTPException(status_code=503, detail="Configure MEDILOGIC_ADMIN_PASSWORD_HASH antes de iniciar sesión")
        if payload.username != settings.admin_username or not verify_password(payload.password, settings.admin_password_hash):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        token = sessions.create(payload.username)
        return TokenResponse(access_token=token, expires_in=sessions.ttl_seconds)

    @app.post("/api/auth/logout")
    def logout(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict[str, str]:
        sessions.revoke(credentials.credentials if credentials else None)
        return {"message": "Sesión cerrada"}

    @app.get("/api/admin/knowledge", response_model=KnowledgeBase)
    def admin_knowledge(_: str = Depends(current_admin)) -> KnowledgeBase:
        return repository.load()

    @app.post("/api/admin/sintomas", response_model=Symptom)
    def create_symptom(payload: SymptomWrite, _: str = Depends(current_admin)) -> Symptom:
        def mutate(kb: KnowledgeBase) -> KnowledgeBase:
            if any(item.id == payload.id for item in kb.symptoms):
                raise KnowledgeValidationError(f"El síntoma ya existe: {payload.id}")
            kb.symptoms.append(Symptom.model_validate(payload.model_dump()))
            return kb

        kb = mutate_knowledge("crear síntoma " + payload.id, mutate)
        return next(item for item in kb.symptoms if item.id == payload.id)

    @app.put("/api/admin/sintomas/{item_id}", response_model=Symptom)
    def update_symptom(item_id: str, payload: SymptomWrite, _: str = Depends(current_admin)) -> Symptom:
        if item_id != payload.id:
            raise HTTPException(status_code=409, detail="El id de la ruta y del cuerpo deben coincidir")

        def mutate(kb: KnowledgeBase) -> KnowledgeBase:
            for index, item in enumerate(kb.symptoms):
                if item.id == item_id:
                    kb.symptoms[index] = Symptom.model_validate(payload.model_dump())
                    return kb
            raise KnowledgeValidationError(f"El síntoma no existe: {item_id}")

        kb = mutate_knowledge("editar síntoma " + item_id, mutate)
        return next(item for item in kb.symptoms if item.id == item_id)

    @app.delete("/api/admin/sintomas/{item_id}")
    def delete_symptom(item_id: str, _: str = Depends(current_admin)) -> dict[str, str]:
        def mutate(kb: KnowledgeBase) -> KnowledgeBase:
            if not any(item.id == item_id for item in kb.symptoms):
                raise KnowledgeValidationError(f"El síntoma no existe: {item_id}")
            if any(item_id in disease.symptoms for disease in kb.diseases):
                raise KnowledgeValidationError("No se puede eliminar el síntoma mientras una enfermedad lo utilice")
            kb.symptoms = [item for item in kb.symptoms if item.id != item_id]
            return kb

        mutate_knowledge("eliminar síntoma " + item_id, mutate)
        return {"message": "Síntoma eliminado"}

    @app.post("/api/admin/medicamentos", response_model=Medication)
    def create_medication(payload: MedicationWrite, _: str = Depends(current_admin)) -> Medication:
        def mutate(kb: KnowledgeBase) -> KnowledgeBase:
            if any(item.id == payload.id for item in kb.medications):
                raise KnowledgeValidationError(f"El medicamento ya existe: {payload.id}")
            kb.medications.append(Medication.model_validate(payload.model_dump()))
            return kb

        kb = mutate_knowledge("crear medicamento " + payload.id, mutate)
        return next(item for item in kb.medications if item.id == payload.id)

    @app.put("/api/admin/medicamentos/{item_id}", response_model=Medication)
    def update_medication(item_id: str, payload: MedicationWrite, _: str = Depends(current_admin)) -> Medication:
        if item_id != payload.id:
            raise HTTPException(status_code=409, detail="El id de la ruta y del cuerpo deben coincidir")

        def mutate(kb: KnowledgeBase) -> KnowledgeBase:
            for index, item in enumerate(kb.medications):
                if item.id == item_id:
                    kb.medications[index] = Medication.model_validate(payload.model_dump())
                    return kb
            raise KnowledgeValidationError(f"El medicamento no existe: {item_id}")

        kb = mutate_knowledge("editar medicamento " + item_id, mutate)
        return next(item for item in kb.medications if item.id == item_id)

    @app.delete("/api/admin/medicamentos/{item_id}")
    def delete_medication(item_id: str, _: str = Depends(current_admin)) -> dict[str, str]:
        def mutate(kb: KnowledgeBase) -> KnowledgeBase:
            if not any(item.id == item_id for item in kb.medications):
                raise KnowledgeValidationError(f"El medicamento no existe: {item_id}")
            if any(item_id in disease.medications for disease in kb.diseases):
                raise KnowledgeValidationError("No se puede eliminar el medicamento mientras una enfermedad lo utilice")
            if any(item_id == conflict.medication_id for conflict in kb.contraindications):
                raise KnowledgeValidationError("No se puede eliminar el medicamento mientras tenga contraindicaciones")
            kb.medications = [item for item in kb.medications if item.id != item_id]
            return kb

        mutate_knowledge("eliminar medicamento " + item_id, mutate)
        return {"message": "Medicamento eliminado"}

    @app.post("/api/admin/enfermedades", response_model=Disease)
    def create_disease(payload: DiseaseWrite, _: str = Depends(current_admin)) -> Disease:
        def mutate(kb: KnowledgeBase) -> KnowledgeBase:
            if any(item.id == payload.id for item in kb.diseases):
                raise KnowledgeValidationError(f"La enfermedad ya existe: {payload.id}")
            kb.diseases.append(Disease.model_validate(payload.model_dump()))
            return kb

        kb = mutate_knowledge("crear enfermedad " + payload.id, mutate)
        return next(item for item in kb.diseases if item.id == payload.id)

    @app.put("/api/admin/enfermedades/{item_id}", response_model=Disease)
    def update_disease(item_id: str, payload: DiseaseWrite, _: str = Depends(current_admin)) -> Disease:
        if item_id != payload.id:
            raise HTTPException(status_code=409, detail="El id de la ruta y del cuerpo deben coincidir")

        def mutate(kb: KnowledgeBase) -> KnowledgeBase:
            for index, item in enumerate(kb.diseases):
                if item.id == item_id:
                    kb.diseases[index] = Disease.model_validate(payload.model_dump())
                    return kb
            raise KnowledgeValidationError(f"La enfermedad no existe: {item_id}")

        kb = mutate_knowledge("editar enfermedad " + item_id, mutate)
        return next(item for item in kb.diseases if item.id == item_id)

    @app.delete("/api/admin/enfermedades/{item_id}")
    def delete_disease(item_id: str, _: str = Depends(current_admin)) -> dict[str, str]:
        def mutate(kb: KnowledgeBase) -> KnowledgeBase:
            if not any(item.id == item_id for item in kb.diseases):
                raise KnowledgeValidationError(f"La enfermedad no existe: {item_id}")
            if any(item_id == conflict.reference_id and conflict.conflict_type.value == "disease" for conflict in kb.contraindications):
                raise KnowledgeValidationError("No se puede eliminar la enfermedad mientras exista una contraindicación que la referencie")
            kb.diseases = [item for item in kb.diseases if item.id != item_id]
            return kb

        mutate_knowledge("eliminar enfermedad " + item_id, mutate)
        return {"message": "Enfermedad eliminada"}

    @app.post("/api/admin/contraindicaciones", response_model=Contraindication)
    def create_contraindication(payload: ContraindicationWrite, _: str = Depends(current_admin)) -> Contraindication:
        def mutate(kb: KnowledgeBase) -> KnowledgeBase:
            conflict = Contraindication.model_validate(payload.model_dump())
            if conflict in kb.contraindications:
                raise KnowledgeValidationError("La contraindicación ya existe")
            kb.contraindications.append(conflict)
            return kb

        kb = mutate_knowledge("crear contraindicación " + payload.medication_id, mutate)
        return kb.contraindications[-1]

    @app.delete("/api/admin/contraindicaciones/{medication_id}/{conflict_type}/{reference_id}")
    def delete_contraindication(medication_id: str, conflict_type: str, reference_id: str, _: str = Depends(current_admin)) -> dict[str, str]:
        def mutate(kb: KnowledgeBase) -> KnowledgeBase:
            original = len(kb.contraindications)
            kb.contraindications = [
                item for item in kb.contraindications
                if not (item.medication_id == medication_id and item.conflict_type.value == conflict_type and item.reference_id == reference_id)
            ]
            if len(kb.contraindications) == original:
                raise KnowledgeValidationError("La contraindicación no existe")
            return kb

        mutate_knowledge("eliminar contraindicación " + medication_id, mutate)
        return {"message": "Contraindicación eliminada"}

    @app.get("/api/admin/prolog")
    def prolog_source(_: str = Depends(current_admin)) -> PlainTextResponse:
        return PlainTextResponse(repository.prolog_text(), media_type="text/plain; charset=utf-8")

    @app.get("/api/admin/prolog/download")
    def download_prolog(_: str = Depends(current_admin)) -> Response:
        return Response(
            content=repository.prolog_text().encode("utf-8"),
            media_type="text/plain",
            headers={"Content-Disposition": 'attachment; filename="medilogic.pl"'},
        )

    @app.post("/api/admin/rpa/import")
    async def rpa_import(file: UploadFile = File(...), _: str = Depends(current_admin)) -> dict:
        filename = file.filename or "carga.txt"
        content = await file.read()
        try:
            result = import_payload(repository, content, filename)
            return result.as_dict()
        except (RpaImportError, KnowledgeValidationError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except KnowledgeReloadError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    return app


app = create_app()
