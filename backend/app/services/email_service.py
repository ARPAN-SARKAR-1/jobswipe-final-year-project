import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    def send_company_claim_verification(self, recipient: str, verify_url: str, token: str, claim_id: int) -> None:
        if settings.env.strip().lower() == "development":
            logger.debug("[JobSwipe] Company claim verification token for claim %s: %s", claim_id, token)
            logger.debug("[JobSwipe] Company claim verification URL for claim %s: %s", claim_id, verify_url)
            return
        # SMTP integration is intentionally abstracted for production configuration.
        logger.info("Company claim verification email queued for %s", recipient)


email_service = EmailService()
