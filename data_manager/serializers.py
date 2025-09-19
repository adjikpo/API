from rest_framework import serializers
from .models import Dataset, Resource, DataRecord, SyncLog


class ResourceSerializer(serializers.ModelSerializer):
    """Serializer pour les ressources"""
    
    records_count = serializers.SerializerMethodField()
    file_size_human = serializers.SerializerMethodField()
    
    class Meta:
        model = Resource
        fields = [
            'id', 'datagouv_id', 'title', 'description', 'url',
            'format', 'mime_type', 'file_size', 'file_size_human',
            'is_processed', 'processing_status', 'processing_error',
            'records_count', 'created_at_source', 'updated_at_source',
            'created_at', 'last_processed'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_records_count(self, obj):
        """Retourne le nombre d'enregistrements parsés"""
        return obj.data_records.count()
    
    def get_file_size_human(self, obj):
        """Retourne la taille du fichier en format lisible"""
        if not obj.file_size:
            return None
        
        size = obj.file_size
        if size > 1024 * 1024:  # MB
            return f"{size / (1024 * 1024):.1f} MB"
        elif size > 1024:  # KB
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size} B"


class DatasetSerializer(serializers.ModelSerializer):
    """Serializer pour les datasets"""
    
    resources = ResourceSerializer(many=True, read_only=True)
    resources_count = serializers.SerializerMethodField()
    total_records = serializers.SerializerMethodField()
    
    class Meta:
        model = Dataset
        fields = [
            'id', 'datagouv_id', 'title', 'slug', 'description',
            'organization', 'tags', 'license', 'is_active',
            'resources_count', 'total_records', 'resources',
            'created_at_source', 'updated_at_source',
            'created_at', 'last_sync'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_resources_count(self, obj):
        """Retourne le nombre de ressources"""
        return obj.resources.count()
    
    def get_total_records(self, obj):
        """Retourne le nombre total d'enregistrements pour ce dataset"""
        return sum(resource.data_records.count() for resource in obj.resources.all())


class DatasetSummarySerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des datasets"""
    
    resources_count = serializers.SerializerMethodField()
    total_records = serializers.SerializerMethodField()
    
    class Meta:
        model = Dataset
        fields = [
            'id', 'datagouv_id', 'title', 'slug', 'organization',
            'tags', 'license', 'is_active', 'resources_count',
            'total_records', 'created_at_source', 'last_sync'
        ]
    
    def get_resources_count(self, obj):
        return obj.resources.count()
    
    def get_total_records(self, obj):
        return sum(resource.data_records.count() for resource in obj.resources.all())


class DataRecordSerializer(serializers.ModelSerializer):
    """Serializer pour les enregistrements de données"""
    
    resource_title = serializers.CharField(source='resource.title', read_only=True)
    dataset_title = serializers.CharField(source='resource.dataset.title', read_only=True)
    
    class Meta:
        model = DataRecord
        fields = [
            'id', 'resource', 'resource_title', 'dataset_title',
            'row_number', 'data', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SyncLogSerializer(serializers.ModelSerializer):
    """Serializer pour les logs de synchronisation"""
    
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = SyncLog
        fields = [
            'id', 'sync_type', 'status', 'datasets_processed',
            'resources_processed', 'records_created', 'message',
            'error_details', 'started_at', 'completed_at', 'duration'
        ]
        read_only_fields = ['id']
    
    def get_duration(self, obj):
        """Retourne la durée de synchronisation en secondes"""
        if obj.completed_at and obj.started_at:
            delta = obj.completed_at - obj.started_at
            return round(delta.total_seconds(), 2)
        return None