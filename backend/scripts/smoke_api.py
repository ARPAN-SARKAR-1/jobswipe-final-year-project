from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/") + "/"


@dataclass
class SmokeResult:
    name: str
    ok: bool
    detail: str


def request_json(path: str, method: str = "GET", payload: dict[str, Any] | None = None) -> tuple[int, Any, str]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        urljoin(API_BASE_URL, path.lstrip("/")),
        data=body,
        method=method,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=15) as response:  # noqa: S310 - URL comes from explicit test env.
            raw = response.read().decode("utf-8", errors="replace")
            return response.status, json.loads(raw) if raw else None, raw
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            data = raw
        return exc.code, data, raw


def no_stack_trace(raw: str) -> bool:
    lowered = raw.lower()
    return "traceback" not in lowered and "stack trace" not in lowered and "sqlalchemy.exc" not in lowered


def check_health() -> SmokeResult:
    status, data, raw = request_json("/health")
    ok = status == 200 and isinstance(data, dict) and data.get("status") == "ok" and no_stack_trace(raw)
    return SmokeResult("health", ok, f"status={status}")


def check_captcha(purpose: str) -> SmokeResult:
    status, data, raw = request_json(f"/api/auth/captcha?purpose={purpose}")
    ok = (
        status == 200
        and isinstance(data, dict)
        and isinstance(data.get("challenge_id"), str)
        and isinstance(data.get("image_base64"), str)
        and data["image_base64"].startswith("data:image/png;base64,")
        and "answer" not in data
        and no_stack_trace(raw)
    )
    return SmokeResult(f"captcha:{purpose}", ok, f"status={status} image_base64={isinstance(data, dict) and bool(data.get('image_base64'))}")


def check_404() -> SmokeResult:
    status, _data, raw = request_json("/api/not-a-real-route")
    ok = status == 404 and no_stack_trace(raw)
    return SmokeResult("controlled_404", ok, f"status={status}")


def check_bad_support_payload() -> SmokeResult:
    status, _data, raw = request_json("/api/support/tickets", method="POST", payload={})
    ok = status in {400, 422} and no_stack_trace(raw)
    return SmokeResult("support_bad_payload", ok, f"status={status}")


def check_protected_route() -> SmokeResult:
    status, _data, raw = request_json("/api/jobseeker/profile")
    ok = status in {401, 403} and no_stack_trace(raw)
    return SmokeResult("protected_route_without_token", ok, f"status={status}")


def main() -> int:
    checks = [
        check_health,
        lambda: check_captcha("login"),
        lambda: check_captcha("contact"),
        check_404,
        check_bad_support_payload,
        check_protected_route,
    ]
    results: list[SmokeResult] = []
    try:
        for check in checks:
            results.append(check())
    except URLError as exc:
        print(f"FAIL could not reach API_BASE_URL={API_BASE_URL} error={exc.__class__.__name__}")
        return 1

    failed = [result for result in results if not result.ok]
    for result in results:
        print(f"{'PASS' if result.ok else 'FAIL'} {result.name}: {result.detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
