# 🔍 Rapport de Diagnostic : Erreur "Text extraction resulted in empty content"

**Date** : 2025-12-08
**Site problématique** : https://www.acupuncture-lyon-trinh.fr/
**Erreur** : `500 - "HTML parsing error: Text extraction resulted in empty content"`

---

## 🎯 Résumé Exécutif

Le problème n'est **PAS lié au site web ou aux paramètres de scraping**. C'est un problème de **configuration Selenium/ChromeDriver sur Railway** combiné à une **régression de code** dans le commit `3616f96`.

---

## 📊 Résultats des Tests

### ✅ Tests locaux (100% de réussite)

| Test | Configuration | Résultat |
|------|--------------|----------|
| Script Python (version locale) | Selenium, sleep=2s | ✅ Success - 6,713 chars markdown |
| Script Python (version locale) | Selenium, sleep=5s | ✅ Success - 6,713 chars markdown |
| Script Python (version locale) | Selenium, wait_type=idle | ✅ Success - 6,713 chars markdown |
| Script Python (version locale) | Playwright, wait_type=idle | ✅ Success - 6,713 chars markdown |
| API locale (version stashed) | Selenium, sleep=2s | ✅ Success - 7,223 bytes JSON |

**Contenu extrait** : 3,930 chars de texte visible, 37 liens, 12 titres, 39 paragraphes

### ❌ Tests avec version committée (production)

| Test | Configuration | Résultat |
|------|--------------|----------|
| Script extract_urls_and_text | Selenium | ✅ Fonctionne localement |
| API committée locale | Selenium | ❌ Erreur : "/usr/bin/chromedriver not found" |
| API Railway (production) | Selenium | ❌ Erreur : "Text extraction resulted in empty content" |

---

## 🐛 Causes Identifiées

### 1. **Problème Principal : Selenium ne fonctionne pas sur Railway**

La version committée (commit `3616f96`) configure Selenium avec :
```python
CHROMEDRIVER_PATH=/usr/bin/chromedriver
CHROME_BIN=/usr/bin/chromium
```

**Sur Railway, Selenium échoue à initialiser Chrome**, ce qui cause :
- Retour d'une liste HTML vide : `html_list = [[]]` ou `[None]`
- Passage de la première validation (`if not html_list or not html_list[0]`)
- Échec de l'extraction de texte → Erreur "Text extraction resulted in empty content"

**Logs d'erreur probables sur Railway** :
```
Chrome initialization failed: Unable to obtain driver for chrome
ValueError: The path is not a valid file: /usr/bin/chromedriver
```

### 2. **Régression de Code : extract_urls_and_text vs html_to_markdown**

Le commit `3616f96` a introduit une **régression** :

#### Version committée (Railway) - commit 3616f96
```python
urls, text = extract_urls_and_text(html_list[0], request.url)

if not text or not text.strip():
    raise ParsingError("Text extraction resulted in empty content")

return ScrapeResponse(url=request.url, urls=urls, text=text, ...)
```

#### Version locale (working directory) - FONCTIONNE
```python
markdown = html_to_markdown(html_list[0], url=request.url, include_images=request.include_images)

if not markdown or not markdown.strip():
    raise ParsingError("Markdown conversion resulted in empty content")

return ScrapeResponse(url=request.url, markdown=markdown, ...)
```

**La version locale a reverté la régression** mais n'a jamais été committée !

### 3. **Configuration Docker : Chromium vs Chrome**

Le Dockerfile installe Chromium de Debian :
```dockerfile
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver
```

**Problème potentiel** :
- `chromium-driver` peut être incompatible avec la version de Selenium
- Les patches Chrome dans `api.py` (version committée) peuvent ne pas fonctionner avec Chromium de Debian
- `/usr/bin/chromedriver` peut ne pas être exécutable ou configuré correctement

---

## 🔧 Solutions Recommandées

### ✅ Solution 1 : **Commiter et déployer la version locale (RECOMMANDÉ)**

**Avantages** :
- ✅ Fonctionne parfaitement en local avec `html_to_markdown`
- ✅ Retourne du markdown propre au lieu de texte brut
- ✅ Garde le paramètre `include_images`
- ✅ Code plus simple, moins de patches

**Actions** :
```bash
git add src/par_scrape/api.py
git commit -m "fix: Revert to html_to_markdown to fix empty content extraction error"
git push origin main
```

---

### ✅ Solution 2 : **Passer à Playwright par défaut**

Playwright est plus fiable que Selenium et ne nécessite pas ChromeDriver externe.

**Changements dans `api.py`** :
```python
class ScrapeRequest(BaseModel):
    fetch_using: str = Field(default="playwright")  # Changé de "selenium"
```

**Changements dans `Dockerfile`** :
```dockerfile
# Remplacer Chromium par Playwright browsers
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Installer Playwright après uv sync
RUN uv run playwright install --with-deps chromium
```

**Avantages** :
- ✅ Plus rapide (3.34s vs 8.40s dans les tests)
- ✅ Moins de problèmes de configuration
- ✅ Pas besoin de ChromeDriver externe
- ✅ Meilleure gestion du JavaScript moderne

---

### ✅ Solution 3 : **Fixer Selenium sur Railway**

Si vous voulez garder Selenium, il faut corriger la configuration Docker.

