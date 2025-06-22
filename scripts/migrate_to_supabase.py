import asyncio
from app.core.database import AsyncSessionLocal, supabase
from app.models.halakha import Halakha
from sqlalchemy import select

async def migrate_to_supabase():
    """Migrer les données locales vers Supabase"""
    async with AsyncSessionLocal() as session:
        # Récupérer les données locales
        result = await session.execute(select(Halakha))
        halakhot = result.scalars().all()
        
        print(f"Migration de {len(halakhot)} halakhot vers Supabase...")
        
        for halakha in halakhot:
            data = {
                "title": halakha.title,
                "content": halakha.content,
                "source": halakha.source,
                "category": halakha.category,
                "reference": halakha.reference,
                "processed": halakha.processed
            }
            
            try:
                response = supabase.table('halakhot').insert(data).execute()
                print(f"✓ Migré: {halakha.title}")
            except Exception as e:
                print(f"✗ Erreur pour {halakha.title}: {e}")

if __name__ == "__main__":
    asyncio.run(migrate_to_supabase())
