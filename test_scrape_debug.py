"""Script de diagnostic pour tester le scraping du site acupuncture-lyon-trinh.fr"""

from par_ai_core.web_tools import fetch_url, html_to_markdown
from bs4 import BeautifulSoup
import time

url = "https://www.acupuncture-lyon-trinh.fr/"

print("=" * 80)
print("DIAGNOSTIC DE SCRAPING - acupuncture-lyon-trinh.fr")
print("=" * 80)

def test_configuration(fetch_using, sleep_time, wait_type, headless, test_name):
    """Test une configuration spécifique"""
    print(f"\n{'=' * 80}")
    print(f"TEST: {test_name}")
    print(f"{'=' * 80}")
    print(f"Configuration:")
    print(f"  - fetch_using: {fetch_using}")
    print(f"  - sleep_time: {sleep_time}s")
    print(f"  - wait_type: {wait_type}")
    print(f"  - headless: {headless}")
    print(f"  - timeout: 15s")
    print()

    try:
        start_time = time.time()

        # Fetch HTML
        print("🔄 Fetching HTML...")
        html_list = fetch_url(
            url,
            fetch_using=fetch_using,
            sleep_time=sleep_time,
            timeout=15,
            headless=headless,
            wait_type=wait_type,
            verbose=False
        )

        fetch_time = time.time() - start_time
        print(f"✅ Fetch completed in {fetch_time:.2f}s")

        if not html_list or not html_list[0]:
            print("❌ ERROR: No HTML fetched!")
            return False

        html = html_list[0]
        print(f"📄 HTML length: {len(html):,} chars")

        # Analyze HTML structure
        soup = BeautifulSoup(html, 'html.parser')

        print(f"\n📊 HTML Structure:")
        print(f"  - <script> tags: {len(soup.find_all('script'))}")
        print(f"  - <style> tags: {len(soup.find_all('style'))}")
        print(f"  - <div> tags: {len(soup.find_all('div'))}")
        print(f"  - <p> tags: {len(soup.find_all('p'))}")
        print(f"  - <h1>-<h6> tags: {len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))}")
        print(f"  - <img> tags: {len(soup.find_all('img'))}")
        print(f"  - <a> tags: {len(soup.find_all('a'))}")

        # Extract visible text
        soup_copy = BeautifulSoup(html, 'html.parser')
        for script in soup_copy(["script", "style"]):
            script.decompose()
        text = soup_copy.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        clean_text = '\n'.join(lines)

        print(f"\n📝 Extracted Text:")
        print(f"  - Length: {len(clean_text):,} chars")
        print(f"  - Number of lines: {len(lines)}")

        if len(clean_text) > 0:
            print(f"\n  First 300 chars:")
            print(f"  {'-' * 76}")
            preview = clean_text[:300].replace('\n', '\n  ')
            print(f"  {preview}")
            print(f"  {'-' * 76}")

        # Convert to markdown
        print(f"\n📄 Markdown Conversion:")
        markdown = html_to_markdown(html, url=url, include_images=True)

        if markdown and markdown.strip():
            print(f"  ✅ Success! Markdown length: {len(markdown):,} chars")
            print(f"\n  First 300 chars:")
            print(f"  {'-' * 76}")
            preview = markdown[:300].replace('\n', '\n  ')
            print(f"  {preview}")
            print(f"  {'-' * 76}")
            return True
        else:
            print(f"  ❌ FAILED: Markdown is empty!")
            return False

    except Exception as e:
        print(f"\n❌ EXCEPTION: {type(e).__name__}: {str(e)}")
        return False


# Run tests
results = {}

# Test 1: Paramètres originaux (reproduire l'erreur)
results['test1'] = test_configuration(
    fetch_using="selenium",
    sleep_time=2,
    wait_type="sleep",
    headless=True,
    test_name="Test 1 - Paramètres originaux (sleep=2s, wait_type=sleep)"
)

# Test 2: Augmenter sleep_time
results['test2'] = test_configuration(
    fetch_using="selenium",
    sleep_time=5,
    wait_type="sleep",
    headless=True,
    test_name="Test 2 - Sleep augmenté (sleep=5s, wait_type=sleep)"
)

# Test 3: Utiliser wait_type="idle"
results['test3'] = test_configuration(
    fetch_using="selenium",
    sleep_time=5,
    wait_type="idle",
    headless=True,
    test_name="Test 3 - Wait idle (sleep=5s, wait_type=idle)"
)

# Test 4: Playwright au lieu de Selenium
results['test4'] = test_configuration(
    fetch_using="playwright",
    sleep_time=5,
    wait_type="idle",
    headless=True,
    test_name="Test 4 - Playwright (sleep=5s, wait_type=idle)"
)

# Test 5: Mode non-headless avec Selenium
results['test5'] = test_configuration(
    fetch_using="selenium",
    sleep_time=5,
    wait_type="idle",
    headless=False,
    test_name="Test 5 - Non-headless (sleep=5s, wait_type=idle, headless=False)"
)

# Summary
print(f"\n{'=' * 80}")
print("RÉSUMÉ DES TESTS")
print(f"{'=' * 80}")
print()

for test_name, success in results.items():
    status = "✅ SUCCESS" if success else "❌ FAILED"
    print(f"{test_name}: {status}")

print()
successful_tests = [name for name, success in results.items() if success]
if successful_tests:
    print(f"✅ {len(successful_tests)} test(s) réussi(s): {', '.join(successful_tests)}")
    print()
    print("RECOMMANDATION: Utiliser la configuration du premier test réussi")
else:
    print("❌ Aucun test n'a réussi!")
    print()
    print("CAUSE PROBABLE:")
    print("  - Le site utilise une protection anti-bot avancée")
    print("  - Le site nécessite une authentification")
    print("  - Le site détecte et bloque les scrapers")
    print("  - Le contenu est chargé via un mécanisme non-standard")

print(f"{'=' * 80}")
