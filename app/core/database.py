from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker
from supabase import create_client, Client
from app.core.config import settings

# SQLAlchemy pour les opérations complexes
engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    future=True,
    pool_pre_ping=True,  # Importante pour Supabase
    pool_recycle=30     # Recycle les connexions toutes les 30 secondes
)
print(settings.database_url)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

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