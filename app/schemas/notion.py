from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class NotionPageRequest(BaseModel):
    title: str = Field(..., description="Titre de la page")
    content: Optional[str] = Field(default=None, description="Contenu de la page")
    properties: Optional[Dict[str, Any]] = Field(default=None, description="Propriétés de la page")


class NotionPageResponse(BaseModel):
    id: str
    url: str
    title: str
    created_time: str
    last_edited_time: str


class NotionDatabaseRequest(BaseModel):
    parent_id: str = Field(..., description="ID de la page parent")
    title: str = Field(..., description="Titre de la base de données")
    properties: Dict[str, Any] = Field(..., description="Schéma des propriétés")


class NotionSyncRequest(BaseModel):
    database_id: str = Field(..., description="ID de la base de données Notion")
    halakha_ids: List[int] = Field(..., description="Liste des IDs des halakhot à synchroniser")
