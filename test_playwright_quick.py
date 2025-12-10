"""Quick test to verify Playwright works with the site"""

from par_ai_core.web_tools import fetch_url, html_to_markdown

url = "https://www.acupuncture-lyon-trinh.fr/"

print("Testing Playwright with acupuncture-lyon-trinh.fr...")
print("=" * 60)

try:
    # Fetch with Playwright (default now)
    html_list = fetch_url(
        url,
        fetch_using="playwright",
        sleep_time=2,
        timeout=10,
        headless=True,
        wait_type="sleep",
        verbose=False
    )

    if not html_list or not html_list[0]:
        print("❌ FAILED: No HTML fetched")
        exit(1)

    html = html_list[0]
    print(f"✅ HTML fetched: {len(html):,} chars")

    # Convert to markdown
    markdown = html_to_markdown(html, url=url, include_images=True)

    if not markdown or not markdown.strip():
        print("❌ FAILED: Markdown is empty")
        exit(1)

    print(f"✅ Markdown generated: {len(markdown):,} chars")
    print(f"\nFirst 200 chars:")
    print("-" * 60)
    print(markdown[:200])
    print("-" * 60)
    print("\n✅ SUCCESS! Playwright works perfectly!")

except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {str(e)}")
    exit(1)
