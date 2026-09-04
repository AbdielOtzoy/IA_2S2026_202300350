"""CLI para reproducir el flujo RPA sin la interfaz web."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.knowledge import KnowledgeRepository
from backend.prolog_engine import PrologEngine
from backend.settings import Settings
from .importer import import_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Carga RPA de enfermedades MediLogic")
    parser.add_argument("archivo", help="Ruta al archivo RPA .json o .txt con JSON UTF-8")
    args = parser.parse_args()
    settings = Settings()
    settings.ensure_directories()
    engine = PrologEngine(settings.prolog_file)
    repository = KnowledgeRepository(settings.data_file, settings.prolog_file, settings.log_file, engine)
    repository.initialize()
    result = import_file(repository, Path(args.archivo))
    print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
