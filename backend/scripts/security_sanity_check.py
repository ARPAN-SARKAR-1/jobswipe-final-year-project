from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

DATABASE_URL_PATTERN = re.compile(
    r"mysql(?:\+pymysql)?://(?P<user>[^:\s/@<>]+):(?P<password>[^@\s<>]+)@(?P<host>[^/\s<>]+)",
    re.I,
)
SECRET_PATTERNS = [
    ("JWT secret assignment", re.compile(r"JWT_SECRET[ \t]*=[ \t]*(?!$|<|your|replace|change|dev|test|example)[\"']?[A-Za-z0-9_\-./+=]{16,}", re.I | re.M)),
    ("SMTP password assignment", re.compile(r"SMTP_PASSWORD[ \t]*=[ \t]*(?!$|<|your|replace|change|example|if-using)[^\s]+", re.I | re.M)),
    ("Brevo API key assignment", re.compile(r"BREVO_API_KEY[ \t]*=[ \t]*(?!$|<|your|replace|change|example)[^\s]+", re.I | re.M)),
    ("Resend API key assignment", re.compile(r"RESEND_API_KEY[ \t]*=[ \t]*(?!$|<|your|replace|change|example|if-using)[^\s]+", re.I | re.M)),
    ("Cloudinary secret assignment", re.compile(r"CLOUDINARY_API_SECRET[ \t]*=[ \t]*(?!$|<|your|replace|change|example)[^\s]+", re.I | re.M)),
]

FRONTEND_SECRET_LOG_PATTERN = re.compile(r"console\.(log|info|debug)\([^)]*(token|password|secret|api[_-]?key)", re.I | re.S)
CAPTCHA_RESPONSE_PATTERN = re.compile(r"class\s+CaptchaResponse\b(?P<body>[\s\S]{0,700})", re.I)
TEXT_CAPTCHA_PATTERN = re.compile(r"\bquestion\s*:", re.I)

SKIP_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".webp",
    ".pdf",
    ".zip",
    ".woff",
    ".woff2",
}


def git_ls_files() -> list[Path]:
    result = subprocess.run(["git", "ls-files"], cwd=REPO_ROOT, text=True, capture_output=True, check=True)
    return [REPO_ROOT / line.strip() for line in result.stdout.splitlines() if line.strip()]


def read_text(path: Path) -> str | None:
    if path.suffix.lower() in SKIP_SUFFIXES:
        return None
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def database_url_looks_real(text: str) -> bool:
    for match in DATABASE_URL_PATTERN.finditer(text):
        password = match.group("password").lower()
        host = match.group("host").lower()
        if any(token in password for token in ("password", "pass", "example", "replace", "change")):
            continue
        if host.startswith(("localhost", "127.0.0.1")):
            continue
        return True
    return False


def main() -> int:
    failures: list[str] = []
    warnings: list[str] = []
    tracked = git_ls_files()

    for path in tracked:
        rel = relative(path)
        lowered = rel.lower()
        if lowered.endswith(".env") or lowered.endswith(".env.local"):
            failures.append(f"{rel}: tracked environment file")
        if "node_modules/" in lowered or "/.next/" in lowered or "/venv/" in lowered or "/uploads/" in lowered:
            failures.append(f"{rel}: generated folder tracked")

        text = read_text(path)
        if text is None:
            continue

        for label, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"{rel}: possible {label}")

        if database_url_looks_real(text):
            failures.append(f"{rel}: possible real database URL with password")

        if rel.startswith("frontend/") and FRONTEND_SECRET_LOG_PATTERN.search(text):
            failures.append(f"{rel}: console output may expose a sensitive value")

        if rel.startswith(("frontend/app/", "frontend/components/", "frontend/lib/")) and "localhost" in text.lower():
            warnings.append(f"{rel}: hardcoded localhost reference in frontend source")

        if rel == "backend/app/schemas/auth.py":
            match = CAPTCHA_RESPONSE_PATTERN.search(text)
            if match and TEXT_CAPTCHA_PATTERN.search(match.group("body")):
                failures.append(f"{rel}: CaptchaResponse appears to expose question text")

    if failures:
        print("FAIL security sanity check")
        for item in failures:
            print(f"- {item}")
        if warnings:
            print("Warnings:")
            for item in warnings:
                print(f"- {item}")
        return 1

    print("PASS security sanity check")
    if warnings:
        print("Warnings:")
        for item in warnings:
            print(f"- {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
