from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.urls import reverse
from .models import Dataset, Resource, DataRecord, SyncLog


@api_view(['GET'])
def api_home(request):
    """
    Page d'accueil de l'API avec informations générales et liens vers les endpoints
    """
    base_url = request.build_absolute_uri('/api/')
    
    # Statistiques rapides
    stats = {
        'datasets': Dataset.objects.filter(is_active=True).count(),
        'resources': Resource.objects.count(),
        'processed_resources': Resource.objects.filter(is_processed=True).count(),
        'data_records': DataRecord.objects.count(),
        'sync_logs': SyncLog.objects.count(),
    }
    
    # Documentation des endpoints
    endpoints = {
        'datasets': {
            'url': f'{base_url}datasets/',
            'description': 'Liste et gestion des datasets',
            'methods': ['GET'],
            'actions': {
                'list': f'{base_url}datasets/',
                'detail': f'{base_url}datasets/{{id}}/',
                'search': f'{base_url}datasets/search/?q={{query}}',
                'sync': f'{base_url}datasets/sync/ [POST]',
                'stats': f'{base_url}datasets/stats/',
                'resources': f'{base_url}datasets/{{id}}/resources/',
            }
        },
        'resources': {
            'url': f'{base_url}resources/',
            'description': 'Liste et gestion des ressources',
            'methods': ['GET', 'POST'],
            'actions': {
                'list': f'{base_url}resources/',
                'detail': f'{base_url}resources/{{id}}/',
                'process': f'{base_url}resources/{{id}}/process/ [POST]',
                'data': f'{base_url}resources/{{id}}/data/',
            }
        },
        'records': {
            'url': f'{base_url}records/',
            'description': 'Données parsées des ressources',
            'methods': ['GET'],
            'actions': {
                'list': f'{base_url}records/',
                'detail': f'{base_url}records/{{id}}/',
            }
        },
        'sync_logs': {
            'url': f'{base_url}sync-logs/',
            'description': 'Logs de synchronisation',
            'methods': ['GET'],
            'actions': {
                'list': f'{base_url}sync-logs/',
                'detail': f'{base_url}sync-logs/{{id}}/',
            }
        }
    }
    
    return Response({
        'message': 'API Django Data.gouv.fr',
        'version': '1.0.0',
        'description': 'API pour récupérer et traiter les données de data.gouv.fr',
        'admin_panel': request.build_absolute_uri('/admin/'),
        'stats': stats,
        'endpoints': endpoints,
        'example_usage': {
            'search_datasets': f'{base_url}datasets/search/?q=covid',
            'get_dataset_resources': f'{base_url}datasets/{{id}}/resources/',
            'sync_new_datasets': f'{base_url}datasets/sync/ [POST] {{"query": "transport", "limit": 5}}',
            'process_resource': f'{base_url}resources/{{id}}/process/ [POST] {{"max_rows": 100}}',
        }
    })


@api_view(['GET'])
def api_docs(request):
    """
    Documentation détaillée de l'API
    """
    return Response({
        'title': 'API Django Data.gouv.fr - Documentation',
        'description': 'Cette API permet de récupérer, parser et exposer les données de data.gouv.fr',
        'authentication': 'Aucune authentification requise pour les endpoints de lecture',
        'pagination': {
            'default_page_size': 20,
            'max_page_size': 100,
            'parameters': ['page', 'page_size']
        },
        'filtering': {
            'description': 'La plupart des endpoints supportent le filtrage',
            'examples': [
                '?organization=INSEE',
                '?format=CSV',
                '?is_active=true'
            ]
        },
        'search': {
            'description': 'Recherche textuelle dans les champs pertinents',
            'parameter': 'search',
            'example': '?search=covid'
        },
        'ordering': {
            'description': 'Tri des résultats',
            'parameter': 'ordering',
            'examples': [
                '?ordering=-created_at',
                '?ordering=title'
            ]
        },
        'response_format': {
            'success': {
                'status_code': 200,
                'format': 'JSON'
            },
            'error': {
                'status_codes': [400, 404, 500],
                'format': {'error': 'Message d\'erreur'}
            }
        }
    })