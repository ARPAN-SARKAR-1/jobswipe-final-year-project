from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app


def main() -> None:
    captcha_routes = [route.path for route in app.routes if "captcha" in route.path or route.path == "/health"]
    for path in captcha_routes:
        print(path)
    if "/api/auth/captcha" not in captcha_routes:
        raise SystemExit("Missing /api/auth/captcha route")
    print("CAPTCHA_ROUTE_PRESENT=True")


if __name__ == "__main__":
    main()
