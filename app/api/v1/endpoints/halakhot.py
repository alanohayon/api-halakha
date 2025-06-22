from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from typing import List, Optional

from app.core.database import get_supabase
from app.services.supabase_service import SupabaseService

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_halakha(
    halakha_data: dict,
    supabase: Client = Depends(get_supabase)
):
    """Créer une nouvelle halakha"""
    service = SupabaseService(supabase)
    return await service.create_halakha(halakha_data)

@router.get("/{halakha_id}")
async def get_halakha(
    halakha_id: int,
    supabase: Client = Depends(get_supabase)
):
    """Récupérer une halakha par ID"""
    service = SupabaseService(supabase)
    halakha = await service.get_halakha_by_id(halakha_id)
    if not halakha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Halakha not found"
        )
    return halakha

@router.get("/", response_model=List[dict])
async def list_halakhot(
    skip: int = 0,
    limit: int = 100,
    supabase: Client = Depends(get_supabase)
):
    """Lister les halakhot avec pagination"""
    service = SupabaseService(supabase)
    return await service.get_halakhot(skip=skip, limit=limit)

@router.put("/{halakha_id}")
async def update_halakha(
    halakha_id: int,
    halakha_data: dict,
    supabase: Client = Depends(get_supabase)
):
    """Mettre à jour une halakha"""
    service = SupabaseService(supabase)
    updated_halakha = await service.update_halakha(halakha_id, halakha_data)
    if not updated_halakha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Halakha not found"
        )
    return updated_halakha

@router.delete("/{halakha_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_halakha(
    halakha_id: int,
    supabase: Client = Depends(get_supabase)
):
    """Supprimer une halakha"""
    service = SupabaseService(supabase)
    success = await service.delete_halakha(halakha_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Halakha not found"
        )

@router.post("/{halakha_id}/process")
async def process_halakha(
    halakha_id: int,
    schedule_days: int = 0,
    supabase: Client = Depends(get_supabase)
):
    """Traiter une halakha avec OpenAI et publier vers Notion"""
    # Implémentation du traitement
    pass

# Recherche avec filtres
@router.get("/search")
async def search_halakhot(
    category: Optional[str] = None,
    source: Optional[str] = None,
    supabase: Client = Depends(get_supabase)
):
    service = SupabaseService(supabase)
    return await service.search_halakhot(category, source)
