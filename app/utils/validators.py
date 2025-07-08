import re
from typing import Optional, Any, Dict


def sanitize_json_text(text: str) -> str:
    """
    Nettoie un texte pour éviter les erreurs de décodage JSON
    en supprimant/échappant les caractères de contrôle invalides
    
    Args:
        text: Le texte à nettoyer
        
    Returns:
        str: Le texte nettoyé et sécurisé pour JSON
    """
    if not text:
        return ""
    
    # Supprimer les autres caractères de contrôle ASCII (0-31 sauf \n, \r, \t)
    # qui peuvent causer des erreurs JSON
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Nettoyer les caractères Unicode problématiques
    text = text.encode('utf-8', errors='ignore').decode('utf-8')
    
    return text


def sanitize_text_fields(data: Dict[str, Any], text_fields: list) -> Dict[str, Any]:
    """
    Nettoie les champs textuels spécifiés dans un dictionnaire de données
    
    Args:
        data: Dictionnaire contenant les données à nettoyer
        text_fields: Liste des noms de champs à nettoyer
        
    Returns:
        dict: Les données avec les champs textuels nettoyés
    """
    if not isinstance(data, dict):
        return data
    
    for field in text_fields:
        if field in data and isinstance(data[field], str):
            data[field] = sanitize_json_text(data[field])
    
    return data


def validate_and_sanitize_request(request_data: Any, text_fields: list) -> Any:
    """
    Valide et nettoie les données d'une requête
    
    Args:
        request_data: Données de la requête (peut être un dict, une liste, ou un objet Pydantic)
        text_fields: Liste des champs textuels à nettoyer
        
    Returns:
        Les données nettoyées
    """
    # Si c'est un modèle Pydantic, convertir en dict
    if hasattr(request_data, 'model_dump'):
        data = request_data.model_dump()
    elif hasattr(request_data, 'dict'):
        data = request_data.dict()
    else:
        data = request_data
    
    # Nettoyer les champs textuels
    if isinstance(data, dict):
        data = sanitize_text_fields(data, text_fields)
    elif isinstance(data, list):
        data = [sanitize_text_fields(item, text_fields) if isinstance(item, dict) else item for item in data]
    
    return data
