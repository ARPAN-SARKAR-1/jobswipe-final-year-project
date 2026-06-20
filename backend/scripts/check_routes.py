from __future__ import annotations

import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app  # noqa: E402


CRITICAL_ROUTES = {
    "/health": {"GET"},
    "/api/auth/captcha": {"GET"},
    "/api/auth/login": {"POST"},
    "/api/auth/register": {"POST"},
    "/api/jobseeker/profile": {"GET", "PUT"},
    "/api/jobs/feed": {"GET"},
    "/api/support/tickets": {"POST"},
    "/api/admin/support-tickets": {"GET"},
}


def route_methods() -> dict[str, set[str]]:
    routes: dict[str, set[str]] = {}
    for route in app.routes:
        path = getattr(route, "path", "")
        methods = set(getattr(route, "methods", set()) or set())
        if path:
            routes.setdefault(path, set()).update(methods)
    return routes


def main() -> int:
    routes = route_methods()
    print(app.title)
    print(f"route_count={len(app.routes)}")
    missing: list[str] = []
    for path, expected_methods in CRITICAL_ROUTES.items():
        actual_methods = routes.get(path)
        if not actual_methods:
            missing.append(f"{path} missing")
            continue
        missing_methods = expected_methods - actual_methods
        if missing_methods:
            missing.append(f"{path} missing methods {sorted(missing_methods)}")
    if missing:
        print("FAIL critical routes:")
        for item in missing:
            print(f"- {item}")
        return 1
    print("PASS critical routes present")
    for path in sorted(CRITICAL_ROUTES):
        print(f"{path} {sorted(routes[path])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
