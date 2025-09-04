from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List, Union
from functools import lru_cache
import os

class Settings(BaseSettings):
    """Configuration centralisée de l'application Halakha API"""
    
    # Configuration de base Pydantic v2
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True
    )
    
    # ============================================================================
    # SUPABASE CONFIGURATION
    # ============================================================================
    supabase_url: str = Field(
        ..., 
        description="URL de votre projet Supabase",
        pattern=r"^https://[a-zA-Z0-9-]+\.supabase\.co$"
    )
    supabase_anon_key: str = Field(
        ..., 
        description="Clé anonyme publique Supabase",
        min_length=50
    )
    supabase_service_key: str = Field(
        ..., 
        description="Clé de service privée Supabase",
        min_length=50
    )
    database_url: str = Field(
        ..., 
        description="URL de connexion à la base de données PostgreSQL",
        pattern=r"^postgresql\+asyncpg://.*$"
    )
    
    # ============================================================================
    # OPENAI CONFIGURATION
    # ============================================================================
    openai_api_key: Optional[str] = Field(
        None, 
        description="Clé API OpenAI",
        min_length=40
    )
    openai_organization_id: Optional[str] = Field(
        None, 
        description="ID de l'organisation OpenAI"
    )
    openai_project_id: Optional[str] = Field(
        None, 
        description="ID du projet OpenAI"
    )
    openai_project_ai: Optional[str] = Field(
        None, 
        description="ID du projet AI OpenAI"
    )
    
    # Assistant IDs OpenAI
    asst_halakha: Optional[str] = Field(
        None, 
        description="ID de l'assistant Halakha OpenAI"
    )
    asst_insta_post: Optional[str] = Field(
        None, 
        description="ID de l'assistant post Instagram OpenAI"
    )
    asst_legend_post: Optional[str] = Field(
        None, 
        description="ID de l'assistant légende post OpenAI"
    )
    
    # ============================================================================
    # NOTION CONFIGURATION
    # ============================================================================
    notion_api_token: Optional[str] = Field(
        None, 
        description="Token d'API Notion",
        min_length=40
    )
    notion_database_id_post_halakha: Optional[str] = Field(
        None, 
        description="ID de la base de données Notion pour les posts Halakha"
    )
    
    # ============================================================================
    # API CONFIGURATION
    # ============================================================================
    app_name: str = Field(
        default="Halakha API",
        description="Nom de l'application"
    )
    debug: bool = Field(
        default=False,
        description="Mode debug (désactivé en production)"
    )
    host: str = Field(
        default="0.0.0.0",
        description="Adresse d'écoute du serveur"
    )
    port: int = Field(
        default=8000,
        ge=1024,
        le=65535,
        description="Port d'écoute du serveur"
    )
    
    # ============================================================================
    # CORS CONFIGURATION
    # ============================================================================
    backend_cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Origines autorisées pour CORS"
    )
    
    # ============================================================================
    # LOGGING CONFIGURATION
    # ============================================================================
    log_level: str = Field(
        default="INFO",
        description="Niveau de log",
        pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"
    )
    log_format: str = Field(
        default="json",
        description="Format des logs (json ou text)",
        pattern=r"^(json|text)$"
    )
    
    # ============================================================================
    # RATE LIMITING CONFIGURATION
    # ============================================================================
    rate_limit_requests: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Nombre maximum de requêtes par fenêtre"
    )
    rate_limit_window: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Fenêtre de temps pour le rate limiting en secondes"
    )
    
    # ============================================================================
    # DATABASE CONFIGURATION
    # ============================================================================
    database_echo: bool = Field(
        default=False,
        description="Afficher les requêtes SQL (désactivé en production)"
    )
    database_pool_size: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Taille du pool de connexions"
    )
    database_max_overflow: int = Field(
        default=20,
        ge=0,
        le=100,
        description="Nombre maximum de connexions en surplus"
    )
    database_pool_timeout: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Timeout du pool de connexions en secondes"
    )
    database_pool_recycle: int = Field(
        default=3600,
        ge=300,
        le=7200,
        description="Recyclage des connexions en secondes"
    )
    
    # ============================================================================
    # SECURITY CONFIGURATION
    # ============================================================================
    secret_key: str = Field(
        ...,  # Obligatoire - pas de valeur par défaut
        description="Clé secrète pour les tokens JWT (OBLIGATOIRE)",
        min_length=32
    )
    api_key: str = Field(
        ...,  # Obligatoire pour l'authentification API
        description="Clé API pour l'authentification des requêtes (OBLIGATOIRE)",
        min_length=32
    )
    access_token_expire_minutes: int = Field(
        default=30,
        ge=5,
        le=1440,
        description="Durée d'expiration du token d'accès en minutes"
    )
    
    # ============================================================================
    # TIMEOUTS CONFIGURATION (PRODUCTION OPTIMIZED)
    # ============================================================================
    openai_timeout: int = Field(
        default=300,  # 5 minutes au lieu de 1h
        ge=60,
        le=600,
        description="Timeout OpenAI en secondes"
    )
    notion_timeout: int = Field(
        default=60,  # 1 minute
        ge=30,
        le=120,
        description="Timeout Notion en secondes"
    )
    supabase_timeout: int = Field(
        default=30,  # 30 secondes
        ge=10,
        le=60,
        description="Timeout Supabase en secondes"
    )
    request_timeout: int = Field(
        default=120,  # 2 minutes pour les requêtes API
        ge=30,
        le=300,
        description="Timeout général des requêtes en secondes"
    )
    
    # ============================================================================
    # CACHE CONFIGURATION
    # ============================================================================
    redis_url: Optional[str] = Field(
        None,
        description="URL Redis pour le cache",
        pattern=r"^redis://.*$"
    )
    cache_ttl: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Durée de vie du cache en secondes"
    )
    
    # ============================================================================
    # VALIDATORS
    # ============================================================================

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Valide et assemble les origines CORS"""
        if isinstance(v, str):
            if v.startswith("["):
                # Si c'est une liste JSON
                import json
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    raise ValueError("Format JSON invalide pour backend_cors_origins")
            else:
                # Si c'est une chaîne séparée par des virgules
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return v
        else:
            raise ValueError("backend_cors_origins doit être une chaîne ou une liste")
    
    @field_validator("log_level", mode="before")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Valide le niveau de log"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level doit être l'un de: {', '.join(valid_levels)}")
        return v.upper()
    
    @field_validator("database_url", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Valide l'URL de la base de données"""
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError("database_url doit commencer par 'postgresql+asyncpg://'")
        return v
    
    @field_validator("supabase_url", mode="before")
    @classmethod
    def validate_supabase_url(cls, v: str) -> str:
        """Valide l'URL Supabase"""
        if not v.startswith("https://") or ".supabase.co" not in v:
            raise ValueError("supabase_url doit être une URL Supabase valide")
        return v.rstrip("/")
    
    @field_validator("secret_key", mode="after")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Valide la clé secrète"""
        if v == "your-secret-key-change-in-production":
            raise ValueError(
                "SECURITE: La clé secrète par défaut est interdite. "
                "Configurez SECRET_KEY dans vos variables d'environnement."
            )
        return v
    
    # ============================================================================
    # PROPERTIES UTILITAIRES
    # ============================================================================
    
    @property
    def is_production(self) -> bool:
        """Détermine si l'environnement est en production"""
        return not self.debug and os.getenv("ENVIRONMENT", "").upper() == "PRODUCTION"
    
    @property
    def database_config(self) -> dict:
        """Configuration de la base de données pour SQLAlchemy"""
        return {
            "echo": self.database_echo,
            "pool_size": self.database_pool_size,
            "max_overflow": self.database_max_overflow,
            "pool_timeout": self.database_pool_timeout,
            "pool_recycle": self.database_pool_recycle,
            "pool_pre_ping": True,
        }
    
    @property
    def cors_config(self) -> dict:
        """Configuration CORS pour FastAPI"""
        return {
            "allow_origins": self.backend_cors_origins,
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Authorization", "Content-Type", "X-API-Key"],
        }

# ============================================================================
# INSTANCE GLOBALE ET FONCTIONS UTILITAIRES
# ============================================================================

@lru_cache
def get_settings() -> Settings:
    """Retourne une instance singleton des paramètres"""
    return Settings()

# Instance globale pour compatibilité
settings = get_settings()
