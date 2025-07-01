import sys
import os
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.utils.image_utils import get_latest_image_path
from app.services.supabase_service import SupabaseService
from app.core.database import get_supabase

async def main():
    print("=== Test d'upload d'image vers Supabase Storage avec S3 ===")

    
    latest_image = get_latest_image_path()
    print(f"📁 Dernière image trouvée : {latest_image}")
    
    if latest_image:
        try:
            supabase_client = get_supabase()
            supabase_service = SupabaseService(supabase_client)
            
            print("🚀 Upload en cours...")
            url = await supabase_service.uploa_img_to_supabase(latest_image)
            
            if url:
                print(f"✅ Succès ! URL de l'image uploadée : {url}")
            else:
                print("❌ Échec de l'upload")
                
        except Exception as e:
            print(f"❌ Erreur lors de l'upload: {e}")
    else:
        print("❌ Aucune image trouvée dans le dossier Downloads")

if __name__ == "__main__":
    asyncio.run(main())