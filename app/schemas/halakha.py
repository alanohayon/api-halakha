from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum

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