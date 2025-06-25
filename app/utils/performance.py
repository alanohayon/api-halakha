"""
Module utilitaire pour la mesure de performance

Ce module fournit des décorateurs génériques pour mesurer le temps d'exécution
des fonctions dans tous les services de l'application.
"""

from typing import Callable, Any
import asyncio
import time
from functools import wraps
import structlog

logger = structlog.get_logger()

def measure_execution_time(operation_name: str = ""):
    """
    Décorateur générique pour mesurer le temps d'exécution des fonctions
    
    Args:
        operation_name: Nom personnalisé de l'opération pour les logs.
                       Si vide, utilise le nom de la fonction.
    
    Usage:
        @measure_execution_time("Ma super opération")
        async def ma_fonction():
            pass
            
        @measure_execution_time()  # Utilise le nom de la fonction
        def ma_fonction_sync():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # Nom de l'opération pour les logs
            op_name = operation_name or func.__name__
            
            # Mesure du temps de début
            start_time = time.time()
            logger.info(f"⏱️ Démarrage de '{op_name}'")
            
            try:
                # Exécution de la fonction asynchrone
                result = await func(*args, **kwargs)
                
                # Calcul du temps d'exécution
                execution_time = time.time() - start_time
                logger.info(
                    f"✅ '{op_name}' terminé avec succès",
                    operation=op_name,
                    execution_time_seconds=round(execution_time, 3),
                    execution_time_formatted=f"{execution_time:.3f}s"
                )
                
                return result
                
            except Exception as e:
                # Calcul du temps d'exécution même en cas d'erreur
                execution_time = time.time() - start_time
                logger.error(
                    f"❌ '{op_name}' a échoué",
                    operation=op_name,
                    execution_time_seconds=round(execution_time, 3),
                    execution_time_formatted=f"{execution_time:.3f}s",
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # Nom de l'opération pour les logs
            op_name = operation_name or func.__name__
            
            # Mesure du temps de début
            start_time = time.time()
            logger.info(f"⏱️ Démarrage de '{op_name}'")
            
            try:
                # Exécution de la fonction synchrone
                result = func(*args, **kwargs)
                
                # Calcul du temps d'exécution
                execution_time = time.time() - start_time
                logger.info(
                    f"✅ '{op_name}' terminé avec succès",
                    operation=op_name,
                    execution_time_seconds=round(execution_time, 3),
                    execution_time_formatted=f"{execution_time:.3f}s"
                )
                
                return result
                
            except Exception as e:
                # Calcul du temps d'exécution même en cas d'erreur
                execution_time = time.time() - start_time
                logger.error(
                    f"❌ '{op_name}' a échoué",
                    operation=op_name,
                    execution_time_seconds=round(execution_time, 3),
                    execution_time_formatted=f"{execution_time:.3f}s",
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise
        
        # Retourner le wrapper approprié selon le type de fonction
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def measure_class_methods(*method_names: str):
    """
    Décorateur de classe pour mesurer automatiquement le temps d'exécution 
    de méthodes spécifiques d'une classe
    
    Args:
        *method_names: Noms des méthodes à instrumenter
    
    Usage:
        @measure_class_methods('method1', 'method2')
        class MyService:
            def method1(self):
                pass
            def method2(self):
                pass
    """
    def class_decorator(cls):
        for method_name in method_names:
            if hasattr(cls, method_name):
                original_method = getattr(cls, method_name)
                # Appliquer le décorateur avec le nom de la classe et méthode
                decorated_method = measure_execution_time(f"{cls.__name__}.{method_name}")(original_method)
                setattr(cls, method_name, decorated_method)
        return cls
    return class_decorator

# Décorateur de performance avec métadonnées personnalisées
def measure_with_metadata(**metadata):
    """
    Décorateur avancé avec métadonnées personnalisées
    
    Args:
        **metadata: Métadonnées à inclure dans les logs
        
    Usage:
        @measure_with_metadata(service="openai", operation_type="processing")
        async def process_text():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            operation_name = func.__name__
            start_time = time.time()
            
            # Log de début avec métadonnées
            log_data = {
                "operation": operation_name,
                **metadata
            }
            logger.info(f"⏱️ Démarrage de '{operation_name}'", **log_data)
            
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                logger.info(
                    f"✅ '{operation_name}' terminé avec succès",
                    execution_time_seconds=round(execution_time, 3),
                    execution_time_formatted=f"{execution_time:.3f}s",
                    **log_data
                )
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"❌ '{operation_name}' a échoué",
                    execution_time_seconds=round(execution_time, 3),
                    execution_time_formatted=f"{execution_time:.3f}s",
                    error=str(e),
                    error_type=type(e).__name__,
                    **log_data
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            operation_name = func.__name__
            start_time = time.time()
            
            # Log de début avec métadonnées
            log_data = {
                "operation": operation_name,
                **metadata
            }
            logger.info(f"⏱️ Démarrage de '{operation_name}'", **log_data)
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                logger.info(
                    f"✅ '{operation_name}' terminé avec succès",
                    execution_time_seconds=round(execution_time, 3),
                    execution_time_formatted=f"{execution_time:.3f}s",
                    **log_data
                )
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"❌ '{operation_name}' a échoué",
                    execution_time_seconds=round(execution_time, 3),
                    execution_time_formatted=f"{execution_time:.3f}s",
                    error=str(e),
                    error_type=type(e).__name__,
                    **log_data
                )
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator 