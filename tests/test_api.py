from __future__ import annotations

import json

from fastapi.testclient import TestClient

from backend.main import create_app


def authenticated_client(test_settings):
    client = TestClient(create_app(test_settings))
    login = client.post("/api/auth/login", json={"username": "admin", "password": "test-password"})
    assert login.status_code == 200
    client.headers.update({"Authorization": f"Bearer {login.json()['access_token']}"})
    return client


def test_patient_api_and_pdf(test_settings):
    client = TestClient(create_app(test_settings))
    payload = {
        "sintomas": [{"id": "tos", "severity": "leve"}],
        "alergias": [],
        "enfermedades_cronicas": [],
        "tratamientos_actuales": [],
    }
    response = client.post("/api/analisis", json=payload)
    assert response.status_code == 200
    assert response.json()["diagnoses"][0]["affinity"] == 11.11
    pdf = client.post("/api/informes/pdf", json=payload)
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF")


def test_admin_is_protected_and_can_create_record(test_settings):
    client = TestClient(create_app(test_settings))
    assert client.get("/api/admin/knowledge").status_code == 401
    client = authenticated_client(test_settings)
    response = client.post("/api/admin/sintomas", json={"id": "dolor_prueba", "name": "Dolor de prueba", "description": "Sintético"})
    assert response.status_code == 200
    knowledge = client.get("/api/admin/knowledge")
    assert any(item["id"] == "dolor_prueba" for item in knowledge.json()["symptoms"])
    assert "dolor_prueba" in test_settings.prolog_file.read_text(encoding="utf-8")
    assert test_settings.log_file.exists()


def test_admin_rejects_delete_with_invalidating_relationship(test_settings):
    client = authenticated_client(test_settings)
    response = client.delete("/api/admin/sintomas/tos")
    assert response.status_code == 422
    assert "utilice" in response.json()["detail"]


def test_rpa_upload_updates_catalog_and_logs(test_settings):
    client = authenticated_client(test_settings)
    content = open("rpa/examples/carga_tres_enfermedades.txt", "rb").read()
    response = client.post("/api/admin/rpa/import", files={"file": ("carga.txt", content, "text/plain")})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["created_diseases"] == 3
    assert result["created_symptoms"] == 1
    assert test_settings.prolog_file.read_text(encoding="utf-8").count("disease('") >= 7
    assert (test_settings.log_file.parent / result["log_file"].split("/")[-1]).exists() or __import__("pathlib").Path(result["log_file"]).exists()

