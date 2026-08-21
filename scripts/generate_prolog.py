"""Regenera prolog/medilogic.pl a partir del JSON versionado."""

from pathlib import Path

from backend.knowledge import validate_knowledge
from backend.models import KnowledgeBase
from backend.prolog_generator import render_prolog, validate_prolog_file


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "knowledge_base.json"
PROLOG = ROOT / "prolog" / "medilogic.pl"


def main() -> None:
    kb = KnowledgeBase.model_validate_json(DATA.read_text(encoding="utf-8"))
    validate_knowledge(kb)
    PROLOG.parent.mkdir(parents=True, exist_ok=True)
    PROLOG.write_text(render_prolog(kb), encoding="utf-8")
    validate_prolog_file(PROLOG)
    print(f"Generado y validado: {PROLOG}")


if __name__ == "__main__":
    main()

