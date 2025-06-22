from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from supabase import create_client, Client
from app.core.config import settings

# SQLAlchemy pour les opérations complexes
engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    future=True,
    pool_pre_ping=True,  # Importante pour Supabase
    pool_recycle=300     # Recycle les connexions toutes les 5 minutes
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

# Client Supabase pour les opérations simples et auth
supabase: Client = create_client(settings.supabase_url, settings.supabase_anon_key)

# Dependency pour FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def get_supabase():
    return supabase