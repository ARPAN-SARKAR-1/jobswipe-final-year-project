from pathlib import Path
import os
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import HTTPException

from app.core.config import settings
from app.services.email_service import ensure_email_provider_configured, send_security_code


def domain(email: str) -> str:
    return email.rsplit("@", 1)[-1].lower() if "@" in email else "unknown"


def main() -> None:
    provider = settings.email_provider.lower()
    recipient = os.getenv("TEST_EMAIL_TO")
    try:
        ensure_email_provider_configured()
    except HTTPException as exc:
        print(f"EMAIL_PROVIDER_CONFIGURED=False provider={provider} status={exc.status_code}")
        print(f"EMAIL_PROVIDER_ERROR={exc.detail}")
        raise SystemExit(1)

    print(f"EMAIL_PROVIDER_CONFIGURED=True provider={provider}")
    if not recipient:
        print("EMAIL_TEST_SENT=False reason=TEST_EMAIL_TO_not_set")
        return

    try:
        send_security_code(recipient, "000000", "Swipe for Success email provider test")
    except HTTPException as exc:
        print(f"EMAIL_TEST_SENT=False provider={provider} recipient_domain={domain(recipient)} status={exc.status_code}")
        print(f"EMAIL_TEST_ERROR={exc.detail}")
        raise SystemExit(1)
    except Exception as exc:
        print(f"EMAIL_TEST_SENT=False provider={provider} recipient_domain={domain(recipient)} error_class={exc.__class__.__name__}")
        raise SystemExit(1)
    print(f"EMAIL_TEST_SENT=True provider={provider} recipient_domain={domain(recipient)}")


if __name__ == "__main__":
    main()
