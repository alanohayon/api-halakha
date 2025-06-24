from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client
from typing import List, Optional

from app.core.database import get_supabase
from app.services.supabase_service import SupabaseService

router = APIRouter()

# READ - Lister tous les tags
@router.get("/", response_model=List[dict])
async def list_tags(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments à retourner"),
    name: Optional[str] = Query(None, description="Filtrer par nom de tag"),
    supabase: Client = Depends(get_supabase)
):
    """Lister tous les tags avec pagination et filtres"""
    service = SupabaseService(supabase)
    return await service.get_tags(skip=skip, limit=limit, name=name)

# READ - Récupérer un tag spécifique
@router.get("/{tag_id}")
async def get_tag(
    tag_id: int,
    supabase: Client = Depends(get_supabase)
):
    """Récupérer un tag par ID"""
    service = SupabaseService(supabase)
    tag = await service.get_tag_by_id(tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    return tag

# READ - Récupérer toutes les halakhot associées à un tag
@router.get("/{tag_id}/halakhot")
async def get_tag_halakhot(
    tag_id: int,
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments à retourner"),
    supabase: Client = Depends(get_supabase)
):
    """Récupérer toutes les halakhot associées à un tag"""
    service = SupabaseService(supabase)
    
    # Vérifier que le tag existe
    tag = await service.get_tag_by_id(tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    # Récupérer les halakhot
    halakhot = await service.get_halakhot_by_tag(tag_id, skip=skip, limit=limit)
    return halakhot 