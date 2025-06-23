from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from app.api.v1.router import api_router

# Configuration de sécurité pour Swagger (optionnel)
security = HTTPBearer()

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Halakha API - Administration",
        version="1.0.0",
        description="""
        ## API pour la gestion des Halakhot
        
        ### 🔧 Fonctionnalités d'administration
        - Traitement des halakhot avec OpenAI
        - Génération de contenu pour les réseaux sociaux
        - Intégration Notion et Supabase
        
        ### 📝 Utilisation
        - Utilisez les endpoints `/halakha/analyze` et `/halakha/complete`
        - Tous les caractères Unicode (emojis, caractères spéciaux) sont supportés
        - Le texte est automatiquement nettoyé des caractères de contrôle
        
        ### 🔐 Authentification
        - Certains endpoints peuvent nécessiter une authentification
        """,
        routes=app.routes,
    )
    
    # Ajouter des informations de sécurité (si nécessaire)
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

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

# Remplacer le schéma OpenAPI par le personnalisé
app.openapi = custom_openapi

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



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

# Inclure les routes API v1
app.include_router(api_router, prefix="/api/v1")