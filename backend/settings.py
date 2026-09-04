"""Configuración centralizada y segura para ejecución local."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent


def _split_origins(value: str | None) -> list[str]:
    raw = value or "http://localhost:5173,http://127.0.0.1:5173"
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@dataclass(frozen=True)
class Settings:
    root_dir: Path = ROOT_DIR
    data_file: Path = field(default_factory=lambda: Path(os.getenv("MEDILOGIC_DATA_FILE") or ROOT_DIR / "data" / "knowledge_base.json"))
    prolog_file: Path = field(default_factory=lambda: Path(os.getenv("MEDILOGIC_PROLOG_FILE") or ROOT_DIR / "prolog" / "medilogic.pl"))
    log_file: Path = field(default_factory=lambda: Path(os.getenv("MEDILOGIC_LOG_FILE") or ROOT_DIR / "logs" / "changes.txt"))
    admin_username: str = field(default_factory=lambda: os.getenv("MEDILOGIC_ADMIN_USERNAME", "admin"))
    admin_password_hash: str = field(default_factory=lambda: os.getenv("MEDILOGIC_ADMIN_PASSWORD_HASH", ""))
    cors_origins: list[str] = field(default_factory=lambda: _split_origins(os.getenv("MEDILOGIC_CORS_ORIGINS")))
    host: str = field(default_factory=lambda: os.getenv("MEDILOGIC_API_HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: int(os.getenv("MEDILOGIC_API_PORT", "8000")))

    def ensure_directories(self) -> None:
        for path in (self.data_file.parent, self.prolog_file.parent, self.log_file.parent):
            path.mkdir(parents=True, exist_ok=True)

