from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from .models import Dataset, Resource, DataRecord, SyncLog
from .serializers import (
    DatasetSerializer, DatasetSummarySerializer, ResourceSerializer,
    DataRecordSerializer, SyncLogSerializer
)
from .services import DatasetSyncService
from .parsers import ResourceProcessor


class StandardResultsSetPagination(PageNumberPagination):
    """Pagination personnalisée"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class DatasetViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les datasets
    
    Endpoints disponibles:
    - GET /api/datasets/ : Liste des datasets
    - GET /api/datasets/{id}/ : Détail d'un dataset
    - GET /api/datasets/search/?q=<query> : Recherche dans les datasets
    - POST /api/datasets/sync/ : Synchroniser des datasets
    """
    
    queryset = Dataset.objects.all().prefetch_related('resources')
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization', 'is_active']
    search_fields = ['title', 'description', 'organization', 'tags']
    ordering_fields = ['created_at', 'updated_at_source', 'last_sync', 'title']
    ordering = ['-last_sync']
    
    def get_serializer_class(self):
        """Utilise un serializer différent selon l'action"""
        if self.action == 'list':
            return DatasetSummarySerializer
        return DatasetSerializer
    
    def get_queryset(self):
        """Filtre les datasets selon les paramètres"""
        queryset = self.queryset
        
        # Filtrer par tag
        tag = self.request.query_params.get('tag')
        if tag:
            queryset = queryset.filter(tags__contains=[tag])
        
        # Filtrer les datasets actifs par défaut
        if self.request.query_params.get('show_inactive') != 'true':
            queryset = queryset.filter(is_active=True)
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Recherche avancée dans les datasets
        
        Paramètres:
        - q: terme de recherche
        - organization: filtrer par organisation
        - tag: filtrer par tag
        """
        query = request.query_params.get('q', '')
        if not query:
            return Response(
                {'error': 'Le paramètre "q" est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(organization__icontains=query) |
            Q(tags__contains=[query])
        ).distinct()
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def sync(self, request):
        """
        Synchronise des datasets depuis data.gouv.fr
        
        Paramètres POST:
        - query: terme de recherche (défaut: 'covid')
        - limit: nombre max de datasets (défaut: 10)
        """
        query = request.data.get('query', 'covid')
        limit = min(int(request.data.get('limit', 10)), 50)  # Max 50
        
        try:
            sync_service = DatasetSyncService()
            datasets = sync_service.sync_datasets_by_query(query, limit)
            
            serializer = DatasetSummarySerializer(datasets, many=True)
            
            return Response({
                'message': f'{len(datasets)} dataset(s) synchronisé(s)',
                'query': query,
                'count': len(datasets),
                'datasets': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def resources(self, request, pk=None):
        """Retourne les ressources d'un dataset"""
        dataset = self.get_object()
        resources = dataset.resources.all()
        
        page = self.paginate_queryset(resources)
        if page is not None:
            serializer = ResourceSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ResourceSerializer(resources, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques générales des datasets"""
        queryset = self.get_queryset()
        
        stats = {
            'total_datasets': queryset.count(),
            'active_datasets': queryset.filter(is_active=True).count(),
            'total_resources': Resource.objects.filter(dataset__in=queryset).count(),
            'processed_resources': Resource.objects.filter(
                dataset__in=queryset, is_processed=True
            ).count(),
            'total_records': DataRecord.objects.filter(
                resource__dataset__in=queryset
            ).count(),
        }
        
        # Top organisations
        top_orgs = (
            queryset.exclude(organization='')
            .values('organization')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        
        stats['top_organizations'] = list(top_orgs)
        
        return Response(stats)


class ResourceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les ressources
    
    Endpoints disponibles:
    - GET /api/resources/ : Liste des ressources
    - GET /api/resources/{id}/ : Détail d'une ressource
    - POST /api/resources/{id}/process/ : Traiter une ressource
    """
    
    queryset = Resource.objects.all().select_related('dataset')
    serializer_class = ResourceSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['format', 'is_processed', 'processing_status', 'dataset']
    search_fields = ['title', 'description', 'dataset__title']
    ordering_fields = ['created_at', 'updated_at_source', 'last_processed']
    ordering = ['-updated_at_source']
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """
        Traite une ressource (parse et sauvegarde les données)
        
        Paramètres POST:
        - max_rows: nombre max de lignes à traiter (défaut: 1000)
        """
        resource = self.get_object()
        max_rows = min(int(request.data.get('max_rows', 1000)), 5000)  # Max 5000
        
        try:
            processor = ResourceProcessor()
            records_count = processor.process_resource(resource, max_rows)
            
            serializer = self.get_serializer(resource)
            
            return Response({
                'message': f'Ressource traitée avec succès',
                'records_created': records_count,
                'resource': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def data(self, request, pk=None):
        """Retourne les données parsées d'une ressource"""
        resource = self.get_object()
        data_records = resource.data_records.all()
        
        page = self.paginate_queryset(data_records)
        if page is not None:
            serializer = DataRecordSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = DataRecordSerializer(data_records, many=True)
        return Response(serializer.data)


class DataRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les enregistrements de données
    
    Endpoints disponibles:
    - GET /api/records/ : Liste des enregistrements
    - GET /api/records/{id}/ : Détail d'un enregistrement
    """
    
    queryset = DataRecord.objects.all().select_related('resource', 'resource__dataset')
    serializer_class = DataRecordSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['resource', 'resource__dataset']
    search_fields = ['data']
    ordering_fields = ['created_at', 'row_number']
    ordering = ['resource', 'row_number']
    
    def get_queryset(self):
        """Filtre les enregistrements selon les paramètres"""
        queryset = self.queryset
        
        # Filtrer par dataset
        dataset_id = self.request.query_params.get('dataset')
        if dataset_id:
            queryset = queryset.filter(resource__dataset__id=dataset_id)
        
        return queryset


class SyncLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les logs de synchronisation
    
    Endpoints disponibles:
    - GET /api/sync-logs/ : Liste des logs
    - GET /api/sync-logs/{id}/ : Détail d'un log
    """
    
    queryset = SyncLog.objects.all()
    serializer_class = SyncLogSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['sync_type', 'status']
    ordering_fields = ['started_at', 'completed_at']
    ordering = ['-started_at']
