from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# Route d'exemple pour les halakhot
@app.get("/api/v1/halakhot")
async def get_halakhot():
    return {
        "halakhot": [
            {
                "id": 1,
                "title": "Exemple de Halakha",
                "content": "Contenu d'exemple",
                "source": "Source d'exemple"
            }
        ]
    }