#!/usr/bin/env python3
"""
Script de démonstration de l'API Django Data.gouv.fr
Montre les principales fonctionnalités de l'API
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_separator(title):
    print("\n" + "="*50)
    print(f"🔍 {title}")
    print("="*50)

def print_json(data, max_items=3):
    if isinstance(data, dict) and 'results' in data:
        results = data['results'][:max_items] if max_items else data['results']
        data_copy = data.copy()
        data_copy['results'] = results
        if len(data['results']) > max_items:
            data_copy['showing'] = f"{max_items} sur {len(data['results'])} résultats"
        print(json.dumps(data_copy, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))

def test_endpoint(method, url, data=None, description=""):
    print(f"\n📡 {method} {url}")
    if description:
        print(f"   {description}")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 201:
            return response.json()
        else:
            print(f"   Erreur: {response.text}")
            return None
            
    except Exception as e:
        print(f"   Erreur: {e}")
        return None

def main():
    print("🚀 Démonstration de l'API Django Data.gouv.fr")
    print("="*60)
    
    # Test 1: Page d'accueil
    print_separator("Page d'accueil de l'API")
    home_data = test_endpoint("GET", BASE_URL, description="Informations générales sur l'API")
    if home_data:
        # Afficher seulement les statistiques et un endpoint d'exemple
        stats = home_data.get('stats', {})
        print(f"\n📊 Statistiques:")
        for key, value in stats.items():
            print(f"   - {key}: {value}")
    
    # Test 2: Liste des datasets
    print_separator("Liste des datasets")
    datasets_data = test_endpoint("GET", f"{BASE_URL}/api/datasets/", description="Récupération de la liste des datasets")
    if datasets_data:
        print(f"\nTotal datasets: {datasets_data.get('count', 0)}")
        print_json(datasets_data, max_items=2)
    
    # Test 3: Statistiques
    print_separator("Statistiques détaillées")
    stats_data = test_endpoint("GET", f"{BASE_URL}/api/datasets/stats/", description="Statistiques complètes de l'API")
    if stats_data:
        print_json(stats_data)
    
    # Test 4: Recherche
    print_separator("Recherche de datasets")
    search_data = test_endpoint("GET", f"{BASE_URL}/api/datasets/search/?q=covid", 
                               description="Recherche de datasets contenant 'covid'")
    if search_data:
        print(f"\nRésultats trouvés: {search_data.get('count', 0)}")
        print_json(search_data, max_items=1)
    
    # Test 5: Synchronisation
    print_separator("Synchronisation de nouveaux datasets")
    sync_data = test_endpoint("POST", f"{BASE_URL}/api/datasets/sync/", 
                             data={"query": "education", "limit": 1},
                             description="Synchronisation d'1 dataset sur l'éducation")
    if sync_data:
        print_json(sync_data)
    
    # Test 6: Liste des ressources
    print_separator("Liste des ressources")
    resources_data = test_endpoint("GET", f"{BASE_URL}/api/resources/", 
                                  description="Récupération de toutes les ressources")
    if resources_data:
        print(f"\nTotal ressources: {resources_data.get('count', 0)}")
        print_json(resources_data, max_items=2)
    
    # Test 7: Logs de synchronisation
    print_separator("Logs de synchronisation")
    logs_data = test_endpoint("GET", f"{BASE_URL}/api/sync-logs/", 
                             description="Historique des synchronisations")
    if logs_data:
        print(f"\nTotal logs: {logs_data.get('count', 0)}")
        print_json(logs_data, max_items=2)
    
    print_separator("Démonstration terminée")
    print("🎉 L'API Django Data.gouv.fr est opérationnelle !")
    print("\n📝 Prochaines étapes suggérées:")
    print("   1. Accéder à l'admin Django: http://localhost:8000/admin/")
    print("   2. Explorer l'API: http://localhost:8000/")
    print("   3. Tester les endpoints avec curl ou Postman")
    print("   4. Synchroniser plus de données avec ./run.sh")
    print("\n👤 Admin credentials: admin / admin123")

if __name__ == "__main__":
    main()