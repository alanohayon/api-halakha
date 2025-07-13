"""
Utilitaires pour charger et manipuler les données JSON des halakhot
"""

import json
import os
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Chemin vers le fichier JSON des halakhot
JSON_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "halakhot.json")

async def load_halakha_by_index(index: int) -> str:
    """
    Charge une halakha spécifique par son index dans le fichier JSON
    
    Args:
        index: Index de la halakha à charger (commence à 0)
        
    Returns:
        Contenu de la halakha sous forme de string
        
    Raises:
        FileNotFoundError: Si le fichier JSON n'existe pas
        IndexError: Si l'index est invalide
        ValueError: Si la halakha est vide ou malformée
    """
    try:
        logger.info(f"📖 Chargement de la halakha à l'index {index}")
        
        # Vérifier que le fichier existe
        if not os.path.exists(JSON_FILE_PATH):
            raise FileNotFoundError(f"Fichier JSON non trouvé : {JSON_FILE_PATH}")
        
        # Charger le fichier JSON
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as file:
            halakhot_data = json.load(file)
        
        # Vérifier que c'est bien une liste
        if not isinstance(halakhot_data, list):
            raise ValueError("Le fichier JSON doit contenir une liste d'halakhot")
        
        # Vérifier que l'index est valide
        if index < 0 or index >= len(halakhot_data):
            raise IndexError(f"Index {index} invalide. Le fichier contient {len(halakhot_data)} halakhot (indices 0-{len(halakhot_data)-1})")
        
        # Extraire la halakha
        halakha_obj = halakhot_data[index]
        
        if not isinstance(halakha_obj, dict):
            raise ValueError(f"L'élément à l'index {index} n'est pas un objet valide")
        
        halakha_content = halakha_obj.get("halakha", "")
        
        if not halakha_content or not halakha_content.strip():
            raise ValueError(f"La halakha à l'index {index} est vide ou manquante")
        
        logger.info(f"✅ Halakha #{index} chargée avec succès ({len(halakha_content)} caractères)")
        return halakha_content.strip()
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du chargement de la halakha #{index}: {e}")
        raise

async def load_all_halakhot() -> List[Dict[str, Any]]:
    """
    Charge toutes les halakhot du fichier JSON
    
    Returns:
        Liste complète des halakhot avec leurs métadonnées
        
    Raises:
        FileNotFoundError: Si le fichier JSON n'existe pas
        ValueError: Si le fichier JSON est malformé
    """
    try:
        logger.info("📚 Chargement de toutes les halakhot")
        
        # Vérifier que le fichier existe
        if not os.path.exists(JSON_FILE_PATH):
            raise FileNotFoundError(f"Fichier JSON non trouvé : {JSON_FILE_PATH}")
        
        # Charger le fichier JSON
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as file:
            halakhot_data = json.load(file)
        
        # Vérifier que c'est bien une liste
        if not isinstance(halakhot_data, list):
            raise ValueError("Le fichier JSON doit contenir une liste d'halakhot")
        
        # Enrichir chaque halakha avec son index
        enriched_halakhot = []
        for i, halakha_obj in enumerate(halakhot_data):
            if isinstance(halakha_obj, dict) and halakha_obj.get("halakha"):
                enriched_halakha = {
                    **halakha_obj,
                    "index": i,
                    "character_count": len(halakha_obj.get("halakha", "")),
                    "word_count": len(halakha_obj.get("halakha", "").split())
                }
                enriched_halakhot.append(enriched_halakha)
            else:
                logger.warning(f"⚠️ Halakha malformée à l'index {i}, ignorée")
        
        logger.info(f"✅ {len(enriched_halakhot)} halakhot chargées sur {len(halakhot_data)} éléments du fichier")
        return enriched_halakhot
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du chargement de toutes les halakhot: {e}")
        raise

async def get_halakhot_count() -> int:
    """
    Retourne le nombre total d'halakhot disponibles dans le fichier JSON
    
    Returns:
        Nombre total d'halakhot
        
    Raises:
        FileNotFoundError: Si le fichier JSON n'existe pas
        ValueError: Si le fichier JSON est malformé
    """
    try:
        logger.info("🔢 Comptage des halakhot disponibles")
        
        # Vérifier que le fichier existe
        if not os.path.exists(JSON_FILE_PATH):
            raise FileNotFoundError(f"Fichier JSON non trouvé : {JSON_FILE_PATH}")
        
        # Charger le fichier JSON
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as file:
            halakhot_data = json.load(file)
        
        # Vérifier que c'est bien une liste
        if not isinstance(halakhot_data, list):
            raise ValueError("Le fichier JSON doit contenir une liste d'halakhot")
        
        # Compter uniquement les halakhot valides
        valid_count = 0
        for halakha_obj in halakhot_data:
            if isinstance(halakha_obj, dict) and halakha_obj.get("halakha", "").strip():
                valid_count += 1
        
        logger.info(f"📊 {valid_count} halakhot valides trouvées sur {len(halakhot_data)} éléments")
        return valid_count
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du comptage des halakhot: {e}")
        raise

async def get_halakhot_range(start_index: int, limit: int) -> List[Dict[str, Any]]:
    """
    Charge une plage spécifique d'halakhot (fonction bonus utile)
    
    Args:
        start_index: Index de départ (inclus)
        limit: Nombre maximum d'halakhot à charger
        
    Returns:
        Liste des halakhot dans la plage demandée
        
    Raises:
        ValueError: Si les paramètres sont invalides
    """
    try:
        logger.info(f"📋 Chargement de {limit} halakhot à partir de l'index {start_index}")
        
        # Charger toutes les halakhot
        all_halakhot = await load_all_halakhot()
        
        # Valider les paramètres
        if start_index < 0:
            raise ValueError("L'index de départ doit être >= 0")
        
        if limit <= 0:
            raise ValueError("La limite doit être > 0")
        
        if start_index >= len(all_halakhot):
            raise ValueError(f"Index de départ {start_index} >= nombre total d'halakhot {len(all_halakhot)}")
        
        # Calculer la fin
        end_index = min(start_index + limit, len(all_halakhot))
        
        # Extraire la plage
        halakhot_range = all_halakhot[start_index:end_index]
        
        logger.info(f"✅ {len(halakhot_range)} halakhot extraites (indices {start_index}-{end_index-1})")
        return halakhot_range
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du chargement de la plage d'halakhot: {e}")
        raise