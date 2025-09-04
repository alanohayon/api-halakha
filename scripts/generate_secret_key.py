#!/usr/bin/env python3
"""
Script de génération de clé secrète sécurisée
Génère une clé secrète cryptographiquement sécurisée pour la production
"""

import secrets
import string
import sys

def generate_secret_key(length: int = 64) -> str:
    """
    Génère une clé secrète cryptographiquement sécurisée
    
    Args:
        length: Longueur de la clé (minimum 32, recommandé 64)
    
    Returns:
        Clé secrète sécurisée
    """
    if length < 32:
        length = 32
    
    # Caractères autorisés pour la clé secrète
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    
    # Générer la clé de manière cryptographiquement sécurisée
    secret_key = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    return secret_key

def main():
    """Fonction principale"""
    print("🔐 GÉNÉRATEUR DE CLÉ SECRÈTE SÉCURISÉE")
    print("=" * 50)
    
    # Générer une clé de 64 caractères
    secret_key = generate_secret_key(64)
    
    print(f"✅ Clé secrète générée (64 caractères)")
    print(f"📋 Longueur: {len(secret_key)} caractères")
    print(f"🔒 Sécurité: Cryptographiquement sécurisée")
    print()
    print("📝 Ajoutez cette ligne à votre fichier .env :")
    print("-" * 50)
    print(f"SECRET_KEY={secret_key}")
    print("-" * 50)
    print()
    print("⚠️  IMPORTANT:")
    print("• Ne jamais commiter cette clé dans le code")
    print("• Gardez cette clé secrète et sécurisée")
    print("• Utilisez des clés différentes pour dev/staging/prod")
    print("• Changez régulièrement vos clés en production")
    
    return secret_key

if __name__ == "__main__":
    main()