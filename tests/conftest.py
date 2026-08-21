from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from backend.auth import hash_password
from backend.knowledge import KnowledgeRepository
from backend.prolog_engine import PrologEngine
from backend.settings import Settings


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    data_file = tmp_path / "data" / "knowledge_base.json"
    prolog_file = tmp_path / "prolog" / "medilogic.pl"
    log_file = tmp_path / "logs" / "changes.txt"
    data_file.parent.mkdir(parents=True)
    shutil.copyfile(Path("data/knowledge_base.json"), data_file)
    return Settings(
        root_dir=tmp_path,
        data_file=data_file,
        prolog_file=prolog_file,
        log_file=log_file,
        admin_username="admin",
        admin_password_hash=hash_password("test-password"),
        cors_origins=["http://localhost:5173"],
    )


@pytest.fixture
def repository(test_settings):
    engine = PrologEngine(test_settings.prolog_file)
    repository = KnowledgeRepository(test_settings.data_file, test_settings.prolog_file, test_settings.log_file, engine)
    repository.initialize()
    return repository

