from fastapi import HTTPException, status
from typing import Optional, Dict, Any

class HalakhaAPIException(Exception):
    """Base exception for Halakha API"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class HalakhaNotFoundError(HalakhaAPIException):
    """Raised when a halakha is not found"""
    pass

class OpenAIServiceError(HalakhaAPIException):
    """Raised when OpenAI service encounters an error"""
    pass

class NotionServiceError(HalakhaAPIException):
    """Raised when Notion service encounters an error"""
    pass

class DatabaseError(HalakhaAPIException):
    """Raised when database operations fail"""
    pass

class ValidationError(HalakhaAPIException):
    """Raised when data validation fails"""
    pass

class BaseAPIException(HTTPException):
    """Base exception pour toutes les exceptions de l'API"""
    pass

class SupabaseServiceException(BaseAPIException):
    """Exception de base pour les erreurs du service Supabase"""
    def __init__(self, detail: str, status_code: int = 500):
        super().__init__(status_code=status_code, detail=detail)

class SupabaseAuthException(SupabaseServiceException):
    """Exception pour les erreurs d'authentification Supabase"""
    def __init__(self, detail: str, error_code: Optional[str] = None):
        self.error_code = error_code
        super().__init__(detail=detail, status_code=401)

class SupabaseDataException(SupabaseServiceException):
    """Exception pour les erreurs de données Supabase"""
    def __init__(self, detail: str, status_code: int = 422):
        super().__init__(detail=detail, status_code=status_code)

class SupabaseNotFoundException(SupabaseServiceException):
    """Exception pour les ressources non trouvées"""
    def __init__(self, resource: str, identifier: Any):
        detail = f"{resource} avec l'identifiant '{identifier}' n'a pas été trouvé"
        super().__init__(detail=detail, status_code=404)

class SupabaseConflictException(SupabaseServiceException):
    """Exception pour les conflits de données (contraintes UNIQUE, etc.)"""
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=409)

class SupabaseRateLimitException(SupabaseServiceException):
    """Exception pour les limitations de taux"""
    def __init__(self, detail: str = "Trop de requêtes. Veuillez réessayer plus tard."):
        super().__init__(detail=detail, status_code=429)

class SupabaseValidationException(SupabaseServiceException):
    """Exception pour les erreurs de validation"""
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=422)

# Mapping des codes d'erreur Supabase vers nos exceptions
SUPABASE_ERROR_MAPPING = {
    # Erreurs d'authentification
    'invalid_credentials': SupabaseAuthException,
    'user_not_found': SupabaseAuthException,
    'email_exists': SupabaseConflictException,
    'captcha_failed': SupabaseAuthException,
    'weak_password': SupabaseValidationException,
    'email_rate_limit_exceeded': SupabaseRateLimitException,
    
    # Erreurs de données
    'conflict': SupabaseConflictException,
    'validation_failed': SupabaseValidationException,
    'not_found': SupabaseNotFoundException,
    
    # Erreurs de serveur
    'internal_server_error': SupabaseServiceException,
    'service_unavailable': SupabaseServiceException,
}

def map_supabase_error(error_data: Dict, operation_context: str = "") -> SupabaseServiceException:
    """
    Mappe une erreur Supabase vers une exception appropriée
    
    Args:
        error_data: Données d'erreur de Supabase (avec code, message, etc.)
        operation_context: Contexte de l'opération pour des messages plus clairs
        
    Returns:
        SupabaseServiceException: Exception appropriée
    """
    error_code = error_data.get('code', '')
    error_message = error_data.get('message', 'Erreur Supabase inconnue')
    
    # Ajout du contexte au message
    if operation_context:
        error_message = f"{operation_context}: {error_message}"
    
    # Mapping par code d'erreur
    if error_code in SUPABASE_ERROR_MAPPING:
        exception_class = SUPABASE_ERROR_MAPPING[error_code]
        if exception_class == SupabaseAuthException:
            return exception_class(error_message, error_code)
        return exception_class(error_message)
    
    # Mapping par codes HTTP status si disponible
    status_code = error_data.get('status', 500)
    if status_code == 403:
        return SupabaseServiceException(f"Accès interdit: {error_message}", 403)
    elif status_code == 404:
        return SupabaseNotFoundException("Ressource", "inconnue")
    elif status_code == 409:
        return SupabaseConflictException(error_message)
    elif status_code == 422:
        return SupabaseValidationException(error_message)
    elif status_code == 429:
        return SupabaseRateLimitException(error_message)
    
    # Exception générique par défaut
    return SupabaseServiceException(error_message, status_code)

# Exception handlers
def create_http_exception(
    status_code: int,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> HTTPException:
    """Create a standardized HTTP exception"""
    return HTTPException(
        status_code=status_code,
        detail={
            "message": message,
            "details": details or {}
        }
    )

def halakha_not_found_exception(halakha_id: int) -> HTTPException:
    return create_http_exception(
        status_code=status.HTTP_404_NOT_FOUND,
        message=f"Halakha with ID {halakha_id} not found"
    )

def openai_service_exception(error: str) -> HTTPException:
    return create_http_exception(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        message="OpenAI service is currently unavailable",
        details={"error": error}
    )

def notion_service_exception(error: str) -> HTTPException:
    return create_http_exception(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        message="Notion service is currently unavailable",
        details={"error": error}
    )