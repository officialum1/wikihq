from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Wikipedia Platform API"
    database_url: str = Field(
        default="postgresql://wiki:wiki@localhost:5432/wikipedia",
        validation_alias="DATABASE_URL",
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def fix_postgres_dialect(cls, value: str) -> str:
        if isinstance(value, str) and value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql://", 1)
        return value
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    elasticsearch_url: str = Field(
        default="http://localhost:9200",
        validation_alias="ELASTICSEARCH_URL",
    )
    jwt_secret: str = Field(
        default="local-development-jwt-secret-change-before-production",
        validation_alias="JWT_SECRET",
    )
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=1440,
        validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    cors_origins_raw: str | list[str] = Field(
        default=["http://localhost:3000"],
        validation_alias="CORS_ORIGINS",
    )
    admin_bootstrap_username: str = Field(default="", validation_alias="ADMIN_BOOTSTRAP_USERNAME")
    admin_bootstrap_email: str = Field(default="", validation_alias="ADMIN_BOOTSTRAP_EMAIL")
    admin_bootstrap_password: str = Field(default="", validation_alias="ADMIN_BOOTSTRAP_PASSWORD")

    @property
    def cors_origins(self) -> list[str]:
        val = self.cors_origins_raw
        if isinstance(val, str):
            return [origin.strip() for origin in val.split(",") if origin.strip()]
        if isinstance(val, list):
            return val
        return ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
