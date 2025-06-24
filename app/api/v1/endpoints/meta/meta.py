from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

router = APIRouter()

# Endpoint pour les informations de l'API
@router.get("/info")
async def get_api_info():
    """Récupérer les informations de l'API"""
    return {
        "name": "API Halakha",
        "version": "1.0.0",
        "description": "API pour la gestion des halakhot (lois religieuses juives)",
        "endpoints": {
            "halakhot": "/api/v1/halakhot",
            "sources": "/api/v1/halakhot/sources",
            "themes": "/api/v1/halakhot/themes", 
            "tags": "/api/v1/halakhot/tags",
            "processing": "/api/v1/processing",
            "openai": "/api/v1/openai",
            "notion": "/api/v1/notion",
            "whatsapp": "/api/v1/whatsapp"
        }
    }

# Endpoint pour les statistiques
@router.get("/stats")
async def get_api_stats():
    """Récupérer les statistiques de l'API"""
    # TODO: Implémenter les vraies statistiques depuis la base de données
    return {
        "total_halakhot": 0,
        "total_sources": 0,
        "total_themes": 0,
        "total_tags": 0,
        "api_version": "1.0.0",
        "status": "active"
    }

# Endpoint de santé
@router.get("/health")
async def health_check():
    """Vérifier l'état de santé de l'API"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "services": {
            "database": "connected",
            "openai": "available",
            "notion": "available"
        }
    } 