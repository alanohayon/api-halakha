import logging
import tempfile
from fastapi import APIRouter, Depends, File, HTTPException, BackgroundTasks, UploadFile, status, Form
from typing import List, Dict, Any, Optional
import uuid
from supabase import Client
import os
from datetime import datetime

# Imports core
from app.core.config import Settings, get_settings
from app.core.database import get_supabase

# Imports services
from app.services.processing_service import ProcessingService
from app.services.supabase_service import SupabaseService

# Imports schemas
from app.schemas.halakha import (
    HalakhaInputBrut,
    HalakhaNotionPost,
)

# Imports utilitaires
from app.utils.validators import sanitize_json_text

# Imports schemas additionnels
from app.schemas.halakha import HalakhaNotionPost

# ============================================================================
# DÉPENDANCES OPTIMISÉES POUR LA PRODUCTION
# ============================================================================

def get_supabase_service() -> SupabaseService:
    """Dépendance pour SupabaseService optimisée"""
    return SupabaseService()

def get_processing_service() -> ProcessingService:
    """Dépendance pour ProcessingService optimisée"""
    return ProcessingService()

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/halakhot/post", response_model=HalakhaNotionPost)
async def process_halakha_to_notion(
    content: str = Form(..., min_length=10, max_length=10000, description="Contenu de la halakha à traiter"),
    schedule_days: int = Form(
        default=0, 
        ge=0, 
        le=100, 
        description="Nombre de jours de report pour la programmation (0-100 uniquement)",
        example=7
    ),
    last_img: bool = Form(
        default=False,
        description="Si True, sauvegarde la dernière image dans Supabase puis dans notion"
    ),
    processing_service: ProcessingService = Depends(get_processing_service)
):
    """
    Traite une halakha avec OpenAI et la publie sur Notion.
    
    Args:
        content: Le texte complet de la halakha à analyser
        schedule_days: Nombre de jours à ajouter pour la date de publication (0-100)
        
    Returns:
        HalakhaNotionPost: Réponse contenant l'URL de la page Notion créée
        
    Raises:
        HTTPException: Si erreur lors du traitement
    """
    logger.info(f"🔄 Requête reçue pour traiter une halakha vers Notion")
    
    # Validation stricte du contenu
    if not content or not content.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Le contenu de la halakha ne peut pas être vide"
        )
    
    if schedule_days < 0 or schedule_days > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="schedule_days doit être entre 0 et 100 inclus"
        )
    
    logger.info(f"✅ Paramètres validés - Contenu: {len(content.strip())} caractères, Jours: {schedule_days}")
    
    try:
        # Nettoyer le contenu textuel
        sanitized_content = sanitize_json_text(content.strip())
        
        # Lancer le processus complet via ProcessingService (avec sauvegarde Supabase)
        notion_url = await processing_service.process_halakha_complete(
            halakha_content=sanitized_content,
            add_day_for_notion=schedule_days,
            last_image=last_img  # Save la derniere image dans supabase puis dans notion
        )
        
        logger.info(f"✅ Halakha traitée avec succès. URL Notion: {notion_url}")
        
        return HalakhaNotionPost(notion_page_url=notion_url)

    except Exception as e:
        logger.error(f"❌ Erreur lors du traitement halakha vers Notion: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Une erreur interne est survenue: {str(e)}"
        )
        
        
