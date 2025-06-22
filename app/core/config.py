from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache

class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str
    database_url: str
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_organization_id: Optional[str] = None
    openai_project_id: Optional[str] = None
    openai_project_ai: Optional[str] = None
    
    # Assistant IDs OpenAI
    asst_halakha: Optional[str] = None
    asst_prompt_dalle: Optional[str] = None
    asst_insta_post: Optional[str] = None
    asst_legend_post: Optional[str] = None
    
    # Notion Configuration
    notion_api_token: Optional[str] = None
    notion_database_id_post_halakha: Optional[str] = None
    
    # API Configuration
    app_name: str = "Halakha API"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS
    backend_cors_origins: List[str] = []
    
    # Logging
    log_level: str = "INFO"
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hour
    
    # Database Configuration
    database_echo: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

settings = Settings()
    

@lru_cache()
def get_settings() -> Settings:
    return Settings()