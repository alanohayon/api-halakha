#!/usr/bin/env python3
"""
Script de test pour vérifier la connexion à Supabase
"""

import asyncio
import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour importer les modules
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import get_supabase
from app.services.supabase_service import SupabaseService

async def test_supabase_connection():
    """Test de la connexion à Supabase"""
    try:
        print("🔍 Test de connexion à Supabase...")
        
        # Obtenir le client Supabase
        supabase_client = get_supabase()
        
        # Créer le service
        service = SupabaseService(supabase_client)
        
        # Test simple - récupérer les halakhot
        print("📋 Récupération des halakhot...")
        halakhot = await service.get_halakhot()
        
        print(f"✅ Connexion réussie ! {len(halakhot)} halakhot trouvées")
        
        # Afficher quelques détails si des données existent
        if halakhot:
            print("\n📝 Première halakha :")
            first_halakha = halakhot[0]
            for key, value in first_halakha.items():
                if key != 'content' or len(str(value)) < 100:  # Éviter d'afficher tout le contenu
                    print(f"  {key}: {value}")
            
            # Test de recherche par thème
            print("\n🔍 Test de recherche par thème...")
            if 'theme' in first_halakha and first_halakha['theme']:
                theme_results = await service.search_halakhot(theme=first_halakha['theme'])
                print(f"  Halakhot avec le thème '{first_halakha['theme']}': {len(theme_results)}")
            
            # Test de recherche par titre
            print("\n🔍 Test de recherche par titre...")
            if 'title' in first_halakha and first_halakha['title']:
                # Prendre les premiers mots du titre pour la recherche
                title_words = first_halakha['title'].split()[:2]
                search_title = ' '.join(title_words)
                title_results = await service.search_halakhot(title=search_title)
                print(f"  Halakhot avec '{search_title}' dans le titre: {len(title_results)}")
        else:
            print("ℹ️  Aucune halakha trouvée dans la base de données")
            
    except Exception as e:
        print(f"❌ Erreur de connexion : {e}")
        print("\n🔧 Vérifiez que :")
        print("  1. Le fichier .env existe avec les bonnes variables")
        print("  2. SUPABASE_URL et SUPABASE_ANON_KEY sont corrects")
        print("  3. Votre projet Supabase est actif")
        print("  4. La table 'halakhot' existe avec les colonnes : id, title, content, theme, source_id, question_id, answer_id")

if __name__ == "__main__":
    asyncio.run(test_supabase_connection()) 