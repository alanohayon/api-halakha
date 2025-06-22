#!/usr/bin/env python3
"""
Script de test simple pour vérifier la connexion à Supabase
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour importer les modules
sys.path.append(str(Path(__file__).parent.parent))

def test_supabase_connection():
    """Test de la connexion à Supabase avec configuration minimale"""
    try:
        print("🔍 Test de connexion à Supabase...")
        
        # Vérifier les variables d'environnement
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_anon_key:
            print("❌ Variables d'environnement manquantes")
            print("   Assurez-vous que SUPABASE_URL et SUPABASE_ANON_KEY sont définies")
            return False
        
        print(f"✅ Variables d'environnement trouvées")
        print(f"   URL: {supabase_url}")
        print(f"   Clé anonyme: {supabase_anon_key[:10]}...")
        
        # Tester la connexion avec le client Supabase
        try:
            from supabase import create_client, Client
            
            client: Client = create_client(supabase_url, supabase_anon_key)
            
            # Test simple - essayer de récupérer les halakhot
            print("📋 Test de récupération des halakhot...")
            response = client.table('halakhot').select('*').limit(1).execute()
            
            print(f"✅ Connexion réussie !")
            print(f"   {len(response.data)} halakhot trouvées")
            
            if response.data:
                print("\n📝 Première halakha :")
                first_halakha = response.data[0]
                for key, value in first_halakha.items():
                    if key != 'content' or len(str(value)) < 100:
                        print(f"  {key}: {value}")
            else:
                print("ℹ️  Aucune halakha trouvée (table vide)")
                
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la connexion : {e}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur générale : {e}")
        return False

if __name__ == "__main__":
    success = test_supabase_connection()
    if not success:
        print("\n🔧 Étapes de dépannage :")
        print("  1. Créez un fichier .env à la racine du projet")
        print("  2. Ajoutez SUPABASE_URL et SUPABASE_ANON_KEY")
        print("  3. Vérifiez que votre projet Supabase est actif")
        print("  4. Exécutez le script SQL pour créer les tables")
        sys.exit(1)
    else:
        print("\n🎉 Connexion Supabase réussie !") 