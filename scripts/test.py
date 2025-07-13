import sys
import os
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.utils.image_utils import get_latest_image_with_clean_name
from app.services.supabase_service import SupabaseService
from app.core.database import get_supabase

async def main():
    print("=== Test d'upload d'image vers Supabase Storage ===")

    try:
        # 1. Test de récupération de la dernière image
        print("\n📁 Recherche de la dernière image dans Downloads...")
        latest_image, clean_filename = get_latest_image_with_clean_name()
        
        if not latest_image:
            print("❌ Aucune image trouvée dans le dossier Downloads")
            print("💡 Conseil : Ajoutez une image (PNG, JPG, etc.) dans votre dossier Downloads")
            return
        
        print(f"✅ Image trouvée : {latest_image}")
        print(f"📝 Nom nettoyé : {clean_filename}")
        
        # 2. Test d'upload vers Supabase
        print("\n🚀 Upload vers Supabase Storage...")
        supabase_client = get_supabase()
        supabase_service = SupabaseService(supabase_client)
        
        image_url = await supabase_service.upload_img_to_supabase(latest_image, clean_filename)
        
        if image_url:
            print(f"✅ Upload réussi !")
            print(f"🌐 URL publique : {image_url}")
            
            # 3. Test de format Notion (simulation)
            print("\n📋 Format pour propriété Notion 'image' :")
            notion_format = {
                "image": {
                    "files": [
                        {
                            "name": "Image",
                            "type": "external",
                            "external": {
                                "url": image_url
                            }
                        }
                    ]
                }
            }
            print(f"✅ {notion_format}")
            
        else:
            print("❌ Échec de l'upload vers Supabase")
            
    except Exception as e:
        print(f"❌ Erreur durant le test : {e}")
        import traceback
        traceback.print_exc()
        
        
def sanitize_json_text(text: str) -> str:
    """
    Nettoie un texte pour éviter les erreurs de décodage JSON
    en supprimant/échappant les caractères de contrôle invalides
    
    Args:
        text: Le texte à nettoyer
        
    Returns:
        str: Le texte nettoyé et sécurisé pour JSON
    """
    if not text:
        return ""
    
    # Remplacer les caractères de contrôle problématiques
    text = text.replace('\n', '\\n')  # Nouvelles lignes
    text = text.replace('\r', '\\r')  # Retours chariot
    text = text.replace('\t', '\\t')  # Tabulations
    text = text.replace('\b', '\\b')  # Backspace
    text = text.replace('\f', '\\f')  # Form feed
    
    # Échapper les guillemets
    text = text.replace('"', '\\"')
    text = text.replace("'", "\\'")
    
    # Supprimer les autres caractères de contrôle ASCII (0-31 sauf ceux déjà traités)
    import re
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Nettoyer les caractères Unicode problématiques
    text = text.encode('utf-8', errors='ignore').decode('utf-8')
    
    return text

async def test_text_sanitization():
    """Test de la fonction de nettoyage de texte"""
    print("\n🧹 Test de nettoyage de texte pour JSON...")
    
    # Texte avec caractères problématiques
    problematic_text = '''

Peut on utiliser un siphon à chantilly shabbat ?

C'est discuté:
•⁠  ⁠Certains permettent ( Orhot shabbat t1,15-28, Maasse ashabbat t1,13-6), d'autres interdisent ( Shmirat shabbat keilhata 11-14, Or hashabbat t16, p31-33).

•⁠  ⁠Meme selon les avis permissifs, il sera interdit d'écrire avec sur un gâteau ou dessiner des formes.
Les traits simples ou formes aléatoires sont cependant permis [ Piske tchouvot 321, note 330].   
   
    '''
    
    print("📝 Texte original :")
    print(repr(problematic_text))
    
    cleaned_text = sanitize_json_text(problematic_text)
    print("\n✅ Texte nettoyé :")
    print(repr(cleaned_text))
    
    # Test avec un JSON
    try:
        import json
        test_data = {
            "question": cleaned_text,
            "content": "Contenu de test"
        }
        json_string = json.dumps(test_data, ensure_ascii=False)
        print("\n🎯 Test JSON réussi !")
        print(f"JSON généré : {json_string}")
        
    except Exception as e:
        print(f"❌ Erreur JSON : {e}")

if __name__ == "__main__":
    asyncio.run(test_text_sanitization())
    
