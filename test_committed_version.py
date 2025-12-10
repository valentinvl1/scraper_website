"""Test de la version committée (déployée) avec extract_urls_and_text"""

from par_ai_core.web_tools import fetch_url
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

url = "https://www.acupuncture-lyon-trinh.fr/"

print("=" * 80)
print("TEST DE LA VERSION COMMITTÉE (celle sur Railway)")
print("=" * 80)

# Fetch HTML
print(f"\n🔄 Fetching HTML from {url}...")
html_list = fetch_url(
    url,
    fetch_using="selenium",
    sleep_time=2,
    timeout=10,
    headless=True,
    wait_type="sleep",
    verbose=False
)

if not html_list or not html_list[0]:
    print("❌ No HTML fetched!")
    exit(1)

html = html_list[0]
print(f"✅ HTML fetched: {len(html):,} chars")

# Extract URLs and text (version committée)
def extract_urls_and_text(html: str, base_url: str) -> tuple[list[str], str]:
    """Extract all URLs and visible text from HTML content."""
    soup = BeautifulSoup(html, 'html.parser')

    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()

    # Extract all URLs from href attributes
    urls = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if not href or href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
            continue

        absolute_url = urljoin(base_url, href)
        parsed = urlparse(absolute_url)
        if parsed.scheme in ['http', 'https']:
            urls.append(absolute_url)

    # Remove duplicates
    seen = set()
    unique_urls = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    # Extract visible text
    text = soup.get_text(separator='\n', strip=True)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    clean_text = '\n'.join(lines)

    return unique_urls, clean_text

print(f"\n🔍 Extracting URLs and text...")
urls, text = extract_urls_and_text(html, url)

print(f"\n📊 Résultats:")
print(f"  - URLs found: {len(urls)}")
print(f"  - Text length: {len(text):,} chars")

if not text or not text.strip():
    print("\n❌ ERREUR REPRODUITE ! Text is empty!")
    print("C'est exactement l'erreur que vous voyez sur Railway!")
else:
    print(f"\n✅ Text extrait avec succès")
    print(f"\nFirst 300 chars:")
    print("-" * 80)
    print(text[:300])
    print("-" * 80)

print("\n" + "=" * 80)
print("CONCLUSION:")
if not text or not text.strip():
    print("❌ La version committée (Railway) a un BUG!")
    print("   La fonction extract_urls_and_text() retourne du texte vide.")
else:
    print("✅ La version committée fonctionne correctement.")
    print("   Le problème doit être ailleurs...")
print("=" * 80)
