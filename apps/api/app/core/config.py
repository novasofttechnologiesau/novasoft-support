from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)
    DATABASE_URL: str
    JWT_SECRET: str = Field(min_length=32)
    JWT_ALGORITHM: Literal["HS256"] = "HS256"
    JWT_EXPIRE_MINUTES: int = Field(default=30, ge=1, le=480)
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:1420,tauri://localhost,http://tauri.localhost"
    AI_PROVIDER: Literal["mock", "deepseek"] = "mock"
    ALLOW_EXTERNAL_AI: bool = False
    DEEPSEEK_API_KEY: str = ""
    AI_MODEL: str = "deepseek-chat"
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_MB: int = Field(default=10, ge=1, le=25)
    ALLOW_DEMO_SEED: bool = False
    DEMO_SEED_PASSWORD: str = ""

    @field_validator("JWT_SECRET")
    @classmethod
    def reject_placeholder(cls, value):
        if len(set(value)) < 12 or any(word in value.lower() for word in ("change_me", "changeme", "replace_me")):
            raise ValueError("Generate a random JWT secret using scripts/configure_local.py")
        return value


    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