@router.post("/batch/halakhot", status_code=status.HTTP_201_CREATED)
async def process_halakhot_from_json(
    start_index: int = Form(
        default=0, 
        ge=0, 
        description="Index de départ dans le fichier JSON des halakhot (commence à 0)",
        example=0
    ),
    limit_halakhot: int = Form(
        default=10, 
        ge=1, 
        le=50, 
        description="Nombre maximum d'halakhot à traiter (1-50)",
        example=10
    ),
    schedule_days: int = Form(
        default=0, 
        ge=0, 
        le=365, 
        description="Nombre de jours de décalage pour la première halakha (0-365)",
        example=0
    ),
    max_retries: int = Form(
        default=3, 
        ge=0, 
        le=10, 
        description="Nombre maximum de tentatives par halakha (0-10)",
        example=3
    ),
    fail_fast_on_max_retries: bool = Form(
        default=True, 
        description="Si True, arrête le batch en cas d'échec définitif d'une halakha"
    ),
    processing_service: ProcessingService = Depends(get_processing_service)
):
    """
    🚀 Traite plusieurs halakhot en lot depuis le fichier JSON vers Notion
    
    Args:
        start_index: Index de départ dans le fichier JSON (0-based)
        limit_halakhot: Nombre maximum d'halakhot à traiter (1-50)
        schedule_days: Jours de décalage pour la première halakha (auto-incrémenté)
        max_retries: Nombre maximum de tentatives par halakha
        fail_fast_on_max_retries: Arrêt du batch si échec définitif
        
    Returns:
        Rapport détaillé du traitement en lot avec statistiques
        
    Raises:
        HTTPException: Si erreur de validation ou traitement
    """
    logger.info(f"🚀 Démarrage batch processing - Range: {start_index}-{start_index + limit_halakhot - 1}")
    logger.info(f"📋 Paramètres: schedule_days={schedule_days}, max_retries={max_retries}, fail_fast={fail_fast_on_max_retries}")
    
    # Validation des paramètres
    if limit_halakhot > 50:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="limit_halakhot ne peut pas dépasser 50 pour éviter les timeouts"
        )
    
    if schedule_days > 365:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="schedule_days ne peut pas dépasser 365 jours"
        )
    
    try:
        # Lancer le traitement en lot via ProcessingService
        batch_result = await processing_service.process_halakhot_from_json(
            start_index=start_index,
            schedule_days=schedule_days,
            limit_halakhot=limit_halakhot,
            max_retries=max_retries,
            fail_fast_on_max_retries=fail_fast_on_max_retries
        )
    # Déterminer le statut HTTP selon le résultat
        if batch_result["status"] == "failed_fast":
            # Fail-fast déclenché - retourner 207 Multi-Status
            status_code = status.HTTP_207_MULTI_STATUS
            message = f"Batch arrêté en fail-fast à la halakha #{batch_result.get('fail_fast_triggered_at_index', 'N/A')}"
        elif batch_result["failed_count"] > 0:
            # Succès partiel - retourner 207 Multi-Status  
            status_code = status.HTTP_207_MULTI_STATUS
            message = f"Batch complété avec {batch_result['failed_count']} échec(s) sur {batch_result['processed_count']}"
        else:
            # Succès complet - retourner 200 OK
            status_code = status.HTTP_200_OK
            message = f"Batch complété avec succès - {batch_result['success_count']} halakhot traitées"
        
        logger.info(f"✅ {message}")
        
        # Retourner la réponse enrichie
        return {
            "status": "success" if batch_result["failed_count"] == 0 else "partial_success",
            "message": message,
            "data": batch_result,
            "summary": {
                "total_processed": batch_result["processed_count"],
                "successful": batch_result["success_count"],
                "failed": batch_result["failed_count"],
                "skipped": batch_result.get("skipped_count", 0),
                "success_rate": batch_result["success_rate"],
                "range": f"{batch_result['start_index']}-{batch_result.get('end_index', 'N/A')}",
                "fail_fast_triggered": batch_result["status"] == "failed_fast"
            }
        }
        
    except RuntimeError as e:
        # Erreur fail-fast ou critique
        if "fail-fast" in str(e):
            logger.error(f"🚨 Fail-fast déclenché: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Traitement arrêté en mode fail-fast: {str(e)}"
            )
        else:
            logger.error(f"❌ Erreur critique du batch: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur critique lors du traitement: {str(e)}"
            )
    
    except ValueError as e:
        # Erreur de validation ou paramètres invalides
        logger.error(f"❌ Erreur de validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Paramètres invalides: {str(e)}"
        )
    
    except Exception as e:
        # Erreur inattendue
        logger.error(f"❌ Erreur inattendue lors du batch: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Une erreur inattendue est survenue: {str(e)}"
        )

@router.post("/images", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(..., description="Fichier image à uploader"),
    clean_filename: Optional[str] = Form(None, description="Nom de fichier personnalisé")
):
    """
    Upload une image vers Supabase Storage et retourne l'URL publique
    
    Args:
        file: Fichier image (.png, .jpg, .jpeg, .webp) à uploader
        clean_filename: Nom de fichier personnalisé (optionnel)
        
    Returns:
        dict: Réponse contenant l'URL de l'image uploadée
        
    Raises:
        HTTPException: Si erreur lors de l'upload ou format de fichier invalide
    """
    logger.info(f"Requête reçue pour upload d'image : {file.filename}")
    
    # Validation basique du fichier
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nom de fichier requis"
        )
    
    # Vérifier le type de fichier
    allowed_extensions = {".png", ".jpg", ".jpeg", ".webp"}
    file_extension = os.path.splitext(file.filename.lower())[1]
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Format non supporté. Formats acceptés : {', '.join(allowed_extensions)}"
        )
    
    # Vérifier le content-type
    allowed_content_types = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
    if file.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Type MIME non supporté : {file.content_type}"
        )
    
    # Vérifier la taille du fichier (max 10MB)
    file_content = await file.read()
    if len(file_content) > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Fichier trop volumineux (max 10MB)"
        )
    
    logger.info(f"Paramètres validés - Fichier: {file.filename}, Taille: {len(file_content)} bytes")
    
    try:
        # Instancier le service d'orchestration
        processing_service = ProcessingService()
        
        # Lancer l'upload via le service d'orchestration
        result = await processing_service.upload_image_to_storage(
            file_content=file_content,
            filename=file.filename,
            clean_filename=clean_filename
        )
        
        logger.info(f"✅ Image uploadée avec succès : {result['filename']}")
        
        return {
            "status": "success", 
            "message": "Image uploadée avec succès",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'upload d'image : {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Une erreur interne est survenue : {str(e)}"
        )

@router.get("/images/latest")
async def get_latest_image():
    """
    Récupère l'URL de la dernière image uploadée dans Supabase Storage
    
    Returns:
        dict: Réponse contenant l'URL de la dernière image
        
    Raises:
        HTTPException: Si aucune image trouvée ou erreur
    """
    logger.info("Requête reçue pour récupérer la dernière image")
    
    try:
        # Instancier le service d'orchestration 
        processing_service = ProcessingService()
        
        # Récupérer la dernière image via Supabase service
        image_url, name = await processing_service.supabase_service.get_last_img_supabase()
        
        if not image_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aucune image trouvée dans le storage "
            )

        
        return {
            "status": "success",
            "message": "Dernière image récupérée avec succès",
            "data": {
                "image_url": image_url,
                "name": name
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la dernière image : {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Une erreur interne est survenue : {str(e)}"
        )

