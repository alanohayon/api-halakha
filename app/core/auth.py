"""
Module d'authentification pour l'API Halakha
"""
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import get_settings

# Configuration de sécurité pour l'authentification
security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Vérifie la clé API fournie dans l'en-tête Authorization
    
    Args:
        credentials: Credentials HTTP Bearer contenant la clé API
        
    Returns:
        str: La clé API si elle est valide
        
    Raises:
        HTTPException: Si la clé API est invalide ou manquante
    """
    settings = get_settings()
    
    if not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API manquante"
        )
    
    if credentials.credentials != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API invalide"
        )
    
    return credentials.credentials

# Dépendance optionnelle pour les endpoints qui peuvent être publics ou privés
async def verify_api_key_optional(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Vérifie la clé API de manière optionnelle
    
    Args:
        credentials: Credentials HTTP Bearer (optionnel)
        
    Returns:
        str|None: La clé API si fournie et valide, None sinon
    """
    try:
        return await verify_api_key(credentials)
    except HTTPException:
        return None