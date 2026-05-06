from typing import Any


def split_skills(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        raw_items = value
    else:
        raw_items = value.split(",")

    seen: set[str] = set()
    skills: list[str] = []
    for item in raw_items:
        skill = str(item).strip()
        key = skill.lower()
        if skill and key not in seen:
            seen.add(key)
            skills.append(skill)
    return skills


def normalize_skills(value: Any) -> str:
    return ", ".join(split_skills(value))
