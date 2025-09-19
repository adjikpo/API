import csv
import json
import pandas as pd
import logging
import io
from typing import List, Dict, Any, Iterator
from django.utils import timezone
from .models import Resource, DataRecord
from .services import DataGouvService

logger = logging.getLogger(__name__)


class BaseParser:
    """Classe de base pour tous les parsers"""
    
    def __init__(self, resource: Resource):
        self.resource = resource
        self.api_service = DataGouvService()
    
    def parse_and_save(self, max_rows: int = 1000) -> int:
        """
        Parse les données et les sauvegarde en base
        
        Args:
            max_rows: Nombre maximum de lignes à traiter
        
        Returns:
            Nombre de lignes traitées
        """
        raise NotImplementedError("Les sous-classes doivent implémenter parse_and_save")
    
    def _save_records(self, data_iterator: Iterator[Dict], max_rows: int = 1000) -> int:
        """Sauvegarde les enregistrements en base de données"""
        records_created = 0
        batch_size = 100
        records_batch = []
        
        # Marquer le début du traitement
        self.resource.processing_status = 'processing'
        self.resource.save()
        
        try:
            for row_number, row_data in enumerate(data_iterator, 1):
                if records_created >= max_rows:
                    break
                
                # Nettoyer les données
                cleaned_data = self._clean_row_data(row_data)
                
                # Créer l'enregistrement
                record = DataRecord(
                    resource=self.resource,
                    row_number=row_number,
                    data=cleaned_data
                )
                records_batch.append(record)
                
                # Sauvegarder par batch
                if len(records_batch) >= batch_size:
                    DataRecord.objects.bulk_create(records_batch, ignore_conflicts=True)
                    records_batch = []
                    records_created += batch_size
                    logger.debug(f"{records_created} enregistrements créés pour {self.resource.title}")
            
            # Sauvegarder le reste
            if records_batch:
                DataRecord.objects.bulk_create(records_batch, ignore_conflicts=True)
                records_created += len(records_batch)
            
            # Marquer comme terminé
            self.resource.is_processed = True
            self.resource.processing_status = 'completed'
            self.resource.last_processed = timezone.now()
            self.resource.processing_error = ""
            self.resource.save()
            
            logger.info(f"{records_created} enregistrements créés pour {self.resource.title}")
            return records_created
            
        except Exception as e:
            self.resource.processing_status = 'failed'
            self.resource.processing_error = str(e)
            self.resource.save()
            logger.error(f"Erreur lors du parsing de {self.resource.title}: {e}")
            raise
    
    def _clean_row_data(self, row_data: Any) -> Dict:
        """Nettoie et normalise les données d'une ligne"""
        if isinstance(row_data, dict):
            return {k: self._clean_value(v) for k, v in row_data.items()}
        elif isinstance(row_data, (list, tuple)):
            return {f"column_{i}": self._clean_value(v) for i, v in enumerate(row_data)}
        else:
            return {"value": self._clean_value(row_data)}
    
    def _clean_value(self, value: Any) -> Any:
        """Nettoie une valeur individuelle"""
        if pd.isna(value):
            return None
        elif isinstance(value, str):
            return value.strip()
        else:
            return value


class CSVParser(BaseParser):
    """Parser pour les fichiers CSV"""
    
    def parse_and_save(self, max_rows: int = 1000) -> int:
        """Parse un fichier CSV et sauvegarde les données"""
        logger.info(f"Parsing du fichier CSV: {self.resource.title}")
        
        try:
            # Télécharger le fichier
            response = self.api_service.download_resource(self.resource.url)
            
            # Détecter l'encodage
            content = response.content
            encoding = self._detect_encoding(content)
            
            # Parser le CSV
            text_content = content.decode(encoding)
            csv_reader = csv.DictReader(io.StringIO(text_content))
            
            return self._save_records(csv_reader, max_rows)
            
        except Exception as e:
            logger.error(f"Erreur lors du parsing CSV de {self.resource.title}: {e}")
            raise
    
    def _detect_encoding(self, content: bytes) -> str:
        """Détecte l'encodage d'un fichier"""
        # Essayer UTF-8 en premier
        try:
            content.decode('utf-8')
            return 'utf-8'
        except UnicodeDecodeError:
            pass
        
        # Essayer d'autres encodages courants
        encodings = ['latin-1', 'cp1252', 'iso-8859-1']
        for encoding in encodings:
            try:
                content.decode(encoding)
                return encoding
            except UnicodeDecodeError:
                continue
        
        # Par défaut, utiliser utf-8 avec gestion des erreurs
        return 'utf-8'


