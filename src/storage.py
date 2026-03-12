from __future__ import annotations

import json
from pathlib import Path

from .models import Question


class QuestionStore:
    def __init__(self, questions_path: Path, asked_path: Path) -> None:
        self.questions_path = questions_path
        self.asked_path = asked_path

    def load_questions(self) -> list[Question]:
        if not self.questions_path.exists():
            return []
        try:
            payload = json.loads(self.questions_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        return [Question.from_dict(item) for item in payload]

    def save_questions(self, questions: list[Question]) -> None:
        payload = [question.to_dict() for question in questions]
        self.questions_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_asked_ids(self) -> set[str]:
        if not self.asked_path.exists():
            return set()
        try:
            data = json.loads(self.asked_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return set()
        return set(str(item) for item in data)

    def save_asked_ids(self, ids: set[str]) -> None:
        self.asked_path.parent.mkdir(parents=True, exist_ok=True)
        self.asked_path.write_text(json.dumps(sorted(ids), ensure_ascii=False, indent=2), encoding="utf-8")
