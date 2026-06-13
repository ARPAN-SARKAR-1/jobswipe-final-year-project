from functools import lru_cache
import os
from pathlib import Path
from urllib.parse import urlparse

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"
LOCAL_DEVELOPMENT_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


class Settings(BaseSettings):
    database_url: str = Field(alias="DATABASE_URL")
    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=1440, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    upload_dir: str = Field(default="uploads", alias="UPLOAD_DIR")
    frontend_url: str = Field(alias="FRONTEND_URL")
    env: str = Field(default="development", alias="ENV")
    cloudinary_cloud_name: str | None = Field(default=None, alias="CLOUDINARY_CLOUD_NAME")
    cloudinary_api_key: str | None = Field(default=None, alias="CLOUDINARY_API_KEY")
    cloudinary_api_secret: str | None = Field(default=None, alias="CLOUDINARY_API_SECRET")
    captcha_enabled: bool = Field(default=True, alias="CAPTCHA_ENABLED")
    email_verification_required: bool = Field(default=True, alias="EMAIL_VERIFICATION_REQUIRED")
    twofa_required_roles: str = Field(default="OWNER,ADMIN,RECRUITER", alias="TWOFA_REQUIRED_ROLES")
    email_provider: str = Field(default="console", alias="EMAIL_PROVIDER")
    email_from: str | None = Field(default=None, alias="EMAIL_FROM")
    resend_api_key: str | None = Field(default=None, alias="RESEND_API_KEY")
    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str | None = Field(default=None, alias="SMTP_USER")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    otp_expire_minutes: int = Field(default=5, alias="OTP_EXPIRE_MINUTES")
    otp_max_attempts: int = Field(default=5, alias="OTP_MAX_ATTEMPTS")
    email_otp_resend_cooldown_seconds: int = Field(default=60, alias="EMAIL_OTP_RESEND_COOLDOWN_SECONDS")
    captcha_expire_minutes: int = Field(default=5, alias="CAPTCHA_EXPIRE_MINUTES")
    trusted_device_days: int = Field(default=30, alias="TRUSTED_DEVICE_DAYS")
    trusted_device_cookie_name: str = Field(default="swipe_trusted_device", alias="TRUSTED_DEVICE_COOKIE_NAME")

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_production_database_url(self) -> "Settings":
        if not self.is_production and not self.is_deployed_runtime:
            return self
        database_url = self.database_url.strip()
        parsed = urlparse(database_url)
        hostname = (parsed.hostname or "").lower()
        invalid_host = hostname in {"localhost", "127.0.0.1", "::1"} or hostname.endswith(".railway.internal")
        if not database_url or parsed.scheme != "mysql+pymysql" or invalid_host:
            raise ValueError("Invalid production DATABASE_URL. Use mysql+pymysql://...")
        return self

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        if not path.is_absolute():
            path = BACKEND_DIR / path
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def is_production(self) -> bool:
        return self.env.lower() == "production"

    @property
    def is_deployed_runtime(self) -> bool:
        return any(os.getenv(name) for name in ("RENDER", "RENDER_SERVICE_ID", "RENDER_EXTERNAL_HOSTNAME"))

    @property
    def cors_origins(self) -> list[str]:
        origins = [origin.strip().rstrip("/") for origin in self.frontend_url.split(",") if origin.strip()]
        if not self.is_production:
            origins.extend(LOCAL_DEVELOPMENT_ORIGINS)
        if self.is_production:
            origins = [origin for origin in origins if origin != "*"]
        return list(dict.fromkeys(origins))

    @property
    def cloudinary_enabled(self) -> bool:
        return all(
            [
                self.cloudinary_cloud_name,
                self.cloudinary_api_key,
                self.cloudinary_api_secret,
            ]
        )

    @property
    def twofa_required_role_set(self) -> set[str]:
        return {role.strip().upper() for role in self.twofa_required_roles.split(",") if role.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
