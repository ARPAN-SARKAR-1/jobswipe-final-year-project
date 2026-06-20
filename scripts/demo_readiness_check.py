from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


FRONTEND_URL = os.getenv("DEMO_FRONTEND_URL", os.getenv("E2E_BASE_URL", "http://127.0.0.1:3000")).rstrip("/") + "/"
BACKEND_URL = os.getenv("DEMO_BACKEND_URL", os.getenv("API_BASE_URL", "http://127.0.0.1:8000")).rstrip("/") + "/"

BANNED_TEXT = [
    "final year project",
    "final-year project",
    "full-stack project",
    "demo project",
    "generate reset token",
    "future scope",
]


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


def fetch(url: str) -> tuple[int, str]:
    request = Request(url, headers={"User-Agent": "SwipeForSuccessDemoReadiness/1.0"})
    try:
        with urlopen(request, timeout=20) as response:  # noqa: S310 - URLs are explicit test env values.
            return response.status, response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")


def check_frontend(path: str) -> Check:
    url = urljoin(FRONTEND_URL, path.lstrip("/"))
    status, body = fetch(url)
    lowered = body.lower()
    banned = [item for item in BANNED_TEXT if item in lowered]
    return Check(f"frontend:{path}", status < 500 and not banned, f"status={status} banned={banned or 'none'}")


def check_backend_health() -> Check:
    status, body = fetch(urljoin(BACKEND_URL, "health"))
    return Check("backend:health", status == 200 and '"ok"' in body.lower(), f"status={status}")


def check_captcha() -> Check:
    status, body = fetch(urljoin(BACKEND_URL, "api/auth/captcha?purpose=login"))
    return Check("backend:captcha", status == 200 and "image_base64" in body and "answer" not in body, f"status={status}")


def main() -> int:
    checks = [
        lambda: check_frontend("/"),
        lambda: check_frontend("/login"),
        lambda: check_frontend("/register"),
        lambda: check_frontend("/contact"),
        check_backend_health,
        check_captcha,
    ]
    results: list[Check] = []
    try:
        for check in checks:
            results.append(check())
    except URLError as exc:
        print(f"FAIL demo readiness could not reach configured URLs: {exc.__class__.__name__}")
        return 1

    failed = [result for result in results if not result.ok]
    for result in results:
        print(f"{'PASS' if result.ok else 'FAIL'} {result.name}: {result.detail}")
    print(f"summary={len(results) - len(failed)}/{len(results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
