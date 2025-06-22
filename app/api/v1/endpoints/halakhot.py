from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import Client
from typing import List, Optional

from app.core.database import get_db, get_supabase
from app.services.supabase_service import SupabaseService
from app.services.halakha_service import HalakhaService
from app.schemas.halakha import HalakhaResponse, HalakhaCreate, HalakhaUpdate
from app.models.halakha import Halakha

router = APIRouter()

@router.post("/", response_model=HalakhaResponse, status_code=status.HTTP_201_CREATED)
async def create_halakha(
    halakha_data: HalakhaCreate,
    db: AsyncSession = Depends(get_db)
):
    """Créer une nouvelle halakha"""
    service = HalakhaService(db)
    return await service.create_halakha(halakha_data)

@router.get("/{halakha_id}", response_model=HalakhaResponse)
async def get_halakha(
    halakha_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Récupérer une halakha par ID"""
    service = HalakhaService(db)
    halakha = await service.get_halakha(halakha_id)
    if not halakha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Halakha not found"
        )
    return halakha

@router.get("/", response_model=List[HalakhaResponse])
async def list_halakhot(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Lister les halakhot avec pagination"""
    service = HalakhaService(db)
    return await service.list_halakhot(skip=skip, limit=limit)

@router.put("/{halakha_id}", response_model=HalakhaResponse)
async def update_halakha(
    halakha_id: int,
    halakha_data: HalakhaUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Mettre à jour une halakha"""
    service = HalakhaService(db)
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
    db: AsyncSession = Depends(get_db)
):
    """Supprimer une halakha"""
    service = HalakhaService(db)
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
    db: AsyncSession = Depends(get_db)
):
    """Traiter une halakha avec OpenAI et publier vers Notion"""
    # Implémentation du traitement
    pass

# Routes Supabase
@router.get("/supabase/list", response_model=List[dict])
async def get_halakhot_supabase(supabase: Client = Depends(get_supabase)):
    service = SupabaseService(supabase)
    return await service.get_halakhot()

@router.post("/supabase/create")
async def create_halakha_supabase(
    halakha_data: dict,
    supabase: Client = Depends(get_supabase)
):
    service = SupabaseService(supabase)
    return await service.create_halakha(halakha_data)

# Recherche avec filtres
@router.get("/search")
async def search_halakhot(
    category: Optional[str] = None,
    source: Optional[str] = None,
    supabase: Client = Depends(get_supabase)
):
    service = SupabaseService(supabase)
    return await service.search_halakhot(category, source)
