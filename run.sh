#!/bin/bash

# Script d'aide pour gérer l'API Django + data.gouv.fr

case "$1" in
    "up")
        echo "🚀 Démarrage des services..."
        docker-compose up -d
        ;;
    "down")
        echo "🛑 Arrêt des services..."
        docker-compose down
        ;;
    "build")
        echo "🔧 Construction des images..."
        docker-compose build --no-cache
        ;;
    "logs")
        echo "📋 Logs des services..."
        docker-compose logs -f
        ;;
    "shell")
        echo "🐚 Shell Django..."
        docker-compose exec web python manage.py shell
        ;;
    "makemigrations")
        echo "📝 Création des migrations..."
        docker-compose exec web python manage.py makemigrations
        ;;
    "migrate")
        echo "⚡ Application des migrations..."
        docker-compose exec web python manage.py migrate
        ;;
    "test")
        echo "🧪 Lancement des tests..."
        docker-compose exec web python manage.py test
        ;;
    "superuser")
        echo "👤 Création d'un superuser..."
        docker-compose exec web python manage.py createsuperuser
        ;;
    *)
        echo "Usage: $0 {up|down|build|logs|shell|makemigrations|migrate|test|superuser}"
        echo ""
        echo "Commands:"
        echo "  up              - Démarre les services"
        echo "  down            - Arrête les services"
        echo "  build           - Reconstruit les images Docker"
        echo "  logs            - Affiche les logs"
        echo "  shell           - Ouvre un shell Django"
        echo "  makemigrations  - Crée les migrations"
        echo "  migrate         - Applique les migrations"
        echo "  test            - Lance les tests"
        echo "  superuser       - Crée un superuser"
        ;;
esac