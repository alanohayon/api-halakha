#!/usr/bin/env python3
"""
Script de test pour vérifier la connexion à Supabase
"""

import asyncio
import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour importer les modules de l'app
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.database import supabase, engine
from sqlalchemy import text

async def test_supabase_client():
    """Test de la connexion au client Supabase"""
    print("🔍 Test de la connexion au client Supabase...")
    
    try:
        # Test simple de la connexion en essayant d'accéder aux métadonnées
        # Cette approche fonctionne même sans tables spécifiques
        response = supabase.auth.get_user()
        print("✅ Connexion au client Supabase réussie")
        return True
    except Exception as e:
        print(f"❌ Erreur de connexion au client Supabase: {e}")
        return False

async def debug_database_connection():
    """Debug détaillé de la connexion"""
    print("🔍 Debug de la connexion à la base de données...")
    
    # Afficher l'URL (masquer le mot de passe)
    db_url = settings.database_url
    masked_url = db_url.replace(db_url.split('@')[0].split(':')[-1], '***')
    print(f"URL utilisée: {masked_url}")
    
    # Afficher les variables d'environnement
    print(f"SUPABASE_URL: {os.getenv('SUPABASE_URL')}")
    print(f"DATABASE_URL présent: {'DATABASE_URL' in os.environ}")
    
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connexion réussie - PostgreSQL: {version}")
            return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print(f"Type d'erreur: {type(e)}")
        return False

def check_environment_variables():
    """Vérification des variables d'environnement"""
    print("🔍 Vérification des variables d'environnement...")
    
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY',
        'SUPABASE_SERVICE_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith('your_'):
            missing_vars.append(var)
            print(f"❌ {var}: Non configuré ou valeur placeholder")
        else:
            print(f"✅ {var}: Configuré")
    
    if missing_vars:
        print(f"\n⚠️  Variables manquantes: {', '.join(missing_vars)}")
        return False
    
    return True

def main():
    """Fonction principale"""
    print("🚀 Test de connexion à Supabase\n")
    
    # Vérifier les variables d'environnement
    env_ok = check_environment_variables()
    
    if not env_ok:
        print("\n📝 Instructions:")
        print("1. Créez un fichier .env à la racine du projet")
        print("2. Ajoutez vos vraies valeurs Supabase:")
        print("   SUPABASE_URL=https://your-project-id.supabase.co")
        print("   SUPABASE_ANON_KEY=your_anon_key")
        print("   SUPABASE_SERVICE_KEY=your_service_key")
        print("3. Relancez ce script")
        return
    
    # Tests de connexion
    async def run_tests():
        supabase_ok = await test_supabase_client()
        db_ok = await debug_database_connection()
        
        print(f"\n📊 Résumé:")
        print(f"   Supabase Client: {'✅' if supabase_ok else '❌'}")
        print(f"   Database: {'✅' if db_ok else '❌'}")
        
        if supabase_ok and db_ok:
            print("\n🎉 Toutes les connexions fonctionnent correctement!")
        else:
            print("\n🔧 Des problèmes de connexion ont été détectés.")
    
    asyncio.run(run_tests())

if __name__ == "__main__":
    main() 