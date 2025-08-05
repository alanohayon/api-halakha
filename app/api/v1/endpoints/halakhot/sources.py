from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client
from typing import List, Optional

from app.core.database import get_supabase
from app.services.supabase_service import SupabaseService
from app.api.deps import SupabaseServiceDep

router = APIRouter()

# READ - Lister toutes les sources
@router.get("/", response_model=List[dict])
async def list_sources(
    service: SupabaseServiceDep,
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments à retourner"),
    name: Optional[str] = Query(None, description="Filtrer par nom de source")
):
    """Lister toutes les sources avec pagination et filtres"""
    return await service.get_sources(skip=skip, limit=limit, name=name)

# READ - Récupérer une source spécifique
@router.get("/{source_id}")
async def get_source(
    source_id: int,
    service: SupabaseServiceDep
):
    """Récupérer une source par ID"""
    source = await service.get_source_by_id(source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found"
        )
    return source

# READ - Récupérer toutes les halakhot associées à une source
@router.get("/{source_id}/halakhot")
async def get_source_halakhot(
    source_id: int,
    service: SupabaseServiceDep,
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments à retourner")
):
    """Récupérer toutes les halakhot associées à une source"""
    
    # Vérifier que la source existe
    source = await service.get_source_by_id(source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found"
        )
    
    # Récupérer les halakhot
    halakhot = await service.get_halakhot_by_source(source_id, skip=skip, limit=limit)
    return halakhot 