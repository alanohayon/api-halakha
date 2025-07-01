import logging
import os
import boto3
from botocore.exceptions import ClientError
from supabase import Client, SupabaseException
from typing import List, Dict, Optional
from app.utils.performance import measure_execution_time
from app.core.config import Settings


logger = logging.getLogger(__name__)

class SupabaseService:
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
    
    # ============================================================================
    # HALAKHOT - CRUD Operations
    # ============================================================================
    
    async def get_halakhot(self, skip: int = 0, limit: int = 100) -> Optional[List[Dict]]:
        """Récupérer les halakhot avec pagination"""
        try:
            response = (
                self.client.table('halakhot')
                .select('*')
                .range(skip, skip + limit - 1)
                .execute()
            )

            return response.data
        except SupabaseException as e:
            logger.error(f"SupabaseException get_halakhot: {e}")
            return None
        except Exception as e:
            logger.error(f"Exception get_halakhot: {e}")
            return None
    
    async def get_halakha_by_id(self, halakha_id: int) -> Optional[Dict]:
        """Récupérer une halakha par ID"""
        try:
            response = (
                self.client.table('halakhot')
                .select('*')
                .eq('id', halakha_id)
                .execute()
            )
            return response.data[0] if response.data else None
        except SupabaseException as e:
            logger.error(f"SupabaseException get_halakha_by_id: {e}")
            return None
        except Exception as e:
            logger.error(f"Exception get_halakha_by_id: {e}")
            return None
    
    @measure_execution_time("Création d'une halakha Supabase")
    async def create_halakha(self, halakha_data: Dict) -> Optional[Dict]:
        """
        Crée une halakha complète avec toutes ses relations
        
        Args:
            halakha_data: Dict contenant title, question, answer, sources, themes, tags, difficulty_level
        
        Returns:
            Dict: La halakha créée avec son ID
        """
        try:
            # 1. Créer la question
            question_response = self.client.table('questions').insert({
                'question': halakha_data['question']
            }).execute()
            if hasattr(question_response, 'error') and question_response.error:
                logger.error(f"Erreur Supabase create question: {question_response.error}")
                return question_response.error
            question_id = question_response.data[0]['id']
            
            # 2. Créer la réponse
            answer_response = self.client.table('answers').insert({
                'answer': halakha_data['answer']
            }).execute()
            if hasattr(answer_response, 'error') and answer_response.error:
                logger.error(f"Erreur Supabase create answer: {answer_response.error}")
                self.client.table('questions').delete().eq('id', question_id).execute()
                return answer_response.error
            answer_id = answer_response.data[0]['id']
            
            # 3. Créer ou récupérer toutes les sources (many-to-many)
            source_ids = []
            try:
                sources_data = halakha_data.get('sources', [])
                if not sources_data:
                    # Créer une source par défaut si aucune n'est fournie
                    default_source = self.client.table('sources').insert({
                        'name': 'Source inconnue',
                        'page': None,
                        'full_src': 'Source inconnue'
                    }).execute()
                    if hasattr(default_source, 'error') and default_source.error:
                        logger.error(f"Erreur Supabase create default source: {default_source.error}")
                        self.client.table('questions').delete().eq('id', question_id).execute()
                        self.client.table('answers').delete().eq('id', answer_id).execute()
                        return default_source.error
                    source_ids.append(default_source.data[0]['id'])
                else:
                    for src in sources_data:
                        existing_source = self.client.table('sources').select('*').eq('name', src['name']).eq('full_src', src['full_src']).execute()
                        if hasattr(existing_source, 'error') and existing_source.error:
                            logger.error(f"Erreur Supabase select source: {existing_source.error}")
                            self.client.table('questions').delete().eq('id', question_id).execute()
                            self.client.table('answers').delete().eq('id', answer_id).execute()
                            return existing_source.error
                        if existing_source.data:
                            sid = existing_source.data[0]['id']
                        else:
                            source_response = self.client.table('sources').insert({
                                'name': src['name'],
                                'page': src.get('page'),
                                'full_src': src['full_src']
                            }).execute()
                            if hasattr(source_response, 'error') and source_response.error:
                                logger.error(f"Erreur Supabase create source: {source_response.error}")
                                self.client.table('questions').delete().eq('id', question_id).execute()
                                self.client.table('answers').delete().eq('id', answer_id).execute()
                                return source_response.error
                            sid = source_response.data[0]['id']
                        source_ids.append(sid)
            except SupabaseException as e:
                logger.error(f"SupabaseException create source: {e}")
                self.client.table('questions').delete().eq('id', question_id).execute()
                self.client.table('answers').delete().eq('id', answer_id).execute()
                return str(e)
            except Exception as e:
                logger.error(f"Exception create source: {e}")
                self.client.table('questions').delete().eq('id', question_id).execute()
                self.client.table('answers').delete().eq('id', answer_id).execute()
                return str(e)
            
            # 4. Créer la halakha principale
            try:
                halakha_response = self.client.table('halakhot').insert({
                    'title': halakha_data['title'],
                    'content': halakha_data['answer'],  # On utilise answer comme content
                    'difficulty_level': halakha_data.get('difficulty_level'),
                    'question_id': question_id,
                    'answer_id': answer_id
                }).execute()
                if hasattr(halakha_response, 'error') and halakha_response.error:
                    # Gestion de la contrainte UNIQUE sur content
                    if 'unique' in str(halakha_response.error).lower() or 'duplicate' in str(halakha_response.error).lower():
                        logger.warning(f"Contrainte UNIQUE violée sur content: {halakha_response.error}")
                        self.client.table('questions').delete().eq('id', question_id).execute()
                        self.client.table('answers').delete().eq('id', answer_id).execute()
                        return halakha_response.error
                    logger.error(f"Erreur Supabase create halakha: {halakha_response.error}")
                    self.client.table('questions').delete().eq('id', question_id).execute()
                    self.client.table('answers').delete().eq('id', answer_id).execute()
                    return halakha_response.error
            except SupabaseException as e:
                logger.error(f"SupabaseException create halakha: {e}")
                self.client.table('questions').delete().eq('id', question_id).execute()
                self.client.table('answers').delete().eq('id', answer_id).execute()
                return str(e)
            except Exception as e:
                # Gestion de la contrainte UNIQUE sur content (erreur d'exception)
                if 'unique' in str(e).lower() or 'duplicate' in str(e).lower():
                    logger.warning(f"Contrainte UNIQUE violée sur content: {e}")
                    self.client.table('questions').delete().eq('id', question_id).execute()
                    self.client.table('answers').delete().eq('id', answer_id).execute()
                    return str(e)
                logger.error(f"Exception create halakha: {e}")
                self.client.table('questions').delete().eq('id', question_id).execute()
                self.client.table('answers').delete().eq('id', answer_id).execute()
                return str(e)
            halakha_id = halakha_response.data[0]['id']
            
            # 5. Lier toutes les sources à la halakha (many-to-many)
            for sid in source_ids:
                try:
                    self.client.table('halakha_sources').insert({
                        'halakha_id': halakha_id,
                        'source_id': sid
                    }).execute()
                except Exception as e:
                    logger.error(f"Exception create halakha_sources: {e}")
                    continue
            
            # 6. Créer les thèmes
            if halakha_data.get('themes'):
                for theme_name in halakha_data['themes']:
                    try:
                        existing_theme = self.client.table('themes').select('*').eq('name', theme_name).execute()
                        if hasattr(existing_theme, 'error') and existing_theme.error:
                            logger.error(f"Erreur Supabase select theme: {existing_theme.error}")
                            continue
                        if existing_theme.data:
                            theme_id = existing_theme.data[0]['id']
                        else:
                            theme_response = self.client.table('themes').insert({
                                'name': theme_name
                            }).execute()
                            if hasattr(theme_response, 'error') and theme_response.error:
                                logger.error(f"Erreur Supabase create theme: {theme_response.error}")
                                continue
                            theme_id = theme_response.data[0]['id']
                        self.client.table('halakha_themes').insert({
                            'halakha_id': halakha_id,
                            'theme_id': theme_id
                        }).execute()
                    except Exception as e:
                        logger.error(f"Exception create theme: {e}")
                        continue
            
            # 7. Créer les tags
            if halakha_data.get('tags'):
                for tag_name in halakha_data['tags']:
                    try:
                        existing_tag = self.client.table('tags').select('*').eq('name', tag_name).execute()
                        if hasattr(existing_tag, 'error') and existing_tag.error:
                            logger.error(f"Erreur Supabase select tag: {existing_tag.error}")
                            continue
                        if existing_tag.data:
                            tag_id = existing_tag.data[0]['id']
                        else:
                            tag_response = self.client.table('tags').insert({
                                'name': tag_name
                            }).execute()
                            if hasattr(tag_response, 'error') and tag_response.error:
                                logger.error(f"Erreur Supabase create tag: {tag_response.error}")
                                continue
                            tag_id = tag_response.data[0]['id']
                        self.client.table('halakha_tags').insert({
                            'halakha_id': halakha_id,
                            'tag_id': tag_id
                        }).execute()
                    except Exception as e:
                        logger.error(f"Exception create tag: {e}")
                        continue
            
            # 8. Retourner la halakha créée avec toutes ses informations
            return {
                'id': halakha_id,
                'title': halakha_data['title'],
                'question': halakha_data['question'],
                'answer': halakha_data['answer'],
                'difficulty_level': halakha_data.get('difficulty_level'),
                'sources': halakha_data.get('sources', []),
                'themes': halakha_data.get('themes', []),
                'tags': halakha_data.get('tags', [])
            }
        except SupabaseException as e:
            logger.error(f"SupabaseException create_halakha: {e}")
            return str(e)
        except Exception as e:
            logger.error(f"Exception create_halakha: {e}")
            return str(e)

    async def update_halakha(self, halakha_id: int, updates: Dict) -> Dict:
        """Mettre à jour une halakha existante"""
        response = (
            self.client.table('halakhot')
            .update(updates)
            .eq('id', halakha_id)
            .execute()
        )
        return response.data[0] if response.data else None

    async def delete_halakha(self, halakha_id: int) -> bool:
        """
        Supprime une halakha et toutes ses relations
        """
        try:
            # Récupérer les IDs des question et answer avant suppression
            halakha_info = self.client.table('halakhot').select('question_id, answer_id').eq('id', halakha_id).execute()
            
            if not halakha_info.data:
                return False
            
            question_id = halakha_info.data[0]['question_id']
            answer_id = halakha_info.data[0]['answer_id']
            
            # Supprimer les relations (les contraintes ON DELETE CASCADE devraient s'en charger)
            # Mais on peut les supprimer explicitement pour être sûr
            self.client.table('halakha_sources').delete().eq('halakha_id', halakha_id).execute()
            self.client.table('halakha_themes').delete().eq('halakha_id', halakha_id).execute()
            self.client.table('halakha_tags').delete().eq('halakha_id', halakha_id).execute()
            
            # Supprimer la halakha principale
            response = self.client.table('halakhot').delete().eq('id', halakha_id).execute()
            
            # Supprimer la question et la réponse associées
            self.client.table('questions').delete().eq('id', question_id).execute()
            self.client.table('answers').delete().eq('id', answer_id).execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            print(f"Erreur lors de la suppression de la halakha: {e}")
            return False

    @measure_execution_time("Recherche d'une halakha Supabase")
    async def search_halakhot(self, 
                             search: Optional[str] = None,
                             theme: Optional[str] = None, 
                             tag: Optional[str] = None,
                             author: Optional[str] = None,
                             difficulty_level: Optional[int] = None,
                             skip: int = 0,
                             limit: int = 100) -> List[Dict]:
        """
        Recherche avancée des halakhot avec filtres et pagination
        """
        query = self.client.table('halakhot').select('*')
        
        # Recherche textuelle dans le titre et le contenu
        if search:
            # Utiliser OR pour chercher dans title ET content
            query = query.or_(f'title.ilike.%{search}%,content.ilike.%{search}%')
        
        # Filtrer par niveau de difficulté
        if difficulty_level:
            query = query.eq('difficulty_level', difficulty_level)
        
        # TODO: Implémenter les filtres par theme, tag et author avec des jointures
        # Ces filtres nécessitent des jointures complexes avec les tables de relations
        
        response = query.range(skip, skip + limit - 1).execute()
        return response.data

    async def get_halakha_sources(self, halakha_id: int) -> List[Dict]:
        """Récupérer toutes les sources associées à une halakha"""
        response = (
            self.client.table('halakha_sources')
            .select('sources(*)')
            .eq('halakha_id', halakha_id)
            .execute()
        )
        return [item['sources'] for item in response.data] if response.data else []

    # ============================================================================
    # SOURCES - CRUD Operations
    # ============================================================================
    
    async def get_sources(self, skip: int = 0, limit: int = 100, name: Optional[str] = None) -> List[Dict]:
        """Récupérer les sources avec pagination et filtres"""
        query = self.client.table('sources').select('*')
        
        if name:
            query = query.ilike('name', f'%{name}%')
            
        response = query.range(skip, skip + limit - 1).execute()
        return response.data
    
    async def get_source_by_id(self, source_id: int) -> Optional[Dict]:
        """Récupérer une source par ID"""
        response = (
            self.client.table('sources')
            .select('*')
            .eq('id', source_id)
            .execute()
        )
        return response.data[0] if response.data else None
    
    async def get_halakhot_by_source(self, source_id: int, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Récupérer toutes les halakhot associées à une source"""
        response = (
            self.client.table('halakha_sources')
            .select('halakhot(*)')
            .eq('source_id', source_id)
            .range(skip, skip + limit - 1)
            .execute()
        )
        return [item['halakhot'] for item in response.data] if response.data else []

    # ============================================================================
    # THEMES - CRUD Operations
    # ============================================================================
    
    async def get_themes(self, skip: int = 0, limit: int = 100, name: Optional[str] = None) -> List[Dict]:
        """Récupérer les thèmes avec pagination et filtres"""
        query = self.client.table('themes').select('*')
        
        if name:
            query = query.ilike('name', f'%{name}%')
            
        response = query.range(skip, skip + limit - 1).execute()
        return response.data
    
    async def get_theme_by_id(self, theme_id: int) -> Optional[Dict]:
        """Récupérer un thème par ID"""
        response = (
            self.client.table('themes')
            .select('*')
            .eq('id', theme_id)
            .execute()
        )
        return response.data[0] if response.data else None
    
    async def get_halakhot_by_theme(self, theme_id: int, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Récupérer toutes les halakhot associées à un thème"""
        response = (
            self.client.table('halakha_themes')
            .select('halakhot(*)')
            .eq('theme_id', theme_id)
            .range(skip, skip + limit - 1)
            .execute()
        )
        return [item['halakhot'] for item in response.data] if response.data else []

    # ============================================================================
    # TAGS - CRUD Operations
    # ============================================================================
    
    async def get_tags(self, skip: int = 0, limit: int = 100, name: Optional[str] = None) -> List[Dict]:
        """Récupérer les tags avec pagination et filtres"""
        query = self.client.table('tags').select('*')
        
        if name:
            query = query.ilike('name', f'%{name}%')
            
        response = query.range(skip, skip + limit - 1).execute()
        return response.data
    
    async def get_tag_by_id(self, tag_id: int) -> Optional[Dict]:
        """Récupérer un tag par ID"""
        response = (
            self.client.table('tags')
            .select('*')
            .eq('id', tag_id)
            .execute()
        )
        return response.data[0] if response.data else None
    
    async def get_halakhot_by_tag(self, tag_id: int, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Récupérer toutes les halakhot associées à un tag"""
        response = (
            self.client.table('halakha_tags')
            .select('halakhot(*)')
            .eq('tag_id', tag_id)
            .range(skip, skip + limit - 1)
            .execute()
        )
        return [item['halakhot'] for item in response.data] if response.data else []

    # ============================================================================
    # LEGACY METHODS (à conserver pour compatibilité)
    # ============================================================================
    
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
    
    async def search_halakhot_by_tag(self, tag_name: str) -> List[Dict]:
        """
        Recherche des halakhot par tag (nécessite une jointure avec la table halakha_tags)
        """
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

    async def replace_halakha(self, halakha_id: int, halakha_data: Dict) -> Dict:
        """
        Remplace complètement une halakha (PUT)
        Supprime et recrée toutes les relations
        """
        try:
            # 1. Supprimer l'ancienne halakha et ses relations
            await self.delete_halakha(halakha_id)
            
            # 2. Créer la nouvelle halakha avec le même ID (si possible)
            # Note: En Supabase, l'ID sera auto-généré, donc on ne peut pas garantir le même ID
            new_halakha = await self.create_halakha(halakha_data)
            
            return new_halakha
            
        except Exception as e:
            print(f"Erreur lors du remplacement de la halakha: {e}")
            raise e

    async def update_halakha_partial(self, halakha_id: int, updates: Dict) -> Dict:
        """
        Mise à jour partielle d'une halakha (PATCH)
        Met à jour uniquement les champs spécifiés
        """
        try:
            # Mise à jour de la table principale halakhot
            response = (
                self.client.table('halakhot')
                .update(updates)
                .eq('id', halakha_id)
                .execute()
            )
            
            # Si on met à jour la question ou la réponse, mettre à jour les tables liées
            if 'question' in updates:
                halakha_info = self.client.table('halakhot').select('question_id').eq('id', halakha_id).execute()
                if halakha_info.data:
                    question_id = halakha_info.data[0]['question_id']
                    self.client.table('questions').update({
                        'question': updates['question']
                    }).eq('id', question_id).execute()
            
            if 'answer' in updates:
                halakha_info = self.client.table('halakhot').select('answer_id').eq('id', halakha_id).execute()
                if halakha_info.data:
                    answer_id = halakha_info.data[0]['answer_id']
                    self.client.table('answers').update({
                        'answer': updates['answer']
                    }).eq('id', answer_id).execute()
            
            return response.data[0] if response.data else None
            
        except Exception as e:
            print(f"Erreur lors de la mise à jour partielle de la halakha: {e}")
            raise e
        
    async def upload_image(self, image_path: str, bucket: str = "notion-images") -> Optional[str]:
        """
        Upload une image vers Supabase Storage en utilisant l'interface S3 et retourne l'URL publique
        
        Args:
            image_path: Chemin vers le fichier image
            bucket: Nom du bucket Supabase (par défaut "notion-images")
            
        Returns:
            URL publique de l'image uploadée ou None en cas d'erreur
        """
        try:
            # Charger la configuration
            from app.core.config import get_settings
            settings = get_settings()
            
    
            
            file_name = os.path.basename(image_path)
            
            # Configurer le client S3 pour Supabase Storage
            s3_client = boto3.client(
                's3',
                endpoint_url="https://uiuormkgtawyflcaqhgl.supabase.co/storage/v1/s3",
                region_name="eu-west-3",
                aws_access_key_id="695ba2b1985bd84b434a150ea111f910",
                aws_secret_access_key=settings.supabase_service_key,  # Utiliser la service key comme secret
            )
            
            # Upload le fichier
            with open(image_path, "rb") as f:
                s3_client.upload_fileobj(
                    f,
                    bucket,
                    file_name,
                    ExtraArgs={
                        'ContentType': self._get_content_type(file_name),
                        'CacheControl': 'max-age=3600'
                    }
                )
            
            # Construire l'URL publique
            public_url = f"{settings.endpoint_s3}/{bucket}/{file_name}"
            logger.info(f"Image uploadée avec succès: {public_url}")
            print(f"URL publique: {public_url}")
            
            return public_url
            
        except ClientError as e:
            logger.error(f"Erreur S3 lors de l'upload de l'image: {e}")
            return None
        except Exception as e:
            logger.error(f"Erreur lors de l'upload de l'image: {e}")
            return None
    
    def _get_content_type(self, filename: str) -> str:
        """Détermine le type MIME basé sur l'extension du fichier"""
        extension = filename.lower().split('.')[-1]
        content_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'svg': 'image/svg+xml'
        }
        return content_types.get(extension, 'image/jpeg')
    
    async def uploa_img_to_supabase(self, image_path: str, bucket: str = "notion-images") -> Optional[str]:
        """
        Upload une image vers Supabase Storage et retourne l'URL publique
        
        Args:
            image_path: Chemin vers le fichier image
            bucket: Nom du bucket Supabase (par défaut "notion-images")
            
        Returns:
            URL publique de l'image uploadée ou None en cas d'erreur
        """
        try:
            # Utiliser la service key pour les permissions d'admin
            from supabase import create_client
            from app.core.config import get_settings
            settings = get_settings()
            
            # Créer un client avec la service key pour l'upload
            admin_client = create_client(settings.supabase_url, settings.supabase_service_key)
            
            file_name = os.path.basename(image_path)
            print(f"📤 Upload du fichier: {file_name}")
            
            with open(image_path, "rb") as f:
                response = admin_client.storage.from_(bucket).upload(
                    file=f,
                    path=file_name,  # Utiliser juste le nom du fichier, pas le chemin complet
                    file_options={"cache-control": "3600", "upsert": "false"}
                )
            
            print("Response upload:", response)
            
            if hasattr(response, 'error') and response.error:
                logger.error(f"Erreur lors de l'upload: {response.error}")
                return None
            
            # Générer l'URL publique
            public_url = admin_client.storage.from_(bucket).get_public_url(file_name)
            logger.info(f"Image uploadée avec succès: {public_url}")
            print(f"✅ URL publique: {public_url}")
            
            return public_url
            
        except Exception as e:
            logger.error(f"Erreur lors de l'upload: {e}")
            print(f"❌ Erreur: {e}")
            return None
