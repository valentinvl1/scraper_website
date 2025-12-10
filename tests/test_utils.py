import pytest

from par_scrape import utils


@pytest.mark.parametrize("items,chunk_size,expected", [
    ([1, 2, 3, 4], 2, [[1, 2], [3, 4]]),
    ([1, 2, 3], 1, [[1], [2], [3]]),
    ([], 3, []),
])
def test_chunk_list(items, chunk_size, expected):
    assert utils.chunk_list(items, chunk_size) == expected


def test_chunk_list_invalid_size():
    with pytest.raises(ValueError):
        utils.chunk_list([1, 2, 3], 0)


@pytest.mark.parametrize("a,b,expected", [
    (4, 2, 2.0),
    (1, 0, 0.0),
])
def test_safe_divide(a, b, expected):
    assert utils.safe_divide(a, b) == expected


def test_merge_dicts():
    a = {"a": 1, "b": 2}
    b = {"b": 3, "c": 4}
    result = utils.merge_dicts(a, b)
    assert result == {"a": 1, "b": 3, "c": 4}


def test_extract_urls_and_text_basic():
    """Test basic URL and text extraction."""
    html = """
    <html>
        <body>
            <h1>Test Page</h1>
            <p>This is a test paragraph with <a href="https://example.com">a link</a>.</p>
            <a href="/relative/path">Relative link</a>
        </body>
    </html>
    """
    base_url = "https://test.com"
    urls, text = utils.extract_urls_and_text(html, base_url)

    assert "https://example.com" in urls
    assert "https://test.com/relative/path" in urls
    assert "Test Page" in text
    assert "This is a test paragraph" in text


def test_extract_urls_and_text_filters_invalid():
    """Test that invalid URLs are filtered out."""
    html = """
    <html>
        <body>
            <a href="https://valid.com">Valid</a>
            <a href="javascript:void(0)">JavaScript</a>
            <a href="mailto:test@example.com">Email</a>
            <a href="tel:+1234567890">Phone</a>
            <a href="#anchor">Anchor</a>
        </body>
    </html>
    """
    base_url = "https://test.com"
    urls, text = utils.extract_urls_and_text(html, base_url)

    assert len(urls) == 1
    assert urls[0] == "https://valid.com"


def test_extract_urls_and_text_removes_scripts():
    """Test that script and style tags are removed from text."""
    html = """
    <html>
        <head>
            <style>body { color: red; }</style>
        </head>
        <body>
            <p>Visible text</p>
            <script>console.log("hidden");</script>
        </body>
    </html>
    """
    base_url = "https://test.com"
    urls, text = utils.extract_urls_and_text(html, base_url)

    assert "Visible text" in text
    assert "color: red" not in text
    assert "console.log" not in text


def test_extract_urls_and_text_deduplicates():
    """Test that duplicate URLs are removed."""
    html = """
    <html>
        <body>
            <a href="https://example.com">Link 1</a>
            <a href="https://example.com">Link 2</a>
            <a href="https://other.com">Link 3</a>
        </body>
    </html>
    """
    base_url = "https://test.com"
    urls, text = utils.extract_urls_and_text(html, base_url)

    assert len(urls) == 2
    assert "https://example.com" in urls
    assert "https://other.com" in urls


def test_extract_urls_and_text_empty_html():
    """Test extraction from empty HTML."""
    html = "<html><body></body></html>"
    base_url = "https://test.com"
    urls, text = utils.extract_urls_and_text(html, base_url)

    assert urls == []
    assert text == ""


def test_extract_urls_and_text_cleans_whitespace():
    """Test that excessive whitespace is cleaned up."""
    html = """
    <html>
        <body>
            <p>Line 1</p>


            <p>Line 2</p>
        </body>
    </html>
    """
    base_url = "https://test.com"
    urls, text = utils.extract_urls_and_text(html, base_url)

    lines = text.split("\n")
    assert len(lines) == 2
    assert lines[0] == "Line 1"
    assert lines[1] == "Line 2"
