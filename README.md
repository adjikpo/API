# API Django Data.gouv.fr

🇫🇷 API Django pour récupérer et traiter les données de data.gouv.fr

## 🚀 Démarrage rapide

### Prérequis
- Docker
- Docker Compose

### Installation

1. Clonez le projet
2. Lancez les services :
```bash
./run.sh up
```

3. Appliquez les migrations :
```bash
./run.sh migrate
```

4. Accédez à l'API : [http://localhost:8000](http://localhost:8000)

## 📋 Commandes utiles

```bash
./run.sh up              # Démarre les services
./run.sh down            # Arrête les services
./run.sh logs            # Affiche les logs
./run.sh migrate         # Applique les migrations
./run.sh shell           # Ouvre un shell Django
./run.sh superuser       # Crée un superuser
```

## 🏗️ Architecture

- **Django 4.2** - Framework web
- **PostgreSQL 15** - Base de données
- **Django REST Framework** - API REST
- **Docker** - Containerisation

## 📱 Endpoints

- `/admin/` - Interface d'administration Django
- `/api/` - Endpoints de l'API (à venir)

## 🔧 Configuration

Les variables d'environnement sont définies dans le fichier `.env`.
SImple API test
