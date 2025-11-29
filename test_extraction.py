"""Test script for URL and text extraction."""

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def extract_urls_and_text(html: str, base_url: str) -> tuple[list[str], str]:
    """Extract all URLs and visible text from HTML content.

    Args:
        html: HTML content to parse
        base_url: Base URL for resolving relative links

    Returns:
        Tuple of (list of URLs, visible text)
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Extract all URLs from href attributes, excluding images
    urls = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        # Skip empty hrefs, anchors, javascript, and mailto links
        if not href or href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
            continue
        
        # Convert relative URLs to absolute
        absolute_url = urljoin(base_url, href)
        
        # Parse the URL to validate it
        parsed = urlparse(absolute_url)
        if parsed.scheme in ['http', 'https']:
            urls.append(absolute_url)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    
    # Extract visible text
    text = soup.get_text(separator='\n', strip=True)
    
    # Clean up multiple newlines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    clean_text = '\n'.join(lines)
    
    return unique_urls, clean_text


# Test with a simple HTML example
test_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
    <style>
        body { font-family: Arial; }
    </style>
</head>
<body>
    <h1>Welcome to Test Page</h1>
    <p>This is a test paragraph with <a href="https://example.com">a link</a>.</p>
    <p>Here's another paragraph with <a href="/relative/path">a relative link</a>.</p>
    <ul>
        <li><a href="https://google.com">Google</a></li>
        <li><a href="https://github.com">GitHub</a></li>
        <li><a href="#anchor">Anchor link (should be ignored)</a></li>
        <li><a href="javascript:void(0)">JavaScript link (should be ignored)</a></li>
        <li><a href="mailto:test@example.com">Email link (should be ignored)</a></li>
    </ul>
    <img src="image.jpg" alt="Test image">
    <script>
        console.log("This script should be removed");
    </script>
</body>
</html>
"""

base_url = "https://test.com/page"
urls, text = extract_urls_and_text(test_html, base_url)

print("=== EXTRACTED URLs ===")
for i, url in enumerate(urls, 1):
    print(f"{i}. {url}")

print("\n=== EXTRACTED TEXT ===")
print(text)

print("\n=== SUMMARY ===")
print(f"Total URLs found: {len(urls)}")
print(f"Text length: {len(text)} characters")
