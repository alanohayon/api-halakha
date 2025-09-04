#!/usr/bin/env python3
"""
Script de vérification de la sécurité CORS
Vérifie que la configuration CORS est sécurisée pour la production
"""

import os
import sys
import json
from pathlib import Path

# Ajouter le répertoire parent au path pour importer les modules
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import get_settings

def check_cors_security():
    """Vérifie la configuration CORS pour la sécurité"""
    print("🔍 Vérification de la sécurité CORS...")
    
    try:
        settings = get_settings()
        
        # Vérifier les origines CORS
        cors_origins = settings.backend_cors_origins
        print(f"📋 Origines CORS configurées: {cors_origins}")
        
        # Vérifications de sécurité
        security_issues = []
        
        # 1. Vérifier qu'on n'utilise pas "*"
        if "*" in cors_origins:
            security_issues.append("❌ CRITIQUE: '*' trouvé dans les origines CORS")
        else:
            print("✅ Aucune origine wildcard '*' détectée")
        
        # 2. Vérifier que les origines sont des URLs valides
        for origin in cors_origins:
            if not origin.startswith(("http://", "https://")):
                security_issues.append(f"❌ Origine invalide: {origin}")
            elif origin.startswith("http://") and "localhost" not in origin:
                security_issues.append(f"⚠️  HTTP non sécurisé en production: {origin}")
        
        # 3. Vérifier la configuration CORS complète
        cors_config = settings.cors_config
        print(f"📋 Configuration CORS complète: {json.dumps(cors_config, indent=2)}")
        
        # 4. Vérifier les headers autorisés
        allowed_headers = cors_config.get("allow_headers", [])
        if "*" in allowed_headers:
            security_issues.append("❌ CRITIQUE: Headers wildcard '*' autorisés")
        else:
            print("✅ Headers spécifiques autorisés")
        
        # 5. Vérifier les méthodes autorisées
        allowed_methods = cors_config.get("allow_methods", [])
        if "*" in allowed_methods:
            security_issues.append("❌ CRITIQUE: Méthodes wildcard '*' autorisées")
        else:
            print("✅ Méthodes spécifiques autorisées")
        
        # Résultat
        if security_issues:
            print("\n🚨 PROBLÈMES DE SÉCURITÉ DÉTECTÉS:")
            for issue in security_issues:
                print(f"  {issue}")
            return False
        else:
            print("\n✅ CONFIGURATION CORS SÉCURISÉE")
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False

def check_environment_variables():
    """Vérifie les variables d'environnement critiques"""
    print("\n🔍 Vérification des variables d'environnement...")
    
    critical_vars = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY", 
        "SUPABASE_SERVICE_KEY",
        "DATABASE_URL"
    ]
    
    missing_vars = []
    for var in critical_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Variables manquantes: {', '.join(missing_vars)}")
        print("💡 Créez un fichier .env basé sur env.example")
        return False
    else:
        print("✅ Variables d'environnement critiques présentes")
        return True

def main():
    """Fonction principale de vérification"""
    print("=" * 60)
    print("🔒 VÉRIFICATION DE SÉCURITÉ CORS - HALAKHA API")
    print("=" * 60)
    
    cors_ok = check_cors_security()
    env_ok = check_environment_variables()
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DE LA VÉRIFICATION")
    print("=" * 60)
    print(f"CORS Sécurisé: {'✅' if cors_ok else '❌'}")
    print(f"Variables d'environnement: {'✅' if env_ok else '❌'}")
    
    if cors_ok and env_ok:
        print("\n🎉 PRÊT POUR LA PRODUCTION!")
        print("✅ Le premier point de la checklist de déploiement est validé")
        return 0
    else:
        print("\n⚠️  CORRECTIONS NÉCESSAIRES AVANT DÉPLOIEMENT")
        return 1

if __name__ == "__main__":
    sys.exit(main())