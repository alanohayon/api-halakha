from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class HalakhaBase(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)

class HalakhaCreate(HalakhaBase):
    pass

class HalakhaUpdate(BaseModel):
    question: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    answer: Optional[str] = None
    text_post: Optional[str] = None
    legend: Optional[str] = None
    status: Optional[ProcessingStatus] = None

class HalakhaResponse(HalakhaBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    answer: Optional[str] = None
    text_post: Optional[str] = None
    legend: Optional[str] = None
    status: ProcessingStatus
    created_at: datetime
    updated_at: Optional[datetime] = None