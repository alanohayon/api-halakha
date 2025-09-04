from fastapi import APIRouter, Depends, HTTPException, status, Form
import logging
from datetime import datetime
from typing import Dict, Any
import time

from app.services.openai_service import OpenAIService
from app.schemas.openai import (
    FullHalakhaResponse,
    HalakhaAnalysisResponse,
    PostContentResponse,
    ErrorResponse
)
from openai import OpenAIError, RateLimitError, APITimeoutError, APIConnectionError

from app.api.deps import OpenAIServiceDep

router = APIRouter()
logger = logging.getLogger(__name__)


# Endpoint pour analyser du texte
@router.post("/query_halakha", response_model=HalakhaAnalysisResponse)
async def query_halakha(
    service: OpenAIServiceDep,  # ✅ Paramètre sans défaut en premier
    text: str = Form(..., description="Texte à analyser par OpenAI")
):
    """
    Analyse un texte halakhique avec OpenAI GPT pour le structurer.
    
    **Fonctionnalités :**
    - Analyse sémantique du contenu avec IA
    - Extraction automatique des concepts clés
    - Génération de résumé et de tags pertinents
    - Structuration des données pour la base de données
    - Support complet des caractères Unicode (hébreu, emojis)
    
    **Paramètres :**
    - `text` : Texte brut de la halakha à analyser
    
    **Retour :**
    - Données structurées de la halakha
    - Titre généré automatiquement
    - Résumé et tags extraits
    - Métadonnées d'analyse
    
    **Utilisation :**
    - Préprocessing avant sauvegarde en base
    - Enrichissement de contenu existant
    - Classification automatique des halakhot
    """
    try:    
        result = await service.queries_halakha(text)
        return result
    except RateLimitError as e:
        logger.warning(f"Limite de taux OpenAI atteinte: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Erreur lors de la génération du contenu du text ou post: {str(e)}"
        )
    except (OpenAIError, APITimeoutError, APIConnectionError) as e:
        logger.error(f"Erreur OpenAI: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Erreur lors de la génération du contenu du text ou post: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Erreur interne inattendue: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur interne s'est produite."
        )
        
# Endpoint pour analyser du texte
@router.post("/full_query_halakha", response_model=FullHalakhaResponse)
async def full_query_halakha(
    service: OpenAIServiceDep,  # ✅ Paramètre sans défaut en premier
    text: str = Form(..., description="Texte à analyser par OpenAI")
):
    """
    Endpoint pour analyser une halakha avec OpenAI et générer le contenu Instagram complet.
    text: Le texte à analyser.
    Retourne une réponse avec les données de la halakha strcuturées, le texte du post Instagram et la légende.
    """
    
    try:
        # 1. Analyse de la halakha
        halakha_result = await service.queries_halakha(text)

        # 2. Génération du contenu Post
        post_result = await service.queries_post_legende(text, halakha_result["answer"])
        
    except RateLimitError as e:
        logger.warning(f"Limite de taux OpenAI atteinte: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Erreur lors de la génération du contenu du text ou post: {str(e)}"
        )
    except (OpenAIError, APITimeoutError, APIConnectionError) as e:
        logger.error(f"Erreur OpenAI: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Erreur lors de la génération du contenu du text ou post: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Erreur interne inattendue: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Erreur lors de la génération du contenu du text ou post: {str(e)}"
        )

    try:
        # 3. Construction de la réponse
        response = FullHalakhaResponse(
                halakha_analysis=halakha_result,
                instagram_content=post_result
            )

        return response
    except Exception as e:
        logger.error(f"Erreur interne inattendue: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur interne s'est produite."
        )
    
            
            
            
            
            