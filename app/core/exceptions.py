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