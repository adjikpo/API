import requests
import logging
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from .models import Dataset, Resource, SyncLog

logger = logging.getLogger(__name__)


class DataGouvService:
    """Service pour interagir avec l'API de data.gouv.fr"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'DATAGOUV_API_BASE_URL', 'https://www.data.gouv.fr/api/1/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Django-API-DataGouv/1.0'
        })
    
    def search_datasets(self, query: str = "", page: int = 1, page_size: int = 20, **kwargs) -> Dict:
        """
        Recherche des datasets sur data.gouv.fr
        
        Args:
            query: Terme de recherche
            page: Numéro de page
            page_size: Nombre de résultats par page
            **kwargs: Autres paramètres de recherche
        
        Returns:
            Dict contenant les résultats de la recherche
        """
        params = {
            'q': query,
            'page': page,
            'page_size': page_size,
            **kwargs
        }
        
        try:
            response = self.session.get(f"{self.base_url}datasets/", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Erreur lors de la recherche de datasets: {e}")
            raise
    
    def get_dataset(self, dataset_id: str) -> Dict:
        """
        Récupère un dataset spécifique par son ID
        
        Args:
            dataset_id: ID du dataset sur data.gouv.fr
        
        Returns:
            Dict contenant les informations du dataset
        """
        try:
            response = self.session.get(f"{self.base_url}datasets/{dataset_id}/")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Erreur lors de la récupération du dataset {dataset_id}: {e}")
            raise
    
    def get_organizations(self, page: int = 1, page_size: int = 20) -> Dict:
        """
        Récupère la liste des organisations
        
        Args:
            page: Numéro de page
            page_size: Nombre de résultats par page
        
        Returns:
            Dict contenant les organisations
        """
        params = {
            'page': page,
            'page_size': page_size
        }
        
        try:
            response = self.session.get(f"{self.base_url}organizations/", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Erreur lors de la récupération des organisations: {e}")
            raise
    
    def download_resource(self, url: str, stream: bool = True) -> requests.Response:
        """
        Télécharge une ressource depuis son URL
        
        Args:
            url: URL de la ressource
            stream: Si True, télécharge en streaming
        
        Returns:
            Response object
        """
        try:
            response = self.session.get(url, stream=stream)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"Erreur lors du téléchargement de la ressource {url}: {e}")
            raise


class DatasetSyncService:
    """Service pour synchroniser les datasets avec la base de données locale"""
    
    def __init__(self):
        self.api_service = DataGouvService()
    
    def sync_single_dataset(self, dataset_id: str) -> Dataset:
        """
        Synchronise un dataset unique
        
        Args:
            dataset_id: ID du dataset sur data.gouv.fr
        
        Returns:
            Instance de Dataset créée ou mise à jour
        """
        logger.info(f"Synchronisation du dataset {dataset_id}")
        
        # Créer un log de synchronisation
        sync_log = SyncLog.objects.create(
            sync_type='single',
            message=f"Synchronisation du dataset {dataset_id}"
        )
        
        try:
            # Récupérer les données depuis l'API
            dataset_data = self.api_service.get_dataset(dataset_id)
            
            # Créer ou mettre à jour le dataset
            dataset = self._create_or_update_dataset(dataset_data)
            
            # Synchroniser les ressources
            resources_count = self._sync_dataset_resources(dataset, dataset_data.get('resources', []))
            
            # Marquer la synchronisation comme terminée
            sync_log.status = 'completed'
            sync_log.datasets_processed = 1
            sync_log.resources_processed = resources_count
            sync_log.completed_at = timezone.now()
            sync_log.save()
            
            logger.info(f"Dataset {dataset_id} synchronisé avec succès")
            return dataset
            
        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_details = str(e)
            sync_log.completed_at = timezone.now()
            sync_log.save()
            logger.error(f"Erreur lors de la synchronisation du dataset {dataset_id}: {e}")
            raise
    
    def sync_datasets_by_query(self, query: str, limit: int = 50) -> List[Dataset]:
        """
        Synchronise les datasets correspondant à une recherche
        
        Args:
            query: Terme de recherche
            limit: Nombre maximum de datasets à synchroniser
        
        Returns:
            Liste des datasets synchronisés
        """
        logger.info(f"Synchronisation des datasets pour la requête: {query}")
        
        sync_log = SyncLog.objects.create(
            sync_type='incremental',
            message=f"Synchronisation par requête: {query}"
        )
        
        datasets = []
        page = 1
        total_processed = 0
        
        try:
            while total_processed < limit:
                # Calculer le nombre d'éléments à récupérer pour cette page
                page_size = min(20, limit - total_processed)
                
                # Rechercher les datasets
                search_results = self.api_service.search_datasets(
                    query=query, 
                    page=page, 
                    page_size=page_size
                )
                
                dataset_list = search_results.get('data', [])
                if not dataset_list:
                    break
                
                # Synchroniser chaque dataset
                for dataset_data in dataset_list:
                    try:
                        dataset = self._create_or_update_dataset(dataset_data)
                        resources_count = self._sync_dataset_resources(dataset, dataset_data.get('resources', []))
                        datasets.append(dataset)
                        sync_log.resources_processed += resources_count
                    except Exception as e:
                        logger.error(f"Erreur lors de la synchronisation du dataset {dataset_data.get('id')}: {e}")
                        continue
                
                total_processed += len(dataset_list)
                page += 1
                
                # Si on a récupéré moins que demandé, on a atteint la fin
                if len(dataset_list) < page_size:
                    break
            
            sync_log.status = 'completed'
            sync_log.datasets_processed = len(datasets)
            sync_log.completed_at = timezone.now()
            sync_log.save()
            
            logger.info(f"{len(datasets)} datasets synchronisés")
            return datasets
            
        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_details = str(e)
            sync_log.completed_at = timezone.now()
            sync_log.save()
            logger.error(f"Erreur lors de la synchronisation par requête: {e}")
            raise
    
    def _create_or_update_dataset(self, dataset_data: Dict) -> Dataset:
        """Crée ou met à jour un dataset"""
        dataset_id = dataset_data['id']
        
        # Extraire les informations de l'organisation
        organization_name = ""
        if dataset_data.get('organization'):
            organization_name = dataset_data['organization'].get('name', '')
        
        # Préparer les données
        dataset_fields = {
            'title': dataset_data.get('title', ''),
            'slug': slugify(dataset_data.get('slug', dataset_data.get('title', dataset_id))),
            'description': dataset_data.get('description', ''),
            'organization': organization_name,
            'tags': [tag.get('name', tag) if isinstance(tag, dict) else tag for tag in dataset_data.get('tags', [])],
            'license': dataset_data.get('license', ''),
            'created_at_source': self._parse_datetime(dataset_data.get('created_at')),
            'updated_at_source': self._parse_datetime(dataset_data.get('last_modified')),
            'last_sync': timezone.now()
        }
        
        # Créer ou mettre à jour
        dataset, created = Dataset.objects.update_or_create(
            datagouv_id=dataset_id,
            defaults=dataset_fields
        )
        
        action = "créé" if created else "mis à jour"
        logger.debug(f"Dataset {dataset_id} {action}")
        
        return dataset
    
    def _sync_dataset_resources(self, dataset: Dataset, resources_data: List[Dict]) -> int:
        """Synchronise les ressources d'un dataset"""
        resources_count = 0
        
        for resource_data in resources_data:
            try:
                resource_fields = {
                    'title': resource_data.get('title', ''),
                    'description': resource_data.get('description', ''),
                    'url': resource_data.get('url', ''),
                    'format': resource_data.get('format', '').upper(),
                    'mime_type': resource_data.get('mime', ''),
                    'file_size': resource_data.get('filesize'),
                    'created_at_source': self._parse_datetime(resource_data.get('created_at')),
                    'updated_at_source': self._parse_datetime(resource_data.get('last_modified')),
                }
                
                resource, created = Resource.objects.update_or_create(
                    dataset=dataset,
                    datagouv_id=resource_data['id'],
                    defaults=resource_fields
                )
                
                resources_count += 1
                
            except Exception as e:
                logger.error(f"Erreur lors de la synchronisation de la ressource {resource_data.get('id')}: {e}")
                continue
        
        return resources_count
    
    def _parse_datetime(self, date_string: Optional[str]):
        """Parse une chaîne de date ISO"""
        if not date_string:
            return None
        
        try:
            from dateutil import parser
            return parser.parse(date_string)
        except Exception:
            logger.warning(f"Impossible de parser la date: {date_string}")
            return None