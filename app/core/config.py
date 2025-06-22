from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    database_url: str
    database_echo: bool = False
    
    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str
    
    # OpenAI Configuration
    openai_api_key: str
    openai_organization_id: Optional[str] = None
    openai_project_id: Optional[str] = None
    openai_project_ai: Optional[str] = None
    
    # Assistant IDs
    asst_halakha: str
    asst_prompt_dalle: str
    asst_insta_post: str
    asst_legend_post: str
    
    # Notion Configuration
    notion_api_token: str
    notion_database_id_post_halakha: str
    
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
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

settings = Settings()
    

@lru_cache()
def get_settings() -> Settings:
    return Settings()