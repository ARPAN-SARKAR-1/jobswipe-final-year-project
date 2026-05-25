from sqlalchemy import Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class SecuritySettings(TimestampMixin, Base):
    __tablename__ = "security_settings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    captcha_login_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    captcha_signup_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    captcha_forgot_password_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    captcha_reports_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    captcha_company_claims_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
