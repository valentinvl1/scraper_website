"""Script de test pour l'API PAR Scrape."""

import requests
import json

# Configuration
API_URL = "http://localhost:8000/scrape"

# Exemple de requête
payload = {
    "url": "https://example.com",
    "fetch_using": "selenium",  # ou "playwright"
    "sleep_time": 2,
    "headless": True,
    "wait_type": "sleep"
}

print("=" * 60)
print("TEST DE L'API PAR SCRAPE")
print("=" * 60)
print(f"\nURL à scraper: {payload['url']}")
print(f"Scraper: {payload['fetch_using']}")
print(f"Headless: {payload['headless']}")
print(f"Sleep time: {payload['sleep_time']}s")

try:
    print("\n🔄 Envoi de la requête...")
    response = requests.post(API_URL, json=payload, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        
        print("\n✅ Succès!")
        print("=" * 60)
        print(f"\n📊 RÉSULTATS:")
        print(f"  • URL scrapée: {data['url']}")
        print(f"  • Scraper utilisé: {data['fetch_using']}")
        print(f"  • Temps de traitement: {data['processing_time']:.2f}s")
        
        print(f"\n🔗 URLs TROUVÉES ({len(data['urls'])}):")
        if data['urls']:
            for i, url in enumerate(data['urls'], 1):
                print(f"  {i}. {url}")
        else:
            print("  Aucune URL trouvée")
        
        print(f"\n📝 TEXTE EXTRAIT ({len(data['text'])} caractères):")
        print("-" * 60)
        # Afficher les 500 premiers caractères
        text_preview = data['text'][:500]
        print(text_preview)
        if len(data['text']) > 500:
            print(f"\n... ({len(data['text']) - 500} caractères supplémentaires)")
        print("-" * 60)
        
        # Sauvegarder les résultats dans un fichier
        output_file = "scrape_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Résultats sauvegardés dans: {output_file}")
        
    else:
        print(f"\n❌ Erreur HTTP {response.status_code}")
        print(f"Détails: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("\n❌ Erreur: Impossible de se connecter à l'API")
    print("Vérifiez que l'API est bien lancée sur http://localhost:8000")
    
except requests.exceptions.Timeout:
    print("\n❌ Erreur: Timeout - La requête a pris trop de temps")
    
except Exception as e:
    print(f"\n❌ Erreur inattendue: {str(e)}")

print("\n" + "=" * 60)
