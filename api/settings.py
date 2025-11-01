import os
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "AgentSentry API"
    environment: str = "dev"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./agentsentry.db")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    api_key: str | None = os.getenv("AGENTSENTRY_API_KEY")

    model_config = SettingsConfigDict(env_file="../.env.dev", env_file_encoding="utf-8", extra="ignore")

settings = Settings()