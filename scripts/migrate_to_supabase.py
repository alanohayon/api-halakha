import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import Base, engine
from app.models import answer, halakha_sources, halakha_tags, halakha_themes, halakha, question, source, tag, theme

async def create_tables():
    """Create all tables defined in your models"""
    try:
        async with engine.begin() as conn:
            # Correct way to create tables with AsyncEngine
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Tables created successfully")
        await engine.dispose()
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        print(f"Check your DATABASE_URL in .env file")
        raise

async def main():
    """Main function"""
    print("🚀 Creating tables in Supabase...")
    await create_tables()
    print("🎉 Migration completed!")

if __name__ == "__main__":
    asyncio.run(main())