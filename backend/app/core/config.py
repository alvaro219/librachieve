from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_SECRET = "dev-insecure-secret-change-me-before-deploying"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    environment: str = "development"
    secret_key: str = _DEV_SECRET
    frontend_url: str = "http://localhost:5173"

    database_url: str = "postgresql+asyncpg://librachieve:librachieve@localhost:5432/librachieve"
    redis_url: str = "redis://localhost:6379/0"

    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    jwt_algorithm: str = "HS256"

    steam_api_key: str = ""
    igdb_client_id: str = ""
    igdb_client_secret: str = ""
    igdb_cache_ttl_seconds: int = 60 * 60 * 24

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @model_validator(mode="after")
    def _check_secret(self):
        if self.environment != "development" and (
            self.secret_key == _DEV_SECRET or len(self.secret_key) < 32
        ):
            raise ValueError("SECRET_KEY must be set to a random string of 32+ chars")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
