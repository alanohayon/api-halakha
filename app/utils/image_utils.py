import os
import glob
import re
import unicodedata
from datetime import datetime

def get_latest_image_path(downloads_folder="/Users/alanohayon/Downloads"):
    image_extensions = ["*.jpg", "*.jpeg", "*.png", "*.gif", "*.webp"]
    image_files = []
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(downloads_folder, ext)))
    if not image_files:
        return None
    latest_image = max(image_files, key=os.path.getmtime)
    print("lget_latest_image_path latest_image", latest_image)
    return latest_image

def get_latest_image_with_clean_name(downloads_folder="/Users/alanohayon/Downloads"):
    """
    Récupère le chemin de la dernière image dans Downloads et retourne un tuple
    (chemin_original, nom_fichier_nettoye)
    """
    original_path = get_latest_image_path(downloads_folder)
    if not original_path:
        return None, None
    
    clean_filename = get_clean_filename(original_path)
    print(f"📤 Fichier original: {os.path.basename(original_path)} -> nettoyé: {clean_filename}")
    
    return original_path, clean_filename

def sanitize_filename(filename: str) -> str:
    """
    Nettoie un nom de fichier pour le rendre compatible avec S3 et les systèmes de fichiers
    
    Args:
        filename: Le nom de fichier original
        
    Returns:
        str: Le nom de fichier nettoyé
    """
    # Récupérer le nom et l'extension
    name, ext = os.path.splitext(filename)
    
    # Normaliser les caractères Unicode (supprimer les accents)
    name = unicodedata.normalize('NFD', name)
    name = ''.join(char for char in name if unicodedata.category(char) != 'Mn')
    
    # Remplacer les espaces et caractères spéciaux par des underscores
    name = re.sub(r'[^\w\-_.]', '_', name)
    
    # Supprimer les underscores multiples
    name = re.sub(r'_+', '_', name)
    
    # Supprimer les underscores en début/fin
    name = name.strip('_')
    
    # Si le nom est vide, générer un nom par défaut
    if not name:
        name = f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Limiter la longueur (optionnel)
    if len(name) > 100:
        name = name[:100]
    
    return f"{name}{ext.lower()}"

def get_clean_filename(filepath: str) -> str:
    """
    Récupère un nom de fichier propre à partir d'un chemin complet
    
    Args:
        filepath: Le chemin complet vers le fichier
        
    Returns:
        str: Le nom de fichier nettoyé
    """
    original_filename = os.path.basename(filepath)
    return sanitize_filename(original_filename)