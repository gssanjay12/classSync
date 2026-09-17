from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "ClassPoll"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "classpoll_super_secret_jwt_access_key_replace_in_production_987654321"
    REFRESH_SECRET_KEY: str = "classpoll_super_secret_jwt_refresh_key_replace_in_production_123456789"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DATABASE_URL: str = "sqlite:///./classpoll.db"
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8000"
    
    EMAIL_HOST: Optional[str] = None
    EMAIL_PORT: Optional[int] = 587
    EMAIL_USERNAME: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "noreply@classpoll.app"

    # Official WhatsApp Cloud / Business API
    WHATSAPP_API_URL: str = "https://graph.facebook.com/v20.0"
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    WHATSAPP_ACCESS_TOKEN: Optional[str] = None
    WHATSAPP_TEMPLATE_NAME: str = "classpoll_reminder"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
