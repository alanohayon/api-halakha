from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client
from typing import List, Optional

from app.core.database import get_supabase
from app.services.supabase_service import SupabaseService
from app.api.deps import SupabaseServiceDep
from app.schemas.halakha import HalakhaAnalyseOpenAi

router = APIRouter()

# CREATE - Créer une nouvelle halakha
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_halakha(
    halakha_data: HalakhaAnalyseOpenAi,
    service_supabase: SupabaseServiceDep
):
    """Créer une nouvelle halakha avec toutes ses données structurées"""
    # Convertir le modèle Pydantic en dictionnaire pour le service
    halakha_dict = halakha_data.model_dump()
    return await service_supabase.create_halakha(halakha_dict)

# READ - Lister toutes les halakhot avec pagination et recherche
@router.get("/", response_model=List[dict])
async def list_halakhot(
    service: SupabaseServiceDep,
    page: int = Query(1, ge=1, description="Numéro de la page"),
    limit: int = Query(20, ge=1, le=100, description="Nombre d'éléments par page"),
    search: Optional[str] = Query(None, description="Recherche dans le titre et le contenu"),
    theme: Optional[str] = Query(None, description="Filtrer par thème"),
    tag: Optional[str] = Query(None, description="Filtrer par tag"),
    author: Optional[str] = Query(None, description="Filtrer par auteur/source"),
    difficulty_level: Optional[int] = Query(None, ge=1, le=5, description="Filtrer par niveau de difficulté")
):
    """
    Lister les halakhot avec pagination et filtres avancés
    
    Exemples d'utilisation :
    - GET /halakhot?page=1&limit=20
    - GET /halakhot?search=pourim
    - GET /halakhot?theme=fêtes&tag=vin
    - GET /halakhot?author=Choulhan%20Aroukh
    """
    skip = (page - 1) * limit
    
    return await service.search_halakhot(
        search=search,
        theme=theme,
        tag=tag,
        author=author,
        difficulty_level=difficulty_level,
        skip=skip,
        limit=limit
    )

# READ - Récupérer une halakha spécifique
@router.get("/{halakha_id}")
async def get_halakha(
    halakha_id: int,
    service: SupabaseServiceDep
):
    """Récupérer une halakha par ID"""
    halakha = await service.get_halakha_by_id(halakha_id)
    if not halakha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Halakha not found"
        )
    return halakha

# UPDATE - Remplacer complètement une halakha
@router.put("/{halakha_id}")
async def replace_halakha(
    halakha_id: int,
    halakha_data: HalakhaAnalyseOpenAi,
    service_supabase: SupabaseServiceDep
):
    """Remplacer complètement une halakha existante"""
    
    # Vérifier que la halakha existe
    existing_halakha = await service_supabase.get_halakha_by_id(halakha_id)
    if not existing_halakha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Halakha not found"
        )
    
    # Remplacer complètement
    halakha_dict = halakha_data.model_dump()
    updated_halakha = await service_supabase.replace_halakha(halakha_id, halakha_dict)
    
    if not updated_halakha:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to replace halakha"
        )
    
    return updated_halakha

# PATCH - Mise à jour partielle d'une halakha
@router.patch("/{halakha_id}")
async def update_halakha_partial(
    halakha_id: int,
    title: Optional[str] = None,
    question: Optional[str] = None,
    answer: Optional[str] = None,
    difficulty_level: Optional[int] = None,
    supabase: Client = Depends(get_supabase)
):
    """
    Mise à jour partielle d'une halakha
    
    Permet de modifier uniquement les champs spécifiés sans affecter les autres.
    """
    service = SupabaseService(supabase)
    
    # Vérifier que la halakha existe
    existing_halakha = await service.get_halakha_by_id(halakha_id)
    if not existing_halakha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Halakha not found"
        )
    
    # Construire le dictionnaire des mises à jour (seulement les champs non-null)
    updates = {}
    if title is not None:
        updates['title'] = title
    if question is not None:
        updates['question'] = question
    if answer is not None:
        updates['answer'] = answer
        updates['content'] = answer  # Synchroniser content avec answer
    if difficulty_level is not None:
        updates['difficulty_level'] = difficulty_level
    
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided for update"
        )
    
    # Effectuer la mise à jour partielle
    updated_halakha = await service.update_halakha_partial(halakha_id, updates)
    
    if not updated_halakha:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update halakha"
        )
    
    return updated_halakha

# DELETE - Supprimer une halakha
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

# SUB-RESOURCE - Récupérer les sources d'une halakha
@router.get("/{halakha_id}/sources")
async def get_halakha_sources(
    halakha_id: int,
    supabase: Client = Depends(get_supabase)
):
    """Récupérer toutes les sources associées à une halakha"""
    service = SupabaseService(supabase)
    
    # Vérifier que la halakha existe
    halakha = await service.get_halakha_by_id(halakha_id)
    if not halakha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Halakha not found"
        )
    
    # Récupérer les sources
    sources = await service.get_halakha_sources(halakha_id)
    return sources
