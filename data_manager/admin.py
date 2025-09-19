from django.contrib import admin
from django.utils.html import format_html
from .models import Dataset, Resource, DataRecord, SyncLog


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ['title', 'organization', 'datagouv_id', 'is_active', 'last_sync', 'created_at']
    list_filter = ['is_active', 'organization', 'created_at', 'last_sync']
    search_fields = ['title', 'description', 'datagouv_id', 'organization']
    readonly_fields = ['id', 'created_at', 'updated_at']
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('title', 'slug', 'description', 'datagouv_id')
        }),
        ('Métadonnées', {
            'fields': ('organization', 'tags', 'license')
        }),
        ('Dates source', {
            'fields': ('created_at_source', 'updated_at_source')
        }),
        ('Status', {
            'fields': ('is_active', 'last_sync')
        }),
        ('Dates locales', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('resources')


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'dataset_title', 'format', 'processing_status', 'is_processed', 'file_size_display', 'last_processed']
    list_filter = ['format', 'processing_status', 'is_processed', 'created_at']
    search_fields = ['title', 'description', 'dataset__title']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['dataset']
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('dataset', 'title', 'description', 'datagouv_id', 'url')
        }),
        ('Métadonnées fichier', {
            'fields': ('format', 'mime_type', 'file_size')
        }),
        ('Traitement', {
            'fields': ('is_processed', 'processing_status', 'processing_error', 'last_processed')
        }),
        ('Dates', {
            'fields': ('created_at_source', 'updated_at_source', 'id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def dataset_title(self, obj):
        return obj.dataset.title
    dataset_title.short_description = 'Dataset'
    
    def file_size_display(self, obj):
        if obj.file_size:
            if obj.file_size > 1024 * 1024:  # MB
                return f"{obj.file_size / (1024 * 1024):.1f} MB"
            elif obj.file_size > 1024:  # KB
                return f"{obj.file_size / 1024:.1f} KB"
            else:
                return f"{obj.file_size} B"
        return "-"
    file_size_display.short_description = 'Taille'


@admin.register(DataRecord)
class DataRecordAdmin(admin.ModelAdmin):
    list_display = ['resource_title', 'row_number', 'data_preview', 'created_at']
    list_filter = ['resource__format', 'created_at']
    search_fields = ['resource__title', 'data']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['resource']
    
    fieldsets = (
        ('Informations', {
            'fields': ('resource', 'row_number')
        }),
        ('Données', {
            'fields': ('data',)
        }),
        ('Métadonnées', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def resource_title(self, obj):
        return obj.resource.title
    resource_title.short_description = 'Ressource'
    
    def data_preview(self, obj):
        data_str = str(obj.data)[:100]
        if len(str(obj.data)) > 100:
            data_str += "..."
        return data_str
    data_preview.short_description = 'Aperçu données'


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ['sync_type', 'status', 'datasets_processed', 'resources_processed', 'records_created', 'started_at', 'duration']
    list_filter = ['sync_type', 'status', 'started_at']
    search_fields = ['message', 'error_details']
    readonly_fields = ['id', 'started_at', 'duration']
    
    fieldsets = (
        ('Synchronisation', {
            'fields': ('sync_type', 'status')
        }),
        ('Statistiques', {
            'fields': ('datasets_processed', 'resources_processed', 'records_created')
        }),
        ('Messages', {
            'fields': ('message', 'error_details')
        }),
        ('Dates', {
            'fields': ('id', 'started_at', 'completed_at', 'duration'),
            'classes': ('collapse',)
        })
    )
    
    def duration(self, obj):
        if obj.completed_at and obj.started_at:
            delta = obj.completed_at - obj.started_at
            return f"{delta.total_seconds():.1f}s"
        return "-"
    duration.short_description = 'Durée'
    
    def has_add_permission(self, request):
        # Empêche l'ajout manuel de logs
        return False
