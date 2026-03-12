from __future__ import annotations

import json
from pathlib import Path

from .models import Question


class QuestionRepository:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.write_text("[]", encoding="utf-8")

    def _repair_mojibake(self, value: str) -> str:
        if not value:
            return value
        if not any(marker in value for marker in ("Ã", "Â", "Ä", "â")):
            return value
        try:
            repaired = value.encode("latin-1").decode("utf-8")
        except UnicodeError:
            return value
        before = sum(value.count(marker) for marker in ("Ã", "Â", "Ä", "â"))
        after = sum(repaired.count(marker) for marker in ("Ã", "Â", "Ä", "â"))
        return repaired if after < before else value

    def _normalize_subject(self, subject: str) -> str:
        subject = self._repair_mojibake(subject).strip()
        if " - " in subject:
            base = subject.split(" - ", 1)[0].strip()
            if base:
                return base
        return subject

    def _normalize_question(self, question: Question) -> bool:
        changed = False

        normalized_subject = self._normalize_subject(question.subject)
        if normalized_subject != question.subject:
            question.subject = normalized_subject
            changed = True

        normalized_text = self._repair_mojibake(question.text)
        if normalized_text != question.text:
            question.text = normalized_text
            changed = True

        normalized_options = [self._repair_mojibake(option) for option in question.options]
        if normalized_options != question.options:
            question.options = normalized_options
            changed = True

        normalized_explanation = self._repair_mojibake(question.explanation)
        if normalized_explanation != question.explanation:
            question.explanation = normalized_explanation
            changed = True

        return changed

    def load_questions(self) -> list[Question]:
        try:
            raw_data = json.loads(self.file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            raw_data = []

        questions: list[Question] = []
        changed = False
        for item in raw_data:
            try:
                question = Question.from_dict(item)
            except (TypeError, ValueError):
                continue

            if (
                question.subject
                and question.text
                and len(question.options) == 4
                and 0 <= question.correct_option < 4
                and all(question.options)
            ):
                if self._normalize_question(question):
                    changed = True
                questions.append(question)
        if changed:
            self.save_questions(questions)
        return questions

    def save_questions(self, questions: list[Question]) -> None:
        payload = [question.to_dict() for question in questions]
        self.file_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def add_question(self, question: Question) -> None:
        questions = self.load_questions()
        self._normalize_question(question)
        questions.append(question)
        self.save_questions(questions)

    def delete_question(self, question: Question) -> bool:
        questions = self.load_questions()
        deleted = False
        remaining_questions: list[Question] = []

        for item in questions:
            if not deleted and item.to_dict() == question.to_dict():
                deleted = True
                continue
            remaining_questions.append(item)

        if deleted:
            self.save_questions(remaining_questions)
        return deleted
