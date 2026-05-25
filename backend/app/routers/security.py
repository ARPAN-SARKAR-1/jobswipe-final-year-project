from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.security import CaptchaChallengeRead
from app.services.captcha import create_captcha_challenge

router = APIRouter(prefix="/security", tags=["Security"])


@router.get("/captcha", response_model=CaptchaChallengeRead)
def captcha_challenge(db: Annotated[Session, Depends(get_db)]) -> CaptchaChallengeRead:
    challenge = create_captcha_challenge(db)
    return CaptchaChallengeRead(captcha_id=challenge.challenge_id, question=getattr(challenge, "question"))
