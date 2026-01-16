from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/ai_chat"
    
    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    
    # OpenAI
    openai_api_key: str = ""
    openai_proxy_url: Optional[str] = None
    openai_proxy_username: Optional[str] = None
    openai_proxy_password: Optional[str] = None
    
    # Bitrix24
    bitrix24_webhook_url: Optional[str] = None
    
    # App
    app_env: str = "development"
    debug: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()
