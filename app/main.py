from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router

# Créer l'application FastAPI
app = FastAPI(
    title="Halakha API",
    description="API pour la gestion des Halakhot",
    version="1.0.0",
    docs_url="/docs",  # URL de Swagger UI
    redoc_url="/redoc"  # URL de ReDoc
)

# Configuration CORS (optionnel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route de test simple
@app.get("/")
async def root():
    return {"message": "Bienvenue sur l'API Halakha"}

@app.get("/health")
async def health_check():
    return {"status": "OK", "message": "Service is running"}

# Inclure les routes API v1
app.include_router(api_router, prefix="/api/v1")