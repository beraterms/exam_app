from __future__ import annotations

from pathlib import Path

from .importer import import_questions
from .ui import run_app


def main() -> None:
    root_dir = Path(__file__).resolve().parents[1]
    data_dir = root_dir / "data"
    ndjson_path = data_dir / "kriptoloji.ndjson"
    questions_path = data_dir / "questions.json"
    asked_path = data_dir / "asked.json"

    if asked_path.exists():
        asked_path.unlink()

    import_questions(ndjson_path, questions_path)
    run_app()


if __name__ == "__main__":
    main()
