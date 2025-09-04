import json
import os

def debug_process_halakhot_local(file_path, start_index, limit=25):
    """
    Fonction de debug pour traiter les halakhot en local sans appels aux services externes
    """
    print(f"=== DÉBUT DU TRAITEMENT LOCAL DES HALAKHOT ===")
    print(f"Fichier: {file_path}")
    print(f"Index de départ: {start_index}")
    print(f"Nombre d'halakhot à traiter: {limit}")
    print("=" * 50)
    
    # Charger le fichier JSON
    hks_json = load_json_file(file_path)
    if not hks_json:
        print("❌ Impossible de charger le fichier JSON")
        return False
    
    total_halakhot = len(hks_json)
    print(f"📊 Nombre total d'halakhot dans le fichier: {total_halakhot}")
    
    # Vérifier l'index de départ
    if start_index >= total_halakhot:
        print(f"❌ L'index de départ ({start_index}) est supérieur au nombre total d'halakhot ({total_halakhot})")
        return False
    
    # Calculer l'index de fin
    end_index = min(start_index + limit, total_halakhot)
    print(f"🎯 Traitement des halakhot {start_index + 1} à {end_index}")
    
    # Boucler sur les halakhot à partir de l'index donné (limité à 25)
    for i, hk_data in enumerate(hks_json[start_index:end_index], start=start_index):
        print(f"\n--- HALAKHA {i+1}/{total_halakhot} ---")
        
        # Extraire le texte de l'halakha
        if isinstance(hk_data, dict) and "halakha" in hk_data:
            hk_text = hk_data["halakha"]
        elif isinstance(hk_data, str):
            hk_text = hk_data
        else:
            print(f"⚠️  Format inattendu pour l'halakha {i+1}: {type(hk_data)}")
            continue
        
        # Afficher un aperçu du texte (premiers 100 caractères)
        preview = hk_text[:100].replace('\n', ' ').strip()
        print(f"📝 Aperçu: {preview}...")
        
        # # Simuler le traitement (sans appels aux services)
        # print(f"✅ Halakha {i+1} traitée localement")
        
        # Optionnel: pause pour permettre de voir le traitement
        # input("Appuyez sur Entrée pour continuer...")
    
    print(f"\n=== FIN DU TRAITEMENT ===")
    print(f"✅ {end_index - start_index} halakhot traitées localement (sur {limit} demandées)")
    return True


def load_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            hks_json = json.load(file)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
    return hks_json


if __name__ == "__main__":
    # Obtenir le répertoire courant du script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Construire le chemin vers le fichier halakhot.json
    file_path = os.path.join(current_dir, "..", "app", "data", "halakhot.json")
    
    # Configuration pour le debug local
    start_index = 312  # Index de départ
    limit = 25  # Nombre d'halakhot à traiter
    
    print(f"📁 Répertoire courant: {current_dir}")
    print(f"📄 Chemin du fichier: {file_path}")
    
    # Exécuter le traitement local
    debug_process_halakhot_local(file_path, start_index, limit)