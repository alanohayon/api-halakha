from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client
from typing import List, Optional


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
    service: SupabaseServiceDep,
    title: Optional[str] = None,
    question: Optional[str] = None,
    answer: Optional[str] = None,
    difficulty_level: Optional[int] = None
):
    """
    Mise à jour partielle d'une halakha
    
    Permet de modifier uniquement les champs spécifiés sans affecter les autres.
    """
    
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
    service: SupabaseServiceDep
):
    """Supprimer une halakha"""
    success = await service.delete_halakha(halakha_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Halakha not found"
        )

# ============================================================================
# SOURCES - CRUD Operations
# ============================================================================

# READ - Lister toutes les sources
@router.get("/sources/", response_model=List[dict])
async def list_sources(
    service: SupabaseServiceDep,
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments à retourner"),
    name: Optional[str] = Query(None, description="Filtrer par nom de source")
):
    """Lister toutes les sources avec pagination et filtres"""
    return await service.get_sources(skip=skip, limit=limit, name=name)

# READ - Récupérer une source spécifique
@router.get("/sources/{source_id}")
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
@router.get("/sources/{source_id}/halakhot")
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

# ============================================================================
# TAGS - CRUD Operations
# ============================================================================

# READ - Lister tous les tags
@router.get("/tags/", response_model=List[dict])
async def list_tags(
    service: SupabaseServiceDep,
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments à retourner"),
    name: Optional[str] = Query(None, description="Filtrer par nom de tag")
):
    """Lister tous les tags avec pagination et filtres"""
    return await service.get_tags(skip=skip, limit=limit, name=name)

# READ - Récupérer un tag spécifique
@router.get("/tags/{tag_id}")
async def get_tag(
    tag_id: int,
    service: SupabaseServiceDep
):
    """Récupérer un tag par ID"""
    tag = await service.get_tag_by_id(tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    return tag

# READ - Récupérer toutes les halakhot associées à un tag
@router.get("/tags/{tag_id}/halakhot")
async def get_tag_halakhot(
    tag_id: int,
    service: SupabaseServiceDep,
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments à retourner")
):
    """Récupérer toutes les halakhot associées à un tag"""
    
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

# ============================================================================
# THEMES - CRUD Operations
# ============================================================================

# READ - Lister tous les thèmes
@router.get("/themes/", response_model=List[dict])
async def list_themes(
    service: SupabaseServiceDep,
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments à retourner"),
    name: Optional[str] = Query(None, description="Filtrer par nom de thème")
):
    """Lister tous les thèmes avec pagination et filtres"""
    return await service.get_themes(skip=skip, limit=limit, name=name)

# READ - Récupérer un thème spécifique
@router.get("/themes/{theme_id}")
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
@router.get("/themes/{theme_id}/halakhot")
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