class JSONParser(BaseParser):
    """Parser pour les fichiers JSON"""
    
    def parse_and_save(self, max_rows: int = 1000) -> int:
        """Parse un fichier JSON et sauvegarde les données"""
        logger.info(f"Parsing du fichier JSON: {self.resource.title}")
        
        try:
            # Télécharger le fichier
            response = self.api_service.download_resource(self.resource.url)
            json_data = response.json()
            
            # Traiter selon la structure du JSON
            if isinstance(json_data, list):
                # Liste d'objets
                return self._save_records(iter(json_data), max_rows)
            elif isinstance(json_data, dict):
                # Objet unique ou objet avec des clés de données
                data_iterator = self._extract_data_from_dict(json_data)
                return self._save_records(data_iterator, max_rows)
            else:
                # Valeur unique
                return self._save_records([json_data], max_rows)
            
        except Exception as e:
            logger.error(f"Erreur lors du parsing JSON de {self.resource.title}: {e}")
            raise
    
    def _extract_data_from_dict(self, json_dict: Dict) -> Iterator[Dict]:
        """Extrait les données d'un dictionnaire JSON"""
        # Chercher des clés communes qui contiennent des listes de données
        data_keys = ['data', 'results', 'items', 'records', 'features']
        
        for key in data_keys:
            if key in json_dict and isinstance(json_dict[key], list):
                yield from json_dict[key]
                return
        
        # Si aucune clé de données trouvée, traiter l'objet entier
        yield json_dict


class ExcelParser(BaseParser):
    """Parser pour les fichiers Excel (.xlsx, .xls)"""
    
    def parse_and_save(self, max_rows: int = 1000) -> int:
        """Parse un fichier Excel et sauvegarde les données"""
        logger.info(f"Parsing du fichier Excel: {self.resource.title}")
        
        try:
            # Télécharger le fichier
            response = self.api_service.download_resource(self.resource.url)
            
            # Lire avec pandas
            df = pd.read_excel(io.BytesIO(response.content))
            
            # Limiter le nombre de lignes
            if len(df) > max_rows:
                df = df.head(max_rows)
            
            # Convertir en itérateur de dictionnaires
            data_iterator = df.to_dict('records')
            
            return self._save_records(iter(data_iterator), max_rows)
            
        except Exception as e:
            logger.error(f"Erreur lors du parsing Excel de {self.resource.title}: {e}")
            raise


class ParserFactory:
    """Factory pour créer les parsers appropriés selon le format"""
    
    PARSERS = {
        'CSV': CSVParser,
        'JSON': JSONParser,
        'XLSX': ExcelParser,
        'XLS': ExcelParser,
        'GEOJSON': JSONParser,  # GeoJSON est du JSON
    }
    
    @classmethod
    def get_parser(cls, resource: Resource) -> BaseParser:
        """
        Retourne le parser approprié pour une ressource
        
        Args:
            resource: Ressource à parser
        
        Returns:
            Instance du parser approprié
        
        Raises:
            ValueError: Si le format n'est pas supporté
        """
        format_upper = resource.format.upper()
        
        if format_upper not in cls.PARSERS:
            supported_formats = ', '.join(cls.PARSERS.keys())
            raise ValueError(f"Format {resource.format} non supporté. Formats supportés: {supported_formats}")
        
        parser_class = cls.PARSERS[format_upper]
        return parser_class(resource)
    
    @classmethod
    def is_supported_format(cls, format_name: str) -> bool:
        """Vérifie si un format est supporté"""
        return format_name.upper() in cls.PARSERS


class ResourceProcessor:
    """Service principal pour traiter les ressources"""
    
    def process_resource(self, resource: Resource, max_rows: int = 1000) -> int:
        """
        Traite une ressource en utilisant le parser approprié
        
        Args:
            resource: Ressource à traiter
            max_rows: Nombre maximum de lignes à traiter
        
        Returns:
            Nombre d'enregistrements créés
        """
        if not ParserFactory.is_supported_format(resource.format):
            logger.warning(f"Format {resource.format} non supporté pour {resource.title}")
            resource.processing_status = 'failed'
            resource.processing_error = f"Format {resource.format} non supporté"
            resource.save()
            return 0
        
        if resource.is_processed:
            logger.info(f"Ressource {resource.title} déjà traitée")
            return resource.data_records.count()
        
        try:
            parser = ParserFactory.get_parser(resource)
            records_count = parser.parse_and_save(max_rows)
            logger.info(f"Ressource {resource.title} traitée avec succès: {records_count} enregistrements")
            return records_count
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de {resource.title}: {e}")
            resource.processing_status = 'failed'
            resource.processing_error = str(e)
            resource.save()
            raise
    
    def process_dataset_resources(self, dataset_id: str, max_rows: int = 1000) -> Dict[str, int]:
        """
        Traite toutes les ressources d'un dataset
        
        Args:
            dataset_id: ID du dataset
            max_rows: Nombre maximum de lignes par ressource
        
        Returns:
            Dictionnaire avec les statistiques de traitement
        """
        from .models import Dataset
        
        try:
            dataset = Dataset.objects.get(datagouv_id=dataset_id)
        except Dataset.DoesNotExist:
            raise ValueError(f"Dataset {dataset_id} non trouvé")
        
        results = {
            'processed_resources': 0,
            'total_records': 0,
            'errors': []
        }
        
        for resource in dataset.resources.all():
            try:
                records_count = self.process_resource(resource, max_rows)
                results['processed_resources'] += 1
                results['total_records'] += records_count
            except Exception as e:
                results['errors'].append({
                    'resource_id': resource.datagouv_id,
                    'resource_title': resource.title,
                    'error': str(e)
                })
        
        return results