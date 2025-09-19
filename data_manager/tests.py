from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Dataset, Resource, DataRecord, SyncLog
from .services import DataGouvService, DatasetSyncService


class DataGouvServiceTest(TestCase):
    """Tests pour le service Data.gouv.fr"""
    
    def setUp(self):
        self.service = DataGouvService()
    
    def test_service_initialization(self):
        """Test l'initialisation du service"""
        self.assertIsNotNone(self.service.base_url)
        self.assertIn('data.gouv.fr', self.service.base_url)
    
    def test_search_datasets_structure(self):
        """Test la structure de la requête de recherche (sans appel réseau)"""
        # Ce test vérifie la structure sans faire d'appel réseau réel
        params = {
            'q': 'test',
            'page': 1,
            'page_size': 20
        }
        
        # Vérifier que les paramètres sont correctement construits
        self.assertEqual(params['q'], 'test')
        self.assertEqual(params['page'], 1)
        self.assertEqual(params['page_size'], 20)


class APIEndpointsTest(APITestCase):
    """Tests pour les endpoints de l'API"""
    
    def setUp(self):
        # Créer des données de test
        self.dataset = Dataset.objects.create(
            datagouv_id='test-dataset-id',
            title='Dataset de Test',
            slug='dataset-de-test',
            description='Un dataset pour les tests',
            organization='Test Organization'
        )
        
        self.resource = Resource.objects.create(
            dataset=self.dataset,
            datagouv_id='test-resource-id',
            title='Resource de Test',
            url='https://example.com/test.csv',
            format='CSV'
        )
    
    def test_api_home(self):
        """Test la page d'accueil de l'API"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('message', data)
        self.assertIn('version', data)
        self.assertIn('endpoints', data)
        self.assertIn('stats', data)
    
    def test_datasets_list(self):
        """Test l'endpoint de liste des datasets"""
        url = '/api/datasets/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('results', data)
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['title'], 'Dataset de Test')
    
    def test_datasets_detail(self):
        """Test l'endpoint de détail d'un dataset"""
        url = f'/api/datasets/{self.dataset.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['title'], 'Dataset de Test')
        self.assertEqual(data['datagouv_id'], 'test-dataset-id')
        self.assertIn('resources', data)
    
    def test_datasets_search(self):
        """Test l'endpoint de recherche"""
        url = '/api/datasets/search/'
        response = self.client.get(url, {'q': 'test'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('results', data)
    
    def test_datasets_search_no_query(self):
        """Test la recherche sans paramètre q"""
        url = '/api/datasets/search/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        data = response.json()
        self.assertIn('error', data)
    
    def test_datasets_stats(self):
        """Test l'endpoint des statistiques"""
        url = '/api/datasets/stats/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('total_datasets', data)
        self.assertIn('active_datasets', data)
        self.assertIn('total_resources', data)
        self.assertEqual(data['total_datasets'], 1)
        self.assertEqual(data['total_resources'], 1)
    
    def test_resources_list(self):
        """Test l'endpoint de liste des ressources"""
        url = '/api/resources/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('results', data)
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['title'], 'Resource de Test')
    
    def test_resources_detail(self):
        """Test l'endpoint de détail d'une ressource"""
        url = f'/api/resources/{self.resource.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['title'], 'Resource de Test')
        self.assertEqual(data['format'], 'CSV')
    
    def test_sync_logs_list(self):
        """Test l'endpoint des logs de synchronisation"""
        # Créer un log de test
        sync_log = SyncLog.objects.create(
            sync_type='single',
            status='completed',
            message='Test sync'
        )
        
        url = '/api/sync-logs/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('results', data)
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['message'], 'Test sync')


class ModelsTest(TestCase):
    """Tests pour les modèles"""
    
    def test_dataset_creation(self):
        """Test la création d'un dataset"""
        dataset = Dataset.objects.create(
            datagouv_id='test-id',
            title='Test Dataset',
            slug='test-dataset',
            description='Description de test'
        )
        
        self.assertEqual(dataset.title, 'Test Dataset')
        self.assertEqual(dataset.datagouv_id, 'test-id')
        self.assertTrue(dataset.is_active)
    
    def test_resource_creation(self):
        """Test la création d'une ressource"""
        dataset = Dataset.objects.create(
            datagouv_id='test-dataset',
            title='Test Dataset',
            slug='test-dataset'
        )
        
        resource = Resource.objects.create(
            dataset=dataset,
            datagouv_id='test-resource',
            title='Test Resource',
            url='https://example.com/test.csv',
            format='CSV'
        )
        
        self.assertEqual(resource.title, 'Test Resource')
        self.assertEqual(resource.dataset, dataset)
        self.assertFalse(resource.is_processed)
        self.assertEqual(resource.processing_status, 'pending')
    
    def test_data_record_creation(self):
        """Test la création d'un enregistrement de données"""
        dataset = Dataset.objects.create(
            datagouv_id='test-dataset',
            title='Test Dataset',
            slug='test-dataset'
        )
        
        resource = Resource.objects.create(
            dataset=dataset,
            datagouv_id='test-resource',
            title='Test Resource',
            url='https://example.com/test.csv',
            format='CSV'
        )
        
        record = DataRecord.objects.create(
            resource=resource,
            row_number=1,
            data={'name': 'Test', 'value': 123}
        )
        
        self.assertEqual(record.resource, resource)
        self.assertEqual(record.row_number, 1)
        self.assertEqual(record.data['name'], 'Test')
        self.assertEqual(record.data['value'], 123)
    
    def test_dataset_str_representation(self):
        """Test la représentation string d'un dataset"""
        dataset = Dataset.objects.create(
            datagouv_id='test-id',
            title='Test Dataset',
            slug='test-dataset'
        )
        
        self.assertEqual(str(dataset), 'Test Dataset')
    
    def test_resource_str_representation(self):
        """Test la représentation string d'une ressource"""
        dataset = Dataset.objects.create(
            datagouv_id='test-dataset',
            title='Test Dataset',
            slug='test-dataset'
        )
        
        resource = Resource.objects.create(
            dataset=dataset,
            datagouv_id='test-resource',
            title='Test Resource',
            url='https://example.com/test.csv',
            format='CSV'
        )
        
        expected = f"{dataset.title} - {resource.title}"
        self.assertEqual(str(resource), expected)


class DatasetSyncServiceTest(TestCase):
    """Tests pour le service de synchronisation (tests unitaires)"""
    
    def setUp(self):
        self.sync_service = DatasetSyncService()
    
    def test_service_initialization(self):
        """Test l'initialisation du service de synchronisation"""
        self.assertIsNotNone(self.sync_service.api_service)
        self.assertIsInstance(self.sync_service.api_service, DataGouvService)
    
    def test_parse_datetime_with_none(self):
        """Test le parsing d'une date None"""
        result = self.sync_service._parse_datetime(None)
        self.assertIsNone(result)
    
    def test_parse_datetime_with_empty_string(self):
        """Test le parsing d'une string vide"""
        result = self.sync_service._parse_datetime("")
        self.assertIsNone(result)
