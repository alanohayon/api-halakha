from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class HalakhaQueryRequest(BaseModel):
    """Schéma de requête générique pour OpenAI"""
    text: str = Field(..., description="Texte à analyser par OpenAI")


class HalakhaAnalysisResponse(BaseModel):
    """Schéma de réponse pour l'analyse structurée d'une halakha"""
    title: str
    question: str
    answer: str
    tags: List[str]
    themes: List[str]
    sources: List[Dict[str, Any]]
    difficulty_level: int


class PostContentResponse(BaseModel):
    """Schéma de réponse pour le contenu Post"""
    post_text: str = Field(..., description="Texte optimisé pour le post Instagram")
    legende_text: str = Field(..., description="Légende optimisée pour les réseaux sociaux")


class FullHalakhaResponse(BaseModel):
    """Schéma de réponse complète incluant analyse halakha et contenu Instagram"""
    halakha_analysis: HalakhaAnalysisResponse = Field(..., description="Analyse structurée de la halakha")
    instagram_content: PostContentResponse = Field(..., description="Contenu optimisé pour Instagram")


class ErrorResponse(BaseModel):
    """Schéma standardisé pour les réponses d'erreur"""
    error_code: str = Field(..., description="Code d'erreur spécifique")
    message: str = Field(..., description="Message d'erreur lisible")
    details: Optional[Dict[str, Any]] = Field(None, description="Détails supplémentaires sur l'erreur")


