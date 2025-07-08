from functools import lru_cache
from typing import Annotated
from fastapi import Depends
from app.core.config import Settings, get_settings
from app.services.openai_service import OpenAIService

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

# Type aliases pour FastAPI
SettingsDep = Annotated[Settings, Depends(get_settings_dependency)]
OpenAIServiceDep = Annotated[OpenAIService, Depends(get_openai_service)]
