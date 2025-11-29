# PAR Scrape API Documentation

REST API for web scraping with support for Playwright and Selenium, returning clean markdown content.

## Quick Start

### Local Development

```bash
# Install dependencies
uv sync

# Run the API server
uv run par_scrape_api

# With custom port
PORT=8001 uv run par_scrape_api

# With auto-reload for development
RELOAD=true uv run par_scrape_api
```

The API will be available at `http://localhost:8000`

### Using Docker (Optional)

```bash
# Build
docker build -t par-scrape-api .

# Run
docker run -p 8000:8000 par-scrape-api
```

## API Endpoints

### GET `/` - API Information

Returns information about the API and available endpoints.

**Response:**
```json
{
  "name": "PAR Scrape",
  "version": "0.8.3",
  "description": "Web scraping API with support for Playwright and Selenium",
  "docs": "/docs",
  "endpoints": {
    "scrape": {
      "method": "POST",
      "path": "/scrape",
      "description": "Scrape a URL and return markdown"
    },
    "health": {
      "method": "GET",
      "path": "/health",
      "description": "Health check endpoint"
    }
  }
}
```

### GET `/health` - Health Check

Health check endpoint for monitoring and deployment platforms like Railway.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-29T14:27:01.123456",
  "version": "0.8.3"
}
```

### POST `/scrape` - Scrape URL

Scrape a web page and return the content as markdown.

**Request Body:**
```json
{
  "url": "https://example.com",
  "fetch_using": "playwright",
  "sleep_time": 2,
  "timeout": 10,
  "headless": true,
  "wait_type": "sleep",
  "wait_selector": null,
  "include_images": true
}
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | string | Yes | - | URL to scrape (must start with http:// or https://) |
| `fetch_using` | string | No | `"playwright"` | Scraper to use: `"playwright"` or `"selenium"` |
| `sleep_time` | integer | No | `2` | Time to wait before scraping (0-30 seconds) |
| `timeout` | integer | No | `10` | Request timeout (1-60 seconds) |
| `headless` | boolean | No | `true` | Run browser in headless mode |
| `wait_type` | string | No | `"sleep"` | Wait strategy: `"sleep"`, `"idle"`, `"none"`, `"selector"`, `"text"` |
| `wait_selector` | string | No | `null` | CSS selector or text to wait for (required for `"selector"` or `"text"` wait_type) |
| `include_images` | boolean | No | `true` | Include images in markdown output |

**Success Response (200):**
```json
{
  "url": "https://example.com",
  "markdown": "# Example Domain\n\nThis domain is for use in...",
  "fetch_using": "playwright",
  "processing_time": 3.45
}
```

**Error Responses:**

| Status Code | Description |
|-------------|-------------|
| 400 | Invalid URL or missing required parameters |
| 502 | Network error (connection failed, DNS error, etc.) |
| 504 | Scraping timeout |
| 500 | Internal server error (parsing error, unexpected error) |

**Error Response Example:**
```json
{
  "detail": "Invalid URL: example.com. URL must start with http:// or https://"
}
```

## Usage Examples

### Basic Scraping

```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.maisoncerezy.fr/"}'
```

### With Custom Configuration

```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "fetch_using": "selenium",
    "sleep_time": 5,
    "timeout": 15,
    "headless": false,
    "wait_type": "idle",
    "include_images": false
  }'
```

### Wait for Specific Selector

```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "wait_type": "selector",
    "wait_selector": "#main-content"
  }'
```

### Python Client Example

```python
import requests

response = requests.post(
    "http://localhost:8000/scrape",
    json={
        "url": "https://www.maisoncerezy.fr/",
        "fetch_using": "playwright",
        "sleep_time": 2,
        "timeout": 10,
        "headless": True,
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"Scraped {data['url']} in {data['processing_time']:.2f}s")
    print(data['markdown'])
else:
    print(f"Error: {response.json()}")
```

### JavaScript/Node.js Client Example

```javascript
const response = await fetch('http://localhost:8000/scrape', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    url: 'https://www.maisoncerezy.fr/',
    fetch_using: 'playwright',
    sleep_time: 2,
    timeout: 10,
    headless: true
  })
});

const data = await response.json();
console.log(`Scraped ${data.url} in ${data.processing_time}s`);
console.log(data.markdown);
```

## Interactive Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

These interfaces allow you to test the API directly from your browser.

## Deployment

### Railway

1. Install Railway CLI:
```bash
npm i -g @railway/cli
```

2. Login and initialize:
```bash
railway login
railway init
```

3. Deploy:
```bash
railway up
```

Railway will automatically:
- Detect the `railway.toml` configuration
- Install dependencies with `uv`
- Run health checks on `/health`
- Restart on failure (up to 3 times)

### Environment Variables on Railway

Railway automatically sets `PORT`. No additional configuration needed!

Optional variables:
- `HOST`: Bind address (default: `0.0.0.0`)
- `RELOAD`: Enable auto-reload (default: `false`)

### Other Platforms

The API can be deployed on any platform that supports Python ASGI applications:

- **Heroku**: Use `Procfile` with `web: uv run par_scrape_api`
- **Render**: Use start command `uv run par_scrape_api`
- **Fly.io**: Configure with `fly.toml`
- **AWS/GCP/Azure**: Use container deployment with uvicorn

## Testing

Run the test suite:

```bash
# All tests
uv run pytest

# API tests only
uv run pytest tests/test_api.py

# With coverage
uv run pytest --cov=par_scrape tests/test_api.py
```

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Edit `.env`:
```env
HOST=0.0.0.0
PORT=8000
RELOAD=true  # Enable for development
```

### Wait Types Explained

- **`sleep`** (default): Wait for a fixed duration (uses `sleep_time`)
- **`idle`**: Wait until network is idle (no pending requests)
- **`none`**: No waiting, scrape immediately after page load
- **`selector`**: Wait for a CSS selector to appear (requires `wait_selector`)
- **`text`**: Wait for specific text to appear (requires `wait_selector`)

## Performance Considerations

- **Timeout**: Increase for slow-loading pages (max 60s)
- **Sleep Time**: Increase for JavaScript-heavy sites (max 30s)
- **Headless Mode**: Keep `true` for production (faster, less resources)
- **Playwright vs Selenium**: Playwright is generally faster and more reliable

## Troubleshooting

### API Returns Empty Markdown

- Increase `sleep_time` to allow page to fully load
- Try `wait_type: "idle"` to wait for network requests
- Check if site requires specific `wait_selector`

### Timeout Errors

- Increase `timeout` parameter
- Check if URL is accessible
- Verify network connectivity

### Connection Refused

- Ensure API server is running
- Check port is not in use
- Verify firewall settings

### Playwright/Selenium Errors

Make sure browsers are installed:
```bash
# Playwright
uv run playwright install

# Selenium (uses webdriver-manager, auto-installs)
```

## Rate Limiting

Currently, there is no built-in rate limiting. For production use, consider:

- Adding rate limiting middleware (e.g., `slowapi`)
- Using a reverse proxy with rate limiting (e.g., nginx, Caddy)
- Implementing token-based authentication

## Security

- The API does not require authentication by default
- For production, add authentication (API keys, JWT, etc.)
- Be cautious about allowing arbitrary URL scraping (potential SSRF)
- Consider whitelisting allowed domains

## Support

- **GitHub Issues**: [Report bugs](https://github.com/paulrobello/par_scrape/issues)
- **Documentation**: [Main README](README.md)
- **CLI Tool**: See main README for CLI usage

## License

MIT License - see [LICENSE](LICENSE) file for details.
