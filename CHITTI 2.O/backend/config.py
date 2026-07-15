from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 50
    SESSION_TTL_MINUTES: int = 60


settings = Settings()
