from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class Question:
    qid: str
    subject: str
    text: str
    options: list[str]
    correct_option: int
    explanation: str
    formulas: list[str]
    source: str
    difficulty: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    @classmethod
    def from_dict(cls, data: dict) -> "Question":
        # Get explanation from either "explanation" or "solution" field
        explanation = str(data.get("explanation", "") or data.get("solution", "")).strip()
        
        # Extract just the explanation portion (after "Açıklama:" if present)
        if "Açıklama:" in explanation:
            explanation = explanation.split("Açıklama:", 1)[1].strip()
        elif "Explanation:" in explanation:
            explanation = explanation.split("Explanation:", 1)[1].strip()
        
        return cls(
            qid=str(data.get("id", "")).strip(),
            subject=str(data.get("subject", "")).strip(),
            text=str(data.get("text", "")).strip(),
            options=[str(item).strip() for item in data.get("options", [])],
            correct_option=int(data.get("correct_option", 0)),
            explanation=explanation,
            formulas=[str(item).strip() for item in data.get("formulas", [])],
            source=str(data.get("source", "")).strip(),
            difficulty=str(data.get("difficulty", "")).strip(),
            created_at=str(data.get("created_at", "")).strip() or datetime.now().isoformat(timespec="seconds"),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.qid,
            "subject": self.subject,
            "text": self.text,
            "options": self.options,
            "correct_option": self.correct_option,
            "explanation": self.explanation,
            "formulas": self.formulas,
            "source": self.source,
            "difficulty": self.difficulty,
            "created_at": self.created_at,
        }
