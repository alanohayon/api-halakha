from functools import lru_cache
from typing import Annotated
from fastapi import Depends
from app.core.config import Settings, get_settings
from app.services.openai_service import OpenAIService
from app.services.notion_service import NotionService
from app.services.supabase_service import SupabaseService
from app.services.processing_service import ProcessingService

@lru_cache
def get_settings_dependency() -> Settings:
    """Dépendance pour injecter les settings dans les endpoints"""
    return get_settings()

@lru_cache
def get_openai_service() -> OpenAIService:
    """
    Dépendance pour injecter OpenAIService avec cache LRU.
    Le service est réutilisé entre les requêtes pour optimiser les performances.
    """
    return OpenAIService()

@lru_cache
def get_notion_service() -> NotionService:
    """
    Dépendance pour injecter NotionService avec cache LRU.
    """
    return NotionService()

@lru_cache
def get_supabase_service() -> SupabaseService:
    """
    Dépendance pour injecter SupabaseService avec cache LRU.
    """
    return SupabaseService()

@lru_cache
def get_processing_service() -> ProcessingService:
    """
    Dépendance pour injecter ProcessingService avec cache LRU.
    """
    return ProcessingService()

# Type aliases pour FastAPI
SettingsDep = Annotated[Settings, Depends(get_settings_dependency)]
OpenAIServiceDep = Annotated[OpenAIService, Depends(get_openai_service)]
NotionServiceDep = Annotated[NotionService, Depends(get_notion_service)]
SupabaseServiceDep = Annotated[SupabaseService, Depends(get_supabase_service)]
ProcessingServiceDep = Annotated[ProcessingService, Depends(get_processing_service)]
