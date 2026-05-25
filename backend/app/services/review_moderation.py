import re
from collections import Counter

ABUSIVE_KEYWORDS = {
    "abuse",
    "abusive",
    "hate",
    "scam",
    "fraud",
    "idiot",
    "stupid",
    "threat",
}

STOP_WORDS = {
    "about",
    "after",
    "also",
    "and",
    "are",
    "but",
    "for",
    "from",
    "had",
    "has",
    "have",
    "into",
    "not",
    "our",
    "that",
    "the",
    "their",
    "this",
    "was",
    "were",
    "with",
    "work",
    "very",
}


def contains_abusive_language(*values: str | None) -> bool:
    text = " ".join(value or "" for value in values).lower()
    return any(keyword in text for keyword in ABUSIVE_KEYWORDS)


def keyword_summary(texts: list[str | None], limit: int = 5) -> list[str]:
    words: list[str] = []
    for text in texts:
        if not text:
            continue
        words.extend(
            word
            for word in re.findall(r"[a-zA-Z][a-zA-Z+-]{2,}", text.lower())
            if word not in STOP_WORDS and len(word) <= 30
        )
    return [word for word, _count in Counter(words).most_common(limit)]
