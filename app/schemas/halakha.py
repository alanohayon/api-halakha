from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum
from app.schemas.base import BaseResponse

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class HalakhaTextInput(BaseModel):
    halakha_content: str = Field(..., min_length=50, description="Le texte complet de la halakha à traiter.")
    schedule_days: int = Field(0, description="Nombre de jours à ajouter pour la date de publication sur Notion.")

class HalakhaProcessResponse(BaseModel):
    status: str = "success"
    message: str = "La halakha a été traitée et publiée avec succès."
    notion_page_url: str 

class HalakhaBase(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)

class HalakhaCreate(HalakhaBase):
    pass


class HalakhaResponse(HalakhaBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    answer: Optional[str] = None
    text_post: Optional[str] = None
    legend: Optional[str] = None
    status: ProcessingStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

class ProcessHalakhaRequest(BaseModel):
    content: str = Field(..., min_length=1, description="Contenu de la halakha à traiter")


class SourceItem(BaseModel):
    name: str
    page: Optional[str] = None
    full_src: Optional[str] = None


class HalakhaCompleteInput(BaseModel):
    """Schéma pour recevoir une halakha complète avec toutes ses données"""
    title: str = Field(..., description="Titre de la halakha")
    difficulty_level: Optional[int] = Field(None, description="Niveau de difficulté de la halakha")
    question: str = Field(..., description="Question de la halakha")
    answer: str = Field(..., description="Réponse de la halakha")
    sources: Optional[List[SourceItem]] = Field(default_factory=list, description="Sources mentionnées")
    themes: Optional[List[str]] = Field(default_factory=list, description="Thèmes identifiés")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags associés")
    
    
class ProcessHalakhaResponse(BaseResponse):
    title: Optional[str] = Field(default=None, description="Titre de la halakha")
    difficulty_level: Optional[int] = Field(default=None, description="Niveau de difficulté de la halakha")
    question: str = Field(..., description="Question extraite de la halakha")
    answer: str = Field(..., description="Réponse extraite de la halakha")
    sources: Optional[List[SourceItem]] = Field(default=None, description="Sources mentionnées")    
    themes: Optional[List[str]] = Field(default=None, description="Thèmes identifiés")
    tags: Optional[List[str]] = Field(default=None, description="Tags associés")

    
class ProcessCompleteHalakhaResponse(BaseResponse):
    title: Optional[str] = Field(default=None, description="Titre de la halakha")
    difficulty_level: Optional[int] = Field(default=None, description="Niveau de difficulté de la halakha")
    question: str = Field(..., description="Question extraite de la halakha")
    answer: str = Field(..., description="Réponse extraite de la halakha")
    sources: Optional[List[SourceItem]] = Field(default=None, description="Sources mentionnées")    
    themes: Optional[List[str]] = Field(default=None, description="Thèmes identifiés")
    tags: Optional[List[str]] = Field(default=None, description="Tags associés")
    text_post: str = Field(..., description="Texte généré pour le post Instagram")
    legend: str = Field(..., description="Légende générée pour le post")
    
    