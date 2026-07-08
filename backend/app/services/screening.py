import json
from typing import Any


MAX_SCREENING_QUESTIONS = 5
MAX_QUESTION_LENGTH = 240
MAX_ANSWER_LENGTH = 1200


def _safe_json_loads(raw: str | None) -> Any:
    if not raw:
        return []
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return []


def normalize_screening_questions(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        loaded = _safe_json_loads(value)
        if isinstance(loaded, list):
            value = loaded
        else:
            value = [value]
    if not isinstance(value, list):
        raise ValueError("Screening questions must be a list")

    questions: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if not text:
            continue
        if len(text) > MAX_QUESTION_LENGTH:
            raise ValueError(f"Screening questions must be {MAX_QUESTION_LENGTH} characters or less")
        questions.append(text)

    if len(questions) > MAX_SCREENING_QUESTIONS:
        raise ValueError(f"Add no more than {MAX_SCREENING_QUESTIONS} screening questions")
    return questions


def dump_screening_questions(value: Any) -> str | None:
    questions = normalize_screening_questions(value)
    return json.dumps(questions) if questions else None


def load_screening_questions(raw: str | None) -> list[str]:
    return normalize_screening_questions(raw)


def normalize_screening_answers(questions: list[str], answers: Any) -> list[dict[str, str]]:
    if not questions:
        return []
    if not isinstance(answers, list):
        raise ValueError("Please answer the screening questions before applying.")
    if len(answers) < len(questions):
        raise ValueError("Please answer all screening questions before applying.")

    normalized: list[dict[str, str]] = []
    for index, question in enumerate(questions):
        answer = str(answers[index] or "").strip()
        if not answer:
            raise ValueError("Please answer all screening questions before applying.")
        if len(answer) > MAX_ANSWER_LENGTH:
            raise ValueError(f"Screening answers must be {MAX_ANSWER_LENGTH} characters or less.")
        normalized.append({"question": question, "answer": answer})
    return normalized


def dump_screening_answers(questions: list[str], answers: Any) -> str | None:
    normalized = normalize_screening_answers(questions, answers)
    return json.dumps(normalized) if normalized else None


def load_screening_answers(raw: str | None) -> list[dict[str, str]]:
    loaded = _safe_json_loads(raw)
    if not isinstance(loaded, list):
        return []
    normalized: list[dict[str, str]] = []
    for item in loaded:
        if not isinstance(item, dict):
            continue
        question = str(item.get("question") or "").strip()
        answer = str(item.get("answer") or "").strip()
        if question and answer:
            normalized.append({"question": question, "answer": answer})
    return normalized
