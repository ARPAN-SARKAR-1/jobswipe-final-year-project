from pathlib import Path
import os
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import HTTPException

from app.core.config import settings
from app.services.email_service import send_security_code


def domain(email: str) -> str:
    return email.rsplit("@", 1)[-1].lower() if "@" in email else "unknown"


def main() -> None:
    recipient = os.getenv("TEST_EMAIL_TO") or os.getenv("SUPPORT_EMAIL")
    if not recipient:
        raise SystemExit("TEST_EMAIL_TO or SUPPORT_EMAIL is required")
    try:
        send_security_code(recipient, "000000", "Swipe for Success email configuration test")
    except HTTPException as exc:
        print(f"EMAIL_TEST_SUCCESS=False provider={settings.email_provider.lower()} recipient_domain={domain(recipient)} status={exc.status_code}")
        print(f"EMAIL_TEST_ERROR={exc.detail}")
        raise SystemExit(1)
    except Exception as exc:
        print(f"EMAIL_TEST_SUCCESS=False provider={settings.email_provider.lower()} recipient_domain={domain(recipient)} error_class={exc.__class__.__name__}")
        raise SystemExit(1)
    print(f"EMAIL_TEST_SUCCESS=True provider={settings.email_provider.lower()} recipient_domain={domain(recipient)}")


if __name__ == "__main__":
    main()
