#!/usr/bin/env python3
"""
Exemple d'utilisation de l'API asynchrone pour les traitements longs

Ce script montre comment :
1. Démarrer un traitement en arrière-plan
2. Faire du polling pour suivre le progrès
3. Récupérer le résultat final
"""

import requests
import time
import json
from typing import Dict, Any

class HalakhaAPIClient:
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
    
    def start_processing(self, halakha_content: str, add_day: int = 0) -> Dict[str, Any]:
        """
        Démarre le traitement d'une halakha en arrière-plan
        """
        response = requests.post(
            f"{self.base_url}/process/start",
            params={
                "halakha_content": halakha_content,
                "add_day": add_day
            }
        )
        response.raise_for_status()
        return response.json()
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Récupère le statut d'un job
        """
        response = requests.get(f"{self.base_url}/process/status/{job_id}")
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(self, job_id: str, poll_interval: int = 5, max_wait: int = 3600) -> Dict[str, Any]:
        """
        Attend la completion d'un job avec polling
        
        Args:
            job_id: ID du job à suivre
            poll_interval: Intervalle en secondes entre les vérifications
            max_wait: Temps maximum d'attente en secondes
        """
        start_time = time.time()
        
        print(f"🔄 Suivi du job {job_id}...")
        
        while time.time() - start_time < max_wait:
            try:
                status = self.get_job_status(job_id)
                
                print(f"⏱️  [{int(time.time() - start_time)}s] Status: {status['status']} - {status['message']}")
                
                if status['status'] == 'completed':
                    print(f"✅ Job terminé avec succès !")
                    return status
                
                elif status['status'] == 'failed':
                    print(f"❌ Job échoué: {status.get('error', 'Erreur inconnue')}")
                    return status
                
                # Attendre avant la prochaine vérification
                time.sleep(poll_interval)
                
            except requests.RequestException as e:
                print(f"⚠️  Erreur lors de la vérification du statut: {e}")
                time.sleep(poll_interval)
        
        print(f"⏰ Timeout atteint ({max_wait}s)")
        return {"status": "timeout", "message": "Temps d'attente dépassé"}

def main():
    """
    Exemple d'utilisation complète
    """
    # Initialiser le client
    client = HalakhaAPIClient()
    
    # Contenu de test
    halakha_content = """
    Question: Que dit la halakha sur la consultation d'Internet le Chabbat ?
    
    Réponse: Cette question moderne nécessite une analyse approfondie...
    [Contenu long qui peut prendre du temps à traiter]
    """
    
    print("🚀 Démarrage du traitement d'une halakha...")
    
    try:
        # 1. Démarrer le traitement
        start_response = client.start_processing(halakha_content, add_day=1)
        job_id = start_response['job_id']
        
        print(f"✅ Job créé: {job_id}")
        print(f"📊 URL de polling: {start_response['polling_url']}")
        
        # 2. Attendre la completion avec polling
        final_status = client.wait_for_completion(job_id, poll_interval=10, max_wait=3600)
        
        # 3. Afficher le résultat
        if final_status['status'] == 'completed':
            result = final_status.get('result', {})
            notion_url = result.get('notion_page_url', 'URL non disponible')
            print(f"🎉 Traitement terminé ! Page Notion: {notion_url}")
        else:
            print(f"💥 Échec du traitement: {final_status.get('error', 'Erreur inconnue')}")
    
    except requests.RequestException as e:
        print(f"❌ Erreur de communication avec l'API: {e}")
    except KeyboardInterrupt:
        print(f"\n⛔ Interrompu par l'utilisateur")
        print(f"🔄 Le job {job_id if 'job_id' in locals() else 'N/A'} continue en arrière-plan")

def list_jobs_example():
    """
    Exemple pour lister tous les jobs
    """
    client = HalakhaAPIClient()
    
    try:
        response = requests.get(f"{client.base_url}/process/jobs")
        response.raise_for_status()
        jobs_data = response.json()
        
        print(f"📋 Jobs actifs: {jobs_data['total']}")
        for job in jobs_data['jobs']:
            print(f"  • {job['job_id']}: {job['status']} - {job['message']}")
    
    except requests.RequestException as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 EXEMPLE D'UTILISATION API ASYNCHRONE")
    print("=" * 50)
    
    # Exemple principal
    main()
    
    print("\n" + "=" * 50)
    print("📋 LISTE DES JOBS")
    print("=" * 50)
    
    # Lister les jobs
    list_jobs_example() 