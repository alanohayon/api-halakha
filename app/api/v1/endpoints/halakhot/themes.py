from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client
from typing import List, Optional

from app.core.database import get_supabase
from app.services.supabase_service import SupabaseService
from app.api.deps import SupabaseServiceDep

router = APIRouter()

# READ - Lister tous les thèmes
@router.get("/", response_model=List[dict])
async def list_themes(
    service: SupabaseServiceDep,
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments à retourner"),
    name: Optional[str] = Query(None, description="Filtrer par nom de thème")
):
    """Lister tous les thèmes avec pagination et filtres"""
    return await service.get_themes(skip=skip, limit=limit, name=name)

# READ - Récupérer un thème spécifique
@router.get("/{theme_id}")
async def get_theme(
    theme_id: int,
    service: SupabaseServiceDep
):
    """Récupérer un thème par ID"""
    theme = await service.get_theme_by_id(theme_id)
    if not theme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Theme not found"
        )
    return theme

# READ - Récupérer toutes les halakhot associées à un thème
@router.get("/{theme_id}/halakhot")
async def get_theme_halakhot(
    theme_id: int,
    service: SupabaseServiceDep,
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments à retourner")
):
    """Récupérer toutes les halakhot associées à un thème"""
    
    # Vérifier que le thème existe
    theme = await service.get_theme_by_id(theme_id)
    if not theme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Theme not found"
        )
    
    # Récupérer les halakhot
    halakhot = await service.get_halakhot_by_theme(theme_id, skip=skip, limit=limit)
    return halakhot 