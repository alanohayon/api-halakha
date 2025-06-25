from functools import lru_cache
from app.core.config import Settings, get_settings

@lru_cache
def get_settings_dependency() -> Settings:
    """Dépendance pour injecter les settings dans les endpoints"""
    return get_settings()
