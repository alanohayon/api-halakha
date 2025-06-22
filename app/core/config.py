from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache

class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_organization_id: Optional[str] = None
    openai_project_id: Optional[str] = None
    openai_project_ai: Optional[str] = None
    
    # Assistant IDs
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
    
    @property
    def get_database_url(self) -> str:
        """Retourne l'URL de la base de données Supabase"""
        # Extraire l'ID du projet depuis l'URL Supabase
        # Format attendu: https://project-id.supabase.co
        if not self.supabase_url or not self.supabase_anon_key:
            raise ValueError("SUPABASE_URL et SUPABASE_ANON_KEY doivent être configurés")
        
        try:
            # Extraire l'ID du projet de l'URL Supabase
            project_id = self.supabase_url.split('//')[1].split('.')[0]
            
            # Construire l'URL de connexion Supabase
            # Format: postgresql+asyncpg://postgres.[project_id]:[password]@aws-0-[project_id].pooler.supabase.com:6543/postgres
            return f"postgresql+asyncpg://postgres.{project_id}:{self.supabase_anon_key}@aws-0-{project_id}.pooler.supabase.com:6543/postgres"
        except (IndexError, AttributeError) as e:
            raise ValueError(f"Format d'URL Supabase invalide: {self.supabase_url}. Format attendu: https://project-id.supabase.co") from e
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

settings = Settings()
    

@lru_cache()
def get_settings() -> Settings:
    return Settings()