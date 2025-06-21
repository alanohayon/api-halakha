from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str
    database_echo: bool = False
    
    # OpenAI
    openai_api_key: str
    openai_organization_id: Optional[str] = None
    openai_project_id: Optional[str] = None
    
    # Notion
    notion_api_token: str
    notion_database_id: str
    
    # API
    api_v1_str: str = "/api/v1"
    project_name: str = "Halakha Processing API"
    debug: bool = False
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()