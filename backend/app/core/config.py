from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"
EXAMPLE_ENV_FILE = BACKEND_DIR / ".env.example"


class Settings(BaseSettings):
    database_url: str = Field(alias="DATABASE_URL")
    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    upload_dir: str = Field(default="uploads", alias="UPLOAD_DIR")
    frontend_url: str = Field(alias="FRONTEND_URL")
    env: str = Field(default="development", alias="ENV")

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE if ENV_FILE.exists() else EXAMPLE_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    @property
    def is_production(self) -> bool:
        return self.env.strip().lower() == "production"

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if not self.is_production:
            return self

        weak_secrets = {"change_this_secret", "changeme", "dev_secret", "secret", "jobswipe_secret"}
        normalized_secret = self.jwt_secret.strip()
        if not normalized_secret or normalized_secret.lower() in weak_secrets or len(normalized_secret) < 32:
            raise ValueError("JWT_SECRET must be set to a strong value in production.")

        origins = [origin.strip() for origin in self.frontend_url.split(",") if origin.strip()]
        if not origins:
            raise ValueError("FRONTEND_URL must be configured in production.")
        if "*" in origins:
            raise ValueError("FRONTEND_URL cannot include '*' in production.")
        return self

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        if not path.is_absolute():
            path = BACKEND_DIR / path
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def cors_origins(self) -> list[str]:
        origins = [origin.strip() for origin in self.frontend_url.split(",") if origin.strip()]
        if self.is_production and "*" in origins:
            raise ValueError("FRONTEND_URL cannot include '*' in production.")
        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