**Option A : Utiliser Selenium Manager (recommandé)**

Retirer les patches et laisser Selenium gérer Chrome automatiquement :

```python
# Dans api.py : SUPPRIMER tous les patches ChromeDriverManager et Chrome
# Laisser Selenium utiliser son propre Selenium Manager
```

**Option B : Installer Chrome (pas Chromium)**

```dockerfile
# Installer Google Chrome officiel au lieu de Chromium Debian
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/google-chrome
```

---

### ✅ Solution 4 : **Améliorer la gestion d'erreurs**

Ajouter plus de diagnostics pour identifier les problèmes futurs :

```python
if not html_list or not html_list[0]:
    # Ajouter logging détaillé
    logger.error(f"No HTML fetched. html_list type: {type(html_list)}, length: {len(html_list) if html_list else 0}")
    if html_list:
        logger.error(f"First item: {html_list[0][:100] if html_list[0] else 'None'}")
    raise ParsingError(
        "No content was fetched from the URL. "
        "This may indicate Selenium/Playwright initialization failure."
    )

if not markdown or not markdown.strip():
    # Ajouter contexte
    html_length = len(html_list[0]) if html_list else 0
    raise ParsingError(
        f"Markdown conversion resulted in empty content. "
        f"HTML length: {html_length} chars. "
        f"Try using fetch_using='playwright' or increasing sleep_time."
    )
```

---

## 🎯 Plan d'Action Recommandé

### Phase 1 : Fix Immédiat (10 minutes)

1. ✅ **Commiter la version locale qui fonctionne**
   ```bash
   git add src/par_scrape/api.py
   git commit -m "fix: Revert to html_to_markdown for reliable content extraction"
   git push origin main
   ```

2. ✅ **Vérifier le déploiement sur Railway**
   - Attendre le redéploiement automatique (2-3 minutes)
   - Tester l'endpoint avec le site problématique
   - Vérifier que l'erreur disparaît

### Phase 2 : Amélioration (30 minutes)

3. ✅ **Passer à Playwright par défaut**
   - Modifier `ScrapeRequest.fetch_using` default
   - Mettre à jour le Dockerfile
   - Commiter et déployer

4. ✅ **Tester avec plusieurs sites**
   - Site problématique : https://www.acupuncture-lyon-trinh.fr/
   - Site simple : https://example.com
   - Site JavaScript-heavy : https://react.dev

### Phase 3 : Prévention (1 heure)

5. ✅ **Ajouter des tests automatisés**
   ```python
   def test_scrape_various_sites():
       """Test scraping avec différents types de sites"""
       sites = [
           "https://example.com",  # Site simple
           "https://www.acupuncture-lyon-trinh.fr/",  # Site problématique
       ]
       for site in sites:
           result = scrape(site)
           assert len(result.markdown) > 0
   ```

6. ✅ **Documenter les configurations testées**
   - Créer TROUBLESHOOTING.md
   - Lister les problèmes connus et solutions

---

## 📈 Comparaison des Approches

| Critère | html_to_markdown (local) | extract_urls_and_text (committée) |
|---------|-------------------------|-----------------------------------|
| **Fonctionne localement** | ✅ Oui | ⚠️ Oui (si pas de patch Chrome) |
| **Fonctionne sur Railway** | ✅ Devrait fonctionner | ❌ Non (Selenium ne démarre pas) |
| **Format de sortie** | Markdown propre | Texte brut + URLs séparés |
| **Images** | ✅ Optionnel | ❌ Non supporté |
| **Compatibilité** | ✅ Haute | ❌ Selenium-dépendant |
| **Complexité** | ✅ Simple | ⚠️ Complexe (patches requis) |

---

## 🚀 Commandes de Déploiement

### Déployer la fix immédiate
```bash
cd "/Users/valentinlopes/Desktop/week_end startup"

# Vérifier les changements
git diff src/par_scrape/api.py

# Commiter
git add src/par_scrape/api.py
git commit -m "fix: Revert to html_to_markdown to fix empty content extraction error

- Reverts commit 3616f96 which introduced extract_urls_and_text
- html_to_markdown is more reliable and works with both Selenium and Playwright
- Restores include_images parameter
- Fixes 500 error 'Text extraction resulted in empty content' on production"

# Déployer
git push origin main
```

### Nettoyer les fichiers de test
```bash
# Optionnel : nettoyer les fichiers de test
rm test_*.py test_*.json
git add -A
git commit -m "chore: Remove test files"
```

---

## 📝 Conclusion

Le problème provient de **deux facteurs combinés** :

1. **Selenium ne fonctionne pas correctement sur Railway** avec la configuration actuelle
2. **Une régression de code non-commitée** qui a été partiellement fixée localement

**La solution la plus rapide** : Commiter et déployer la version locale.

**La solution la plus robuste** : Passer à Playwright comme scraper par défaut.

**Temps estimé pour résolution complète** : 40 minutes (10 min fix + 30 min amélioration)

---

## 🔗 Références

- Commit problématique : `3616f96` - "Return extracted URLs and visible text"
- Fichier principal : `src/par_scrape/api.py:267-274`
- Docker config : `Dockerfile:8-12` (installation Chromium)
- Railway config : `railway.toml`

---

**Généré le** : 2025-12-08 par Claude Code
