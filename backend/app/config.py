from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DATABASE_URL = f"sqlite:///{(Path(__file__).resolve().parents[1] / 'leadpilot_local.db').as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = DEFAULT_DATABASE_URL
    database_echo: bool = False
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_pool_timeout: int = 30
    request_timeout: int = 30
    google_places_api_key: str = ""
    token_encryption_key: str = "leadpilot-local-dev-key-change-me"
    encryption_algorithm: str = "Fernet"
    jwt_secret: str = "leadpilot-jwt-local-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    admin_auth_enabled: bool = False
    admin_username: str = "admin"
    admin_password: str = "admin"
    dry_run: bool = True
    frontend_origin: str = "http://localhost:5173"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    log_level: str = "INFO"
    api_rate_limit: int = 100
    api_rate_limit_window: int = 60
    development_mode: bool = True
    webhook_signing_secret: str = Field(default="")


settings = Settings()
