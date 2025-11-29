# Exemple d'utilisation de l'API PAR Scrape

## Nouveau format de sortie

L'API a été modifiée pour retourner les URLs et le texte visible de la page au lieu du markdown.

### Requête

```bash
curl -X POST "http://localhost:8000/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "fetch_using": "selenium",
    "sleep_time": 2,
    "headless": true,
    "wait_type": "sleep"
  }'
```

### Réponse

```json
{
  "url": "https://example.com",
  "urls": [
    "https://www.iana.org/domains/example",
    "https://www.iana.org/help/example-domains"
  ],
  "text": "Example Domain\nThis domain is for use in illustrative examples in documents. You may use this domain in literature without prior coordination or asking for permission.\nMore information...",
  "fetch_using": "selenium",
  "processing_time": 2.5
}
```

## Champs de la réponse

- **url** (string): L'URL qui a été scrapée
- **urls** (array[string]): Liste de toutes les URLs trouvées sur la page (liens href, excluant les images, ancres, javascript:, mailto:)
- **text** (string): Tout le texte visible de la page (sans les scripts, styles, etc.)
- **fetch_using** (string): Le scraper utilisé (selenium ou playwright)
- **processing_time** (float): Temps de traitement en secondes

## Changements par rapport à l'ancienne version

### ❌ Supprimé
- Champ `markdown` dans la réponse
- Paramètre `include_images` dans la requête
- Extraction des images
- Extraction des URLs de fichiers SVG
- Meta descriptions des images

### ✅ Ajouté
- Champ `urls`: Liste de toutes les URLs de la page (href uniquement)
- Champ `text`: Tout le texte visible à l'écran
- Filtrage automatique des URLs non-HTTP/HTTPS
- Conversion automatique des URLs relatives en absolues
- Suppression des doublons dans la liste des URLs

## Utilisation avec Python

```python
import requests

response = requests.post(
    "http://localhost:8000/scrape",
    json={
        "url": "https://example.com",
        "fetch_using": "selenium",
        "sleep_time": 2,
        "headless": True
    }
)

data = response.json()

print(f"Page scrapée: {data['url']}")
print(f"\nNombre d'URLs trouvées: {len(data['urls'])}")
print("\nURLs:")
for url in data['urls']:
    print(f"  - {url}")

print(f"\nTexte de la page ({len(data['text'])} caractères):")
print(data['text'][:500] + "..." if len(data['text']) > 500 else data['text'])
```
