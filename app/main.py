import time
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from app.core.logging import configure_logging
from app.core.exceptions import HalakhaAPIException
from app.api.v1.router import api_router
from app.core.config import settings

# Initialiser le logging structuré dès le démarrage
configure_logging()

# Configuration de sécurité pour Swagger (optionnel)
security = HTTPBearer()

# Créer l'application FastAPI avec configuration avancée
app = FastAPI(
    title="Halakha API - Administration",
    description="API d'administration pour la gestion des Halakhot",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
    openapi_url="/openapi.json",
    # Personnaliser Swagger UI
    swagger_ui_parameters={
        "defaultModelsExpandDepth": 2,
        "defaultModelExpandDepth": 2,
        "displayRequestDuration": True,
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True,
        "tryItOutEnabled": True,
    }
)

# Configuration CORS
# CORS est une mesure de sécurité qui permet de contrôler les requêtes HTTP entrantes.
# Ici, on permet aux origines suivantes d'accéder à l'API :
# - "http://localhost:3000" : L'application React
# - "http://localhost:8000" : L'API elle-même
# On permet également les méthodes HTTP suivantes :
# - GET : Récupération de données
# - POST : Création de ressources
# - PUT : Mise à jour de ressources
# - DELETE : Suppression de ressources
# - OPTIONS : Récupération des options de requête
# On permet également les headers suivants :
# - Authorization : Autorisation pour les requêtes authentifiées
# - Content-Type : Type de contenu de la requête
# - X-API-Key : Clé API pour les requêtes authentifiées
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,  # Depuis config
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

# Inclure les routes API v1
app.include_router(api_router, prefix="/api/v1")

@app.get("/", tags=["Health"])
async def root():
    """Point d'entrée principal de l'API"""
    return {"message": "Halakha API - Service actif", "status": "healthy"}

@app.get("/health", tags=["Health"])
async def health_check():
    """Vérification de santé de l'API pour Railway"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "service": "halakha-api"
    }

@app.get("/admin/info", tags=["Administration"])
async def admin_info():
    """Informations d'administration de l'API"""
    return {
        "api_name": "Halakha API",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "/api/v1/halakha/analyze",
            "complete": "/api/v1/halakha/complete",
            "process": "/api/v1/process-halakha"
        },
        "features": [
            "Traitement OpenAI",
            "Support Unicode/Emojis",
            "Nettoyage automatique du texte",
            "Intégration Notion",
            "Intégration Supabase"
        ]
    }


# Middleware de logging des requêtes
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log de la requête entrante
    logger = logging.getLogger(__name__)
    logger.info(f"Requête entrante: {request.method} {request.url}")
    
    # Traitement de la requête
    response = await call_next(request)
    
    # Calcul du temps de traitement
    process_time = time.time() - start_time
    
    # Log de la réponse
    logger.info(
        f"Réponse: {response.status_code} - "
        f"Temps: {process_time:.3f}s - "
        f"URL: {request.url}"
    )
    
    # Ajouter le temps de traitement dans les headers
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# Gestion globale des exceptions personnalisées
@app.exception_handler(HalakhaAPIException)
async def halakha_api_exception_handler(request: Request, exc: HalakhaAPIException):
    # Capture les erreurs métier personnalisées (validation, logique business)
    # Retourne un format JSON cohérent avec code d'erreur et détails
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": getattr(exc, "code", exc.__class__.__name__.upper()),
            "message": exc.message,
            "details": exc.details,
        },
    )

# Gestionnaire d'exceptions HTTP de FastAPI
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Capture les erreurs HTTP standard (404, 422, 500, etc.) de FastAPI
    # Uniformise le format de réponse JSON pour toutes les erreurs HTTP
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP_ERROR",
            "message": exc.detail,
            "status_code": exc.status_code,
        },
    )

# Gestionnaire d'exceptions génériques (catch-all)
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # Capture TOUTES les erreurs non gérées (crashes, bugs, erreurs système)
    # Log complet pour debugging + réponse sécurisée sans exposer les détails
    import logging
    logger = logging.getLogger(__name__)
    
    # Log l'erreur complète pour le debugging
    logger.error(f"Exception non gérée: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "Une erreur interne s'est produite",
            "details": "Contactez l'administrateur si le problème persiste",
        },
    )