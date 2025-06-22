from supabase import create_client, Client
from ..core.config import settings
from typing import List, Dict, Optional
from app.core.database import get_supabase

class SupabaseService:
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
    
    # CRUD avec Supabase client (plus simple pour certaines opérations)
    async def get_halakhot(self) -> List[Dict]:
        response = self.client.table('halakhot').select('*').execute()
        return response.data
    
    async def create_halakha(self, halakha_data: Dict) -> Dict:
        response = self.client.table('halakhot').insert(halakha_data).execute()
        return response.data[0] if response.data else None
    
    async def update_halakha(self, halakha_id: int, updates: Dict) -> Dict:
        response = (
            self.client.table('halakhot')
            .update(updates)
            .eq('id', halakha_id)
            .execute()
        )
        return response.data[0] if response.data else None
    
    async def delete_halakha(self, halakha_id: int) -> bool:
        response = (
            self.client.table('halakhot')
            .delete()
            .eq('id', halakha_id)
            .execute()
        )
        return len(response.data) > 0
    
    # Recherche avec filtres basés sur la structure réelle du modèle
    async def search_halakhot(self, theme: Optional[str] = None, 
                             source_name: Optional[str] = None,
                             title: Optional[str] = None) -> List[Dict]:
        """
        Recherche des halakhot avec filtres basés sur la structure réelle du modèle
        
        Args:
            theme: Filtrer par thème
            source_name: Filtrer par nom de source
            title: Filtrer par titre (recherche partielle)
        """
        query = self.client.table('halakhot').select('*')
        
        if theme:
            query = query.eq('theme', theme)
        if title:
            query = query.ilike('title', f'%{title}%')
        if source_name:
            # Pour filtrer par nom de source, il faudrait faire une jointure
            # ou d'abord récupérer l'ID de la source
            # Pour l'instant, on suppose que source_name correspond à source_id
            # ou on peut modifier cette logique selon vos besoins
            pass
            
        response = query.execute()
        return response.data
    
    # Méthode pour récupérer les halakhot avec leurs relations
    async def get_halakhot_with_relations(self) -> List[Dict]:
        """
        Récupère les halakhot avec leurs relations (source, question, answer)
        """
        response = (
            self.client.table('halakhot')
            .select('*, sources(name), questions(*), answers(*)')
            .execute()
        )
        return response.data
    
    # Méthode pour rechercher par tags
    async def search_halakhot_by_tag(self, tag_name: str) -> List[Dict]:
        """
        Recherche des halakhot par tag (nécessite une jointure avec la table halakha_tags)
        """
        # Cette méthode nécessiterait une jointure complexe
        # ou une approche en deux étapes selon la structure de Supabase
        response = (
            self.client.table('halakha_tags')
            .select('halakha_id, tags(name)')
            .eq('tags.name', tag_name)
            .execute()
        )
        
        if response.data:
            halakha_ids = [item['halakha_id'] for item in response.data]
            halakhot_response = (
                self.client.table('halakhot')
                .select('*')
                .in_('id', halakha_ids)
                .execute()
            )
            return halakhot_response.data
        
        return []
    
    # Authentification (si nécessaire)
    def sign_up(self, email: str, password: str):
        return self.client.auth.sign_up({"email": email, "password": password})
    
    def sign_in(self, email: str, password: str):
        return self.client.auth.sign_in_with_password({"email": email, "password": password})
