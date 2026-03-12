from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable

OPTION_PATTERN = re.compile(r"^\s*\(?([A-Da-d])\)?[).]\s*(.+)$")
INLINE_OPTION_SPLIT = re.compile(r"(?<!\n)\s([A-Da-d])[).]\s*")
ANSWER_LETTER = re.compile(r"(?i)do[gğ]ru\s*cevap\s*[:：]\s*\(?\s*([A-Da-d])\s*\)?")
ANSWER_NUMBER = re.compile(r"(?i)do[gğ]ru\s*cevap\s*[:：]\s*([+-]?\d+(?:\.\d+)?)")


class ImportErrorDetail(Exception):
    pass


def _repair_mojibake(value: str) -> str:
    if not value:
        return value
    if not any(marker in value for marker in ("Ã", "Â", "Ä", "â")):
        return value
    try:
        repaired = value.encode("latin-1").decode("utf-8")
    except UnicodeError:
        return value
    return repaired


def _repair_fields(data: dict) -> dict:
    return {key: _repair_mojibake(value) if isinstance(value, str) else value for key, value in data.items()}


def _split_question_options(text: str) -> tuple[str, list[str]]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if normalized.count("\n") < 3:
        normalized = INLINE_OPTION_SPLIT.sub(r"\n\1) ", normalized)
    lines = normalized.split("\n")

    stem_lines: list[str] = []
    options: dict[str, str] = {}
    current_letter: str | None = None

    for line in lines:
        match = OPTION_PATTERN.match(line)
        if match:
            letter = match.group(1).upper()
            options[letter] = match.group(2).strip()
            current_letter = letter
            continue
        if current_letter and line.strip():
            options[current_letter] = f"{options[current_letter]} {line.strip()}".strip()
        else:
            stem_lines.append(line)

    stem = "\n".join(stem_lines).strip() or text.strip()
    ordered = [options.get(letter, "") for letter in "ABCD"]
    if any(not opt for opt in ordered):
        raise ImportErrorDetail("options-missing")
    return stem, ordered


def _extract_correct_index(solution: str, options: list[str]) -> int:
    match = ANSWER_LETTER.search(solution)
    if match:
        return "ABCD".index(match.group(1).upper())
    match = ANSWER_NUMBER.search(solution)
    if match:
        value = match.group(1)
        for idx, opt in enumerate(options):
            if opt.strip() == value:
                return idx
        raise ImportErrorDetail("answer-number-not-in-options")
    raise ImportErrorDetail("answer-missing")


def _generate_numeric_options(solution: str) -> tuple[list[str], int] | None:
    match = ANSWER_NUMBER.search(solution)
    if not match:
        return None
    try:
        number = int(float(match.group(1)))
    except ValueError:
        return None
    candidates = [number + 1, number - 1, number + 2, number - 2, number + 3, number - 3, number + 5]
    distractors: list[str] = []
    for candidate in candidates:
        text = str(candidate)
        if text == str(number) or text in distractors:
            continue
        distractors.append(text)
        if len(distractors) == 3:
            break
    if len(distractors) < 3:
        return None
    return [str(number)] + distractors, 0


def _split_solution(solution: str) -> tuple[str, list[str]]:
    if "Formül:" in solution:
        before, after = solution.split("Formül:", 1)
        formulas = [line.strip() for line in after.strip().splitlines() if line.strip()]
        return before.strip(), formulas
    return solution.strip(), []


def _build_subject(lesson: str | int, topic: str) -> str:
    lesson = str(lesson).strip()
    topic = str(topic).strip()
    if lesson and topic:
        return f"Kriptoloji / Ders {lesson} / {topic}"
    if lesson:
        return f"Kriptoloji / Ders {lesson}"
    return "Kriptoloji"


def _fix_latex_escapes(line: str) -> str:
    """Fix unescaped LaTeX backslashes in JSON strings (e.g. \\phi -> \\\\phi)."""
    return re.sub(r'\\(?!["\\\/bfnrtu])', r'\\\\', line)


def load_ndjson(path: Path) -> list[dict]:
    items: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            data = json.loads(_fix_latex_escapes(line))
        if data.get("type") != "item":
            continue
        data = _repair_fields(data)
        items.append(data)
    return items


def import_questions(ndjson_path: Path, output_path: Path) -> list[dict]:
    items = load_ndjson(ndjson_path)
    now = datetime.now().isoformat(timespec="seconds")
    questions: list[dict] = []
    errors: list[str] = []

    for item in items:
        question_text = str(item.get("question", "")).strip()
        solution_text = str(item.get("solution", "")).strip()
        lesson = item.get("lesson", "")
        topic = item.get("topic", "")
        qid = str(item.get("id", "")).strip()

        try:
            stem, options = _split_question_options(question_text)
        except ImportErrorDetail:
            generated = _generate_numeric_options(solution_text)
            if generated is None:
                errors.append(qid or item.get("id", "?"))
                continue
            options, correct_index = generated
            stem = question_text.strip()
            explanation, formulas = _split_solution(solution_text)
        else:
            explanation, formulas = _split_solution(solution_text)
            try:
                correct_index = _extract_correct_index(solution_text, options)
            except ImportErrorDetail:
                errors.append(qid or item.get("id", "?"))
                continue

        source = str(item.get("source", "")).strip()
        if not source or source.lower() == "yeni":
            source = "Yapay Zeka"

        questions.append(
            {
                "id": qid,
                "subject": _build_subject(lesson, topic),
                "text": stem,
                "options": options,
                "correct_option": correct_index,
                "explanation": explanation,
                "formulas": formulas,
                "source": source,
                "difficulty": str(item.get("difficulty", "")).strip() or "Belirtilmedi",
                "created_at": now,
            }
        )

    if errors:
        raise ImportErrorDetail(f"Failed to parse {len(errors)} items. Example: {errors[0]}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(questions, ensure_ascii=False, indent=2), encoding="utf-8")
    return questions


def main(argv: Iterable[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("ndjson", type=Path)
    parser.add_argument("--out", type=Path, default=Path("data") / "questions.json")
    args = parser.parse_args(list(argv) if argv is not None else None)

    import_questions(args.ndjson, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
