from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class BaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        # Add these for better Unicode support
        str_strip_whitespace=False,  # Don't auto-strip, let your clean function handle it
        validate_default=True,
        extra='forbid'  # Prevent extra fields
    )

class TimestampedSchema(BaseSchema):
    created_at: datetime
    updated_at: Optional[datetime] = None


class BaseResponse(BaseSchema):
    """Classe de base pour les réponses API"""
    success: bool = True
    message: Optional[str] = None
