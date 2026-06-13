import re
import secrets
import string


PUBLIC_ID_ALPHABET = string.ascii_uppercase + string.digits
USERNAME_PATTERN = re.compile(r"^[a-z0-9_-]{3,30}$")
SLUG_PATTERN = re.compile(r"[^a-z0-9]+")
RESERVED_USERNAMES = {
    "admin",
    "owner",
    "login",
    "register",
    "api",
    "support",
    "security",
    "privacy",
    "company",
    "companies",
    "jobs",
    "recruiter",
    "jobseeker",
}


def generate_public_id(prefix: str = "SFS", length: int = 12) -> str:
    clean_prefix = "".join(char for char in prefix.upper() if char in PUBLIC_ID_ALPHABET)[:4]
    random_length = max(length - len(clean_prefix), 8)
    token = "".join(secrets.choice(PUBLIC_ID_ALPHABET) for _ in range(random_length))
    return f"{clean_prefix}{token}"[:length]


def normalize_username(value: str) -> str:
    username = value.strip().lower()
    if not USERNAME_PATTERN.fullmatch(username):
        raise ValueError("Username must be 3-30 characters and use only letters, numbers, hyphen, or underscore.")
    if username in RESERVED_USERNAMES:
        raise ValueError("This username is reserved.")
    return username


def username_seed(*parts: str | None) -> str:
    raw = "-".join(part or "" for part in parts if part).lower()
    seed = re.sub(r"[^a-z0-9_-]+", "-", raw).strip("-_")
    if not seed:
        seed = "user"
    seed = seed[:24].strip("-_") or "user"
    if len(seed) < 3:
        seed = f"{seed}user"
    if seed in RESERVED_USERNAMES:
        seed = f"{seed}-user"
    return seed[:30]


def slugify(value: str | None, fallback: str = "company") -> str:
    slug = SLUG_PATTERN.sub("-", (value or "").lower()).strip("-")
    if not slug:
        slug = fallback
    return slug[:80].strip("-") or fallback
