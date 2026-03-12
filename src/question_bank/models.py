from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class Question:
    subject: str
    text: str
    options: list[str]
    correct_option: int
    explanation: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def to_dict(self) -> dict:
        return {
            "subject": self.subject,
            "text": self.text,
            "options": self.options,
            "correct_option": self.correct_option,
            "explanation": self.explanation,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Question":
        return cls(
            subject=str(data.get("subject", "")).strip(),
            text=str(data.get("text", "")).strip(),
            options=[str(item).strip() for item in data.get("options", [])],
            correct_option=int(data.get("correct_option", 0)),
            explanation=str(data.get("explanation", "")).strip(),
            created_at=str(data.get("created_at", "")).strip() or datetime.now().isoformat(timespec="seconds"),
        )
