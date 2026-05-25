from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class CaptchaChallenge(TimestampMixin, Base):
    __tablename__ = "captcha_challenges"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    challenge_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    answer_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
