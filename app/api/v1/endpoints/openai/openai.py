from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from app.services.openai_service import OpenAIService
from app.schemas.openai import OpenAIRequest

router = APIRouter()

# Endpoint pour générer du contenu avec OpenAI
@router.post("/generate")
async def generate_content(
    request: OpenAIRequest
):
    """Générer du contenu avec OpenAI"""
    service = OpenAIService()
    try:
        result = await service.generate_response(request.prompt, request.model)
        return {"content": result, "status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération: {str(e)}"
        )

# Endpoint pour analyser du texte
@router.post("/analyze")
async def analyze_text(
    text: str
):
    """Analyser un texte avec OpenAI"""
    service = OpenAIService()
    try:
        result = await service.analyze_text(text)
        return {"analysis": result, "status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse: {str(e)}"
        ) 