# API Django Data.gouv.fr

🇫🇷 **API Django complète pour récupérer, traiter et exposer les données de data.gouv.fr**

Cette API permet de :
- 🔄 Synchroniser automatiquement les datasets de data.gouv.fr
- 📊 Parser et stocker les données (CSV, JSON, Excel)
- 🔍 Rechercher et filtrer les datasets
- 📈 Fournir des statistiques en temps réel
- 🌐 Exposer une API REST complète

## 🚀 Démarrage rapide

### Prérequis
- **Docker** 20.10+
- **Docker Compose** 2.0+
- **Git**

### Installation

1. **Clonez le projet**
```bash
git clone <votre-repo>
cd API
```

2. **Démarrez l'environnement**
```bash
./run.sh up
```

3. **Appliquez les migrations**
```bash
./run.sh migrate
```

4. **Créez un superuser** (optionnel)
```bash
./run.sh superuser
```

5. **Testez l'API**
```bash
python3 demo_api.py
```

🎉 **L'API est maintenant accessible :**
- **API Home** : [http://localhost:8000](http://localhost:8000)
- **Admin Django** : [http://localhost:8000/admin](http://localhost:8000/admin) (admin / admin123)
- **API Endpoints** : [http://localhost:8000/api](http://localhost:8000/api)

## 📋 Commandes disponibles

### Scripts d'aide
```bash
./run.sh up              # Démarre les services
./run.sh down            # Arrête les services
./run.sh build           # Reconstruit les images
./run.sh logs            # Affiche les logs en temps réel
./run.sh shell           # Shell Django interactif
./run.sh migrate         # Applique les migrations
./run.sh makemigrations  # Crée de nouvelles migrations
./run.sh test            # Lance les tests
./run.sh superuser       # Crée un superuser admin
```

### Synchronisation des données
```bash
# Synchroniser des datasets par requête
docker-compose exec web python manage.py sync_datasets --query "covid" --limit 5

# Synchroniser et traiter les données
docker-compose exec web python manage.py sync_datasets --query "transport" --limit 3 --process --max-rows 100

# Synchroniser un dataset spécifique
docker-compose exec web python manage.py sync_datasets --dataset-id "53699b82a3a729239d20575d"
```

### Tests et démonstration
```bash
# Lancer tous les tests
./run.sh test

# Démonstration complète de l'API
python3 demo_api.py
```

### 🎮 Exemple de sortie du script de démonstration

<details>
<summary>🔍 Cliquez pour voir l'exemple complet d'exécution</summary>

```
🚀 Démonstration de l'API Django Data.gouv.fr
============================================================

==================================================
🔍 Page d'accueil de l'API
==================================================

📡 GET http://localhost:8000
   Informations générales sur l'API
   Status: 200

📊 Statistiques:
   - datasets: 7
   - resources: 10
   - processed_resources: 0
   - data_records: 0
   - sync_logs: 4

==================================================
🔍 Liste des datasets
==================================================

📡 GET http://localhost:8000/api/datasets/
   Récupération de la liste des datasets
   Status: 200

Total datasets: 7
{
  "count": 7,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "2dd467d3-98fe-493e-bc38-0d68e83b3029",
      "datagouv_id": "53699b82a3a729239d20575d",
      "title": "Paris par arrondissements. Paris par quartiers",
      "slug": "paris-par-arrondissements-paris-par-quartiers",
      "organization": "",
      "tags": [],
      "license": "notspecified",
      "is_active": true,
      "resources_count": 0,
      "total_records": 0,
      "created_at_source": "2014-02-23T16:58:53.990000Z",
      "last_sync": "2025-09-19T12:08:03.540999Z"
    },
    {
      "id": "67a6125c-a64b-4189-8763-0e3b7c5c7042",
      "datagouv_id": "55e4129788ee386899a46ec1",
      "title": "Transports",
      "slug": "transports",
      "organization": "Institut national de la statistique et des études économiques (Insee)",
      "tags": ["automobiles", "carburant", "immatriculations", "transports", "voitures"],
      "license": "fr-lo",
      "is_active": true,
      "resources_count": 0,
      "total_records": 0,
      "created_at_source": "2015-08-31T10:38:47.310000Z",
      "last_sync": "2025-09-19T11:55:22.802719Z"
    }
  ],
  "showing": "2 sur 7 résultats"
}

==================================================
🔍 Statistiques détaillées
==================================================

📡 GET http://localhost:8000/api/datasets/stats/
   Statistiques complètes de l'API
   Status: 200
{
  "total_datasets": 7,
  "active_datasets": 7,
  "total_resources": 10,
  "processed_resources": 0,
  "total_records": 0,
  "top_organizations": [
    {
      "organization": "Toulouse métropole",
      "count": 2
    },
    {
      "organization": "Fabrique numérique des ministères sociaux",
      "count": 1
    }
  ]
}

==================================================
🔍 Recherche de datasets
==================================================

📡 GET http://localhost:8000/api/datasets/search/?q=covid
   Recherche de datasets contenant 'covid'
   Status: 200

Résultats trouvés: 2
{
  "count": 2,
  "results": [
    {
      "id": "0968bfe1-022f-4a27-ba82-8c13f9170024",
      "title": "Tests covid-19 publiés par la plateforme covid-19.sante.gouv.fr",
      "organization": "Fabrique numérique des ministères sociaux",
      "tags": ["covid19"],
      "resources_count": 1,
      "resources": [
        {
          "title": "tests.csv",
          "format": "CSV",
          "file_size_human": "121.4 KB",
          "is_processed": false
        }
      ]
    }
  ]
}

==================================================
🔍 Synchronisation de nouveaux datasets
==================================================

📡 POST http://localhost:8000/api/datasets/sync/
   Synchronisation d'1 dataset sur l'éducation
   Status: 201
{
  "message": "1 dataset(s) synchronisé(s)",
  "query": "education",
  "count": 1,
  "datasets": [
    {
      "id": "c12d8c3d-1b92-470c-a1b2-23a20ef4c719",
      "title": "Education ",
      "organization": "CORBION",
      "resources_count": 1
    }
  ]
}

==================================================
🔍 Logs de synchronisation
==================================================

📡 GET http://localhost:8000/api/sync-logs/
   Historique des synchronisations
   Status: 200

Total logs: 5
{
  "results": [
    {
      "sync_type": "incremental",
      "status": "completed",
      "datasets_processed": 1,
      "resources_processed": 1,
      "message": "Synchronisation par requête: education",
      "duration": 0.12
    }
  ]
}

==================================================
🔍 Démonstration terminée
==================================================
🎉 L'API Django Data.gouv.fr est opérationnelle !

📝 Prochaines étapes suggérées:
   1. Accéder à l'admin Django: http://localhost:8000/admin/
   2. Explorer l'API: http://localhost:8000/
   3. Tester les endpoints avec curl ou Postman
   4. Synchroniser plus de données avec ./run.sh

👤 Admin credentials: admin / admin123
```

</details>

Cet exemple montre :
- ✅ **7 datasets** synchronisés depuis data.gouv.fr
- ✅ **Recherche fonctionnelle** (2 résultats COVID trouvés)
- ✅ **Synchronisation en temps réel** (nouveau dataset éducation ajouté)
- ✅ **Statistiques détaillées** par organisation
- ✅ **Historique complet** des opérations

## 🏗️ Architecture

### Stack technique
- **🐍 Python 3.11** - Langage
- **🌐 Django 4.2** - Framework web
- **📡 Django REST Framework** - API REST
- **🗄️ PostgreSQL 15** - Base de données
- **🐳 Docker** - Containerisation
- **📊 Pandas** - Traitement des données
- **🔍 Django Filter** - Filtrage avancé

### Modèles de données
- **Dataset** : Informations des datasets data.gouv.fr
- **Resource** : Ressources (fichiers) des datasets
- **DataRecord** : Données parsées stockées en JSON
- **SyncLog** : Historique des synchronisations

## 📱 API Endpoints

### Endpoints principaux

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/` | GET | Page d'accueil avec infos API |
| `/api/docs/` | GET | Documentation détaillée |
| `/admin/` | GET | Interface d'administration |

### Datasets

| Endpoint | Méthode | Description | Paramètres |
|----------|---------|-------------|------------|
| `/api/datasets/` | GET | Liste des datasets | `page`, `page_size`, `organization`, `is_active` |
| `/api/datasets/{id}/` | GET | Détail d'un dataset | - |
| `/api/datasets/search/` | GET | Recherche de datasets | `q` (requis), `organization`, `tag` |
| `/api/datasets/stats/` | GET | Statistiques générales | - |
| `/api/datasets/sync/` | POST | Synchroniser des datasets | `{"query": "covid", "limit": 10}` |
| `/api/datasets/{id}/resources/` | GET | Ressources d'un dataset | - |

### Ressources

| Endpoint | Méthode | Description | Paramètres |
|----------|---------|-------------|------------|
| `/api/resources/` | GET | Liste des ressources | `format`, `is_processed`, `dataset` |
| `/api/resources/{id}/` | GET | Détail d'une ressource | - |
| `/api/resources/{id}/process/` | POST | Traiter une ressource | `{"max_rows": 1000}` |
| `/api/resources/{id}/data/` | GET | Données parsées | - |

### Données et logs

| Endpoint | Méthode | Description | Paramètres |
|----------|---------|-------------|------------|
| `/api/records/` | GET | Enregistrements de données | `resource`, `dataset` |
| `/api/records/{id}/` | GET | Détail d'un enregistrement | - |
| `/api/sync-logs/` | GET | Logs de synchronisation | `sync_type`, `status` |
| `/api/sync-logs/{id}/` | GET | Détail d'un log | - |

### Exemples d'utilisation

```bash
# Rechercher des datasets COVID
curl "http://localhost:8000/api/datasets/search/?q=covid"

# Synchroniser 5 datasets sur le transport
curl -X POST -H "Content-Type: application/json" \
     -d '{"query": "transport", "limit": 5}' \
     http://localhost:8000/api/datasets/sync/

# Statistiques de l'API
curl "http://localhost:8000/api/datasets/stats/"

# Traiter une ressource CSV
curl -X POST -H "Content-Type: application/json" \
     -d '{"max_rows": 100}' \
     http://localhost:8000/api/resources/{resource_id}/process/
```

## 📊 Fonctionnalités

### ✅ Implémentées

- **🔄 Synchronisation automatique** depuis data.gouv.fr
- **📊 Parsing multi-format** (CSV, JSON, Excel)
- **🔍 Recherche et filtrage avancés**
- **📈 Statistiques en temps réel**
- **🌐 API REST complète avec pagination**
- **👤 Interface d'administration Django**
- **📝 Logs détaillés des opérations**
- **🧪 Tests automatisés complets**
- **🐳 Déploiement Docker prêt**

### 🚀 Formats supportés

- **CSV** : Détection automatique d'encodage
- **JSON** : Structure flexible avec auto-détection
- **Excel** : .xlsx et .xls
- **GeoJSON** : Traité comme du JSON

## 🔧 Configuration

### Variables d'environnement (`.env`)

```bash
# Django
DEBUG=True
SECRET_KEY=your-secret-key-here

# Base de données
DB_HOST=db
DB_NAME=api_datagouv
DB_USER=django_user
DB_PASS=django_pass
DB_PORT=5432

# API Data.gouv.fr
DATAGOUV_API_BASE_URL=https://www.data.gouv.fr/api/1/
```

### Personnalisation

- **Pagination** : Modifiez `PAGE_SIZE` dans `settings.py`
- **Formats supportés** : Ajoutez des parsers dans `parsers.py`
- **Limites** : Ajustez `max_rows` et `limit` dans les vues

## 🧪 Tests

```bash
# Tests complets
./run.sh test

# Tests spécifiques
docker-compose exec web python manage.py test data_manager.tests.APIEndpointsTest

# Coverage (si installé)
docker-compose exec web coverage run --source='.' manage.py test
docker-compose exec web coverage report
```

**19 tests implémentés** couvrant :
- Modèles Django
- Endpoints API
- Services de synchronisation
- Parsers de données

## 📈 Monitoring

### Logs disponibles

```bash
# Logs en temps réel
./run.sh logs

# Logs spécifiques
docker-compose logs web
docker-compose logs db
```

### Statistiques

Accédez aux statistiques via :
- **API** : `/api/datasets/stats/`
- **Admin** : Dashboard dans l'interface admin

## 🚧 Développement

### Structure du projet

```
API/
├── 🐳 docker-compose.yml     # Configuration Docker
├── 🐍 requirements.txt       # Dépendances Python
├── ⚙️ .env                   # Variables d'environnement
├── 🛠️ run.sh                # Scripts d'aide
├── 🎮 demo_api.py           # Démonstration API
├── datagouv_api/            # Projet Django principal
│   ├── settings.py
│   └── urls.py
└── data_manager/            # App principale
    ├── 📊 models.py         # Modèles de données
    ├── 🌐 views.py          # Vues API REST
    ├── 📡 serializers.py    # Sérialiseurs DRF
    ├── 🔄 services.py       # Services data.gouv.fr
    ├── 📋 parsers.py        # Parsers de données
    ├── 🧪 tests.py          # Tests automatisés
    └── 👤 admin.py          # Configuration admin
```

### Ajout de nouvelles fonctionnalités

1. **Nouveau parser** : Héritez de `BaseParser` dans `parsers.py`
2. **Nouveau endpoint** : Ajoutez une action dans `views.py`
3. **Nouveau modèle** : Créez dans `models.py` + migration
4. **Tests** : Ajoutez dans `tests.py`

## 🛠️ Maintenance

### Mise à jour

```bash
# Mise à jour des dépendances
docker-compose build --no-cache

# Nouvelle migration
./run.sh makemigrations
./run.sh migrate

# Nettoyage
docker-compose down -v  # ⚠️ Supprime les données
```

### Sauvegarde

```bash
# Export de la base
docker-compose exec db pg_dump -U django_user api_datagouv > backup.sql

# Import
docker-compose exec -T db psql -U django_user api_datagouv < backup.sql
```

## 🤝 Contribution

1. Fork le projet
2. Créez une branche (`git checkout -b feature/amazing-feature`)
3. Commitez vos changements (`git commit -m 'Add amazing feature'`)
4. Pushez vers la branche (`git push origin feature/amazing-feature`)
5. Ouvrez une Pull Request

## 📝 Roadmap

### Prochaines fonctionnalités
- **🔐 Authentification API** (JWT/OAuth2)
- **📊 Dashboard de monitoring** avancé
- **⚡ Cache Redis** pour les performances
- **🌍 Support géospatial** (PostGIS)
- **📤 Export des données** (CSV, Excel, PDF)
- **🔔 Notifications** de synchronisation
- **📋 Filtres avancés** et recherche full-text
- **🚀 API GraphQL** complémentaire

## 🐛 Dépannage

### Problèmes courants

**L'API ne démarre pas :**
```bash
./run.sh logs  # Vérifiez les erreurs
./run.sh build --no-cache  # Reconstruisez
```

**Erreur de base de données :**
```bash
docker-compose restart db
./run.sh migrate
```

**Problème de synchronisation :**
- Vérifiez votre connexion internet
- Consultez `/api/sync-logs/` pour les détails d'erreur

## 📄 Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

**🎉 L'API Django Data.gouv.fr est maintenant prête à l'emploi !**

Pour toute question : créez une issue ou consultez la documentation de l'API sur `http://localhost:8000/api/docs/`
SImple API test
