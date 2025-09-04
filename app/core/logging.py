import structlog
import logging
import sys
from .config import get_settings

# ============================================================================
# Processor pour masquer les clés sensibles dans les logs
# ============================================================================
def mask_secrets(logger, method_name, event_dict):
    secrets = [
        "supabase_service_key",
        "secret_key",
        "api_key",
        "notion_api_token",
        "openai_api_key"
    ]
    for key in secrets:
        if key in event_dict:
            event_dict[key] = "***MASKED***"
    return event_dict

# ============================================================================
# Configuration centrale du logging
# ============================================================================
def configure_logging():
    """Configure structured logging"""

    settings = get_settings()
    
    # Niveau de log dynamique selon l'environnement
    level = logging.DEBUG if not settings.is_production else getattr(logging, settings.log_level.upper(), logging.INFO)

    # Configuration de base logging standard
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level
    )

    # Choix du renderer selon settings
    renderer = structlog.processors.JSONRenderer() if settings.log_format == "json" else structlog.dev.ConsoleRenderer()

    # Configuration de structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            mask_secrets,
            renderer
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

# ============================================================================
# Instance logger global
# ============================================================================
logger = structlog.get_logger()
