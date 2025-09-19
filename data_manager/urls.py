from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DatasetViewSet, ResourceViewSet, DataRecordViewSet, SyncLogViewSet
from .api_views import api_home, api_docs

# Router DRF pour les ViewSets
router = DefaultRouter()
router.register(r'datasets', DatasetViewSet)
router.register(r'resources', ResourceViewSet)
router.register(r'records', DataRecordViewSet)
router.register(r'sync-logs', SyncLogViewSet)

urlpatterns = [
    path('', api_home, name='api-home'),
    path('api/', include(router.urls)),
    path('api/docs/', api_docs, name='api-docs'),
]
