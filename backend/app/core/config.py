from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "OPTRACK Dashboard API"
    
    # Database Settings
    DB_HOST: str = "103.58.102.44"
    DB_PORT: int = 3306
    DB_USER: str = "mge_planning"
    DB_PASSWORD: str = "PlanningMGE2026"
    DB_NAME: str = "mge_planning_staging"
    
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Frontend URL for CORS
    FRONTEND_URL: str = "http://localhost:5173"
    
    # Fuel API Settings
    FUEL_API_URL: str = "https://planning.mge.co.id/api/portal/fuel"
    FUEL_API_KEY: str = "mge_fuel_3m9gzdIRGQf2AFtq7PeYSBNxiZLJrcky6nXuKhDWoHMEwlj4"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
