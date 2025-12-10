"""Utility functions for par_scrape."""


def chunk_list(items: list, chunk_size: int) -> list[list]:
    """
    Split a list into evenly sized chunks.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]


def safe_divide(a: float, b: float) -> float:
    """
    Divide two numbers safely, returning 0 if division by zero occurs.
    """
    try:
        return a / b
    except ZeroDivisionError:
        return 0.0


def merge_dicts(a: dict, b: dict) -> dict:
    """
    Merge two dictionaries, with b overwriting keys from a.
    """
    return {**a, **b}


def extract_urls_and_text(html: str, base_url: str) -> tuple[list[str], str]:
    """Extract all URLs and visible text from HTML content.

    This function parses HTML to extract:
    1. All URLs from <a href> tags (excluding javascript:, mailto:, tel:, and anchors)
    2. All visible text content with scripts and styles removed

    Args:
        html: HTML content to parse
        base_url: Base URL for resolving relative links

    Returns:
        Tuple of (list of absolute URLs, visible text as string)

    Example:
        >>> html = '<a href="/path">Link</a><p>Text</p>'
        >>> urls, text = extract_urls_and_text(html, "https://example.com")
        >>> urls
        ['https://example.com/path']
        >>> text
        'Link\\nText'
    """
    from urllib.parse import urljoin, urlparse

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")

    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()

    # Extract all URLs from href attributes
    urls = []
    for link in soup.find_all("a", href=True):
        href = str(link["href"])
        # Skip empty hrefs, anchors, javascript, mailto, and tel links
        if (
            not href
            or href.startswith("#")
            or href.startswith("javascript:")
            or href.startswith("mailto:")
            or href.startswith("tel:")
        ):
            continue

        # Convert relative URLs to absolute
        absolute_url = urljoin(base_url, href)

        # Parse the URL to validate it
        parsed = urlparse(absolute_url)
        if parsed.scheme in ["http", "https"]:
            urls.append(absolute_url)

    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    # Extract visible text
    text = soup.get_text(separator="\n", strip=True)

    # Clean up multiple newlines
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    clean_text = "\n".join(lines)

    return unique_urls, clean_text
