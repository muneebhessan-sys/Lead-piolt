from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DATABASE_URL = f"sqlite:///{(Path(__file__).resolve().parents[1] / 'leadpilot_local.db').as_posix()}"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = DEFAULT_DATABASE_URL
    request_timeout: int = 30
    google_places_api_key: str = ""
    token_encryption_key: str = ""
    dry_run: bool = True
    frontend_origin: str = "http://localhost:5173"
settings = Settings()
