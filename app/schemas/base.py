from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class BaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        arbitrary_types_allowed=True
    )

class TimestampedSchema(BaseSchema):
    created_at: datetime
    updated_at: Optional[datetime] = None
