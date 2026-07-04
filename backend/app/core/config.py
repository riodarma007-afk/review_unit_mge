from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "OPTRACK Dashboard API"
    
    # Database Settings (wajib di-set lewat env var / .env, tidak ada default)
    DB_HOST: str
    DB_PORT: int = 3306
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Frontend URL for CORS
    FRONTEND_URL: str = "http://localhost:5173"

    # Fuel API Settings (wajib di-set lewat env var / .env, tidak ada default)
    FUEL_API_URL: str
    FUEL_API_KEY: str
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
