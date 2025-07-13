from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from app.schemas.base import BaseResponse


class HalakhaNotionPost(BaseModel):
    """
    Schéma de la réponse au client après le traitement de la halakha.
    
    Attributes:
        status (str): Le statut du traitement
        message (str): Le message de réponse
        notion_page_url (str): L'URL de la page Notion créée
    """
    model_config = ConfigDict(from_attributes=True)
    
    status: str = Field(default="success", description="Statut du traitement")
    message: str = Field(default="La halakha a été traitée et publiée avec succès.", description="Message de confirmation")
    notion_page_url: str = Field(..., description="L'URL de la page Notion créée")
   
    
class HalakhaInputBrut(BaseModel):
    """
    Schéma pour recevoir le texte complet de la halakha à traiter (avec OpenAI).
    
    Attributes:
        content (str): Le texte complet de la halakha à traiter
    """
    content: str = Field(..., min_length=50, description="Contenu de la halakha à traiter")


class SourceItem(BaseModel):
    """
        Schéma pour les sources mentionnées dans la halakha.
        name: Le nom de la source.
        page: La page de la source.
        full_src: Le contenu complet de la source.
    """
    name: str
    page: Optional[str] = None
    full_src: Optional[str] = None


class HalakhaAnalyseOpenAi(BaseResponse):
    """
        Schéma pour les données extraites de la halakha avec OpenAI.
        title: Le titre de la halakha.
        difficulty_level: Le niveau de difficulté de la halakha.
        question: La question de la halakha.
        answer: La réponse de la halakha.
        content: Le contenu de la halakha.
        sources: Les sources mentionnées dans la halakha.
        themes: Les thèmes identifiés dans la halakha.
        tags: Les tags associés à la halakha.
    """
    title: str = Field(..., description="Titre de la halakha")
    difficulty_level: Optional[int] = Field(None, description="Niveau de difficulté de la halakha")
    question: str = Field(..., description="Question de la halakha")
    answer: str = Field(..., description="Réponse de la halakha")
    content: str = Field(..., description="Réponse extraite de la halakha")
    sources: Optional[List[SourceItem]] = Field(default_factory=list, description="Sources mentionnées")
    themes: Optional[List[str]] = Field(default_factory=list, description="Thèmes identifiés")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags associés")
    
    
class HalakhaPostLegendeOpenAi(BaseResponse):
    """
        Schéma pour les données extraites de la halakha avec OpenAI.
        title: Le titre de la halakha.
        difficulty_level: Le niveau de difficulté de la halakha.
        question: La question de la halakha.
        answer: La réponse de la halakha.
        content: Le contenu de la halakha.
        sources: Les sources mentionnées dans la halakha.
        themes: Les thèmes identifiés dans la halakha.
        tags: Les tags associés à la halakha.
        text_post: Le texte généré pour le post Instagram.
        legend: La légende générée pour le post.
    """
    title: str = Field(..., description="Titre de la halakha")
    difficulty_level: Optional[int] = Field(default=None, description="Niveau de difficulté de la halakha")
    question: str = Field(..., description="Question extraite de la halakha")
    answer: str = Field(..., description="Réponse extraite de la halakha")
    content: str = Field(..., description="Réponse extraite de la halakha")
    sources: Optional[List[SourceItem]] = Field(default_factory=list, description="Sources mentionnées")
    themes: Optional[List[str]] = Field(default_factory=list, description="Thèmes identifiés")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags associés")
    text_post: str = Field(..., description="Texte généré pour le post Instagram")
    legend: str = Field(..., description="Légende générée pour le post")
    


    
    