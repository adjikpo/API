from django.core.management.base import BaseCommand, CommandError
from data_manager.services import DatasetSyncService
from data_manager.parsers import ResourceProcessor


class Command(BaseCommand):
    help = 'Synchronise les datasets depuis data.gouv.fr'

    def add_arguments(self, parser):
        parser.add_argument(
            '--query',
            type=str,
            default='covid',
            help='Terme de recherche pour les datasets (défaut: covid)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=5,
            help='Nombre maximum de datasets à synchroniser (défaut: 5)'
        )
        parser.add_argument(
            '--dataset-id',
            type=str,
            help='ID spécifique d\'un dataset à synchroniser'
        )
        parser.add_argument(
            '--process',
            action='store_true',
            help='Traite également les ressources après synchronisation'
        )
        parser.add_argument(
            '--max-rows',
            type=int,
            default=100,
            help='Nombre maximum de lignes à traiter par ressource (défaut: 100)'
        )

    def handle(self, *args, **options):
        sync_service = DatasetSyncService()
        processor = ResourceProcessor()
        
        query = options['query']
        limit = options['limit']
        dataset_id = options['dataset_id']
        process_resources = options['process']
        max_rows = options['max_rows']

        self.stdout.write(self.style.SUCCESS('🚀 Début de la synchronisation...'))

        try:
            if dataset_id:
                # Synchroniser un dataset spécifique
                self.stdout.write(f'📡 Synchronisation du dataset: {dataset_id}')
                dataset = sync_service.sync_single_dataset(dataset_id)
                datasets = [dataset]
                
            else:
                # Synchroniser par requête
                self.stdout.write(f'🔍 Recherche de datasets avec: "{query}" (limite: {limit})')
                datasets = sync_service.sync_datasets_by_query(query, limit)

            self.stdout.write(
                self.style.SUCCESS(f'✅ {len(datasets)} dataset(s) synchronisé(s)')
            )

            # Afficher les résultats
            for dataset in datasets:
                resources_count = dataset.resources.count()
                self.stdout.write(f'  📁 {dataset.title} ({resources_count} ressource(s))')

            # Traiter les ressources si demandé
            if process_resources and datasets:
                self.stdout.write(self.style.WARNING(f'⚙️ Traitement des ressources (max {max_rows} lignes par ressource)...'))
                
                total_records = 0
                total_processed = 0
                
                for dataset in datasets:
                    try:
                        results = processor.process_dataset_resources(dataset.datagouv_id, max_rows)
                        total_processed += results['processed_resources']
                        total_records += results['total_records']
                        
                        if results['errors']:
                            self.stdout.write(
                                self.style.WARNING(f'  ⚠️ {len(results["errors"])} erreur(s) pour {dataset.title}')
                            )
                        
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'  ❌ Erreur pour {dataset.title}: {e}')
                        )

                self.stdout.write(
                    self.style.SUCCESS(f'✅ Traitement terminé: {total_processed} ressource(s), {total_records} enregistrement(s)')
                )

            # Informations d'accès
            self.stdout.write('\n' + '='*50)
            self.stdout.write(self.style.SUCCESS('🎉 Synchronisation terminée !'))
            self.stdout.write('\n📊 Accédez à l\'admin Django: http://localhost:8000/admin/')
            self.stdout.write('   Identifiants: admin / admin123')
            self.stdout.write('\n📈 Statistiques:')
            self.stdout.write(f'   - Datasets: {len(datasets)}')
            if process_resources:
                self.stdout.write(f'   - Ressources traitées: {total_processed}')
                self.stdout.write(f'   - Enregistrements créés: {total_records}')

        except Exception as e:
            raise CommandError(f'Erreur lors de la synchronisation: {e}')