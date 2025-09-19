from django.db import models
from django.utils import timezone
import uuid


class Dataset(models.Model):
    """Modèle pour stocker les informations d'un dataset de data.gouv.fr"""
    
    # Identifiants
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    datagouv_id = models.CharField(max_length=100, unique=True, help_text="ID du dataset sur data.gouv.fr")
    
    # Informations principales
    title = models.CharField(max_length=500, help_text="Titre du dataset")
    slug = models.SlugField(max_length=200, unique=True, help_text="Slug du dataset")
    description = models.TextField(blank=True, help_text="Description du dataset")
    
    # Métadonnées
    organization = models.CharField(max_length=300, blank=True, help_text="Organisation propriétaire")
    tags = models.JSONField(default=list, blank=True, help_text="Tags associés au dataset")
    license = models.CharField(max_length=100, blank=True, help_text="Licence du dataset")
    
    # Dates
    created_at_source = models.DateTimeField(null=True, blank=True, help_text="Date de création sur data.gouv.fr")
    updated_at_source = models.DateTimeField(null=True, blank=True, help_text="Dernière modification sur data.gouv.fr")
    
    # Dates locales
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Status
    is_active = models.BooleanField(default=True, help_text="Dataset actif dans notre système")
    last_sync = models.DateTimeField(null=True, blank=True, help_text="Dernière synchronisation")
    
    class Meta:
        ordering = ['-updated_at_source']
        verbose_name = "Dataset"
        verbose_name_plural = "Datasets"
    
    def __str__(self):
        return self.title


class Resource(models.Model):
    """Modèle pour stocker les ressources (fichiers) d'un dataset"""
    
    # Relations
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='resources')
    
    # Identifiants
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    datagouv_id = models.CharField(max_length=100, help_text="ID de la ressource sur data.gouv.fr")
    
    # Informations principales
    title = models.CharField(max_length=500, help_text="Titre de la ressource")
    description = models.TextField(blank=True, null=True, help_text="Description de la ressource")
    url = models.URLField(help_text="URL de téléchargement de la ressource")
    
    # Métadonnées du fichier
    format = models.CharField(max_length=50, help_text="Format du fichier (CSV, JSON, etc.)")
    mime_type = models.CharField(max_length=100, blank=True, null=True, help_text="Type MIME du fichier")
    file_size = models.BigIntegerField(null=True, blank=True, help_text="Taille du fichier en octets")
    
    # Status de traitement
    is_processed = models.BooleanField(default=False, help_text="Ressource traitée et parsée")
    processing_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'En attente'),
            ('processing', 'En cours'),
            ('completed', 'Terminé'),
            ('failed', 'Échec'),
        ],
        default='pending'
    )
    processing_error = models.TextField(blank=True, help_text="Message d'erreur si échec")
    
    # Dates
    created_at_source = models.DateTimeField(null=True, blank=True)
    updated_at_source = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_processed = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-updated_at_source']
        verbose_name = "Resource"
        verbose_name_plural = "Resources"
        unique_together = ['dataset', 'datagouv_id']
    
    def __str__(self):
        return f"{self.dataset.title} - {self.title}"


class DataRecord(models.Model):
    """Modèle générique pour stocker les données parsées des ressources"""
    
    # Relations
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='data_records')
    
    # Identifiant
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Données
    data = models.JSONField(help_text="Données parsées de la ressource (format JSON)")
    
    # Index pour recherche
    row_number = models.PositiveIntegerField(help_text="Numéro de ligne dans le fichier source")
    
    # Dates
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['resource', 'row_number']
        verbose_name = "Data Record"
        verbose_name_plural = "Data Records"
        unique_together = ['resource', 'row_number']
    
    def __str__(self):
        return f"{self.resource.title} - Ligne {self.row_number}"


class SyncLog(models.Model):
    """Modèle pour tracer les synchronisations avec data.gouv.fr"""
    
    # Identifiant
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Type de synchronisation
    sync_type = models.CharField(
        max_length=20,
        choices=[
            ('full', 'Synchronisation complète'),
            ('incremental', 'Synchronisation incrémentale'),
            ('single', 'Dataset unique'),
        ],
        default='incremental'
    )
    
    # Résultats
    status = models.CharField(
        max_length=20,
        choices=[
            ('started', 'Démarré'),
            ('completed', 'Terminé'),
            ('failed', 'Échec'),
        ],
        default='started'
    )
    
    # Statistiques
    datasets_processed = models.PositiveIntegerField(default=0)
    resources_processed = models.PositiveIntegerField(default=0)
    records_created = models.PositiveIntegerField(default=0)
    
    # Messages
    message = models.TextField(blank=True, help_text="Message de statut")
    error_details = models.TextField(blank=True, help_text="Détails des erreurs")
    
    # Dates
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
        verbose_name = "Sync Log"
        verbose_name_plural = "Sync Logs"
    
    def __str__(self):
        return f"Sync {self.sync_type} - {self.status} ({self.started_at.strftime('%Y-%m-%d %H:%M')})"
