"""FastAPI application for web scraping.

This module provides a RESTful API for web scraping using Playwright or Selenium,
returning clean markdown content from web pages.
"""

import time
from datetime import datetime
from typing import Literal
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import logging
import sys

# Configure logging to stdout
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("par_scrape_api")

from par_ai_core.par_logging import console_out
from par_ai_core.web_tools import ScraperWaitType, fetch_url, html_to_markdown
from pydantic import BaseModel, Field

from par_scrape import __application_title__, __version__

# Monkey-patch ChromeDriverManager to use system ChromeDriver
def _patch_chromedriver_manager():
    """Patch ChromeDriverManager to always return system ChromeDriver path."""
    logger.info("Starting ChromeDriverManager patch")
    try:
        import os
        from webdriver_manager.chrome import ChromeDriverManager
        
        original_install = ChromeDriverManager.install
        
        def patched_install(self):
            chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
            logger.info(f"ChromeDriverManager.install() patched to return: {chromedriver_path}")
            return chromedriver_path
        
        ChromeDriverManager.install = patched_install
        logger.info("ChromeDriverManager successfully patched")
    except ImportError:
        logger.warning("webdriver-manager not available, skipping ChromeDriverManager patch")
    except Exception as e:
        logger.error(f"Failed to patch ChromeDriverManager: {str(e)}", exc_info=True)

# Apply ChromeDriverManager patch first
logger.info("Applying ChromeDriverManager patch at module import")
_patch_chromedriver_manager()

# Monkey-patch Selenium Chrome for Docker compatibility
def _patch_selenium_chrome():
    """Patch selenium.webdriver.Chrome to add --no-sandbox flag for Docker compatibility."""
    logger.info("Starting Selenium Chrome patch for Docker compatibility")
    try:
        logger.debug("Importing selenium and webdriver modules")
        import os
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service

        original_init = webdriver.Chrome.__init__

        def patched_init(self, *args, **kwargs):
            logger.info("Chrome initialization called with patched init")
            console_out.print("[magenta]DEBUG: Entering patched webdriver.Chrome.__init__[/magenta]")
            logger.debug(f"Chrome init args: {args}")
            logger.debug(f"Chrome init kwargs: {list(kwargs.keys())}")
            
            # Set up ChromeDriver service with explicit path
            chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
            logger.info(f"Using ChromeDriver path: {chromedriver_path}")
            
            if 'service' not in kwargs:
                kwargs['service'] = Service(executable_path=chromedriver_path)
                logger.info(f"Created Service with executable_path: {chromedriver_path}")
            
            # Ensure options are provided and add --no-sandbox for Docker
            if 'options' not in kwargs:
                kwargs['options'] = Options()

            options = kwargs['options']
            if isinstance(options, Options):
                # Add essential flags for Docker
                existing_args = options.arguments if hasattr(options, 'arguments') else []
                essential_flags = ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']

                for flag in essential_flags:
                    if flag not in existing_args:
                        options.add_argument(flag)
                        console_out.print(f"[yellow]Added Chrome flag for Docker: {flag}[/yellow]")

                # Set binary location if CHROME_BIN is present
                chrome_bin = os.environ.get("CHROME_BIN")
                logger.info(f"CHROME_BIN environment variable: {chrome_bin}")
                console_out.print(f"[magenta]DEBUG: CHROME_BIN env var: {chrome_bin}[/magenta]")
                if chrome_bin:
                    options.binary_location = chrome_bin
                    logger.info(f"Set Chrome binary location to: {chrome_bin}")
                    console_out.print(f"[yellow]Set Chrome binary location to: {chrome_bin}[/yellow]")
                else:
                    logger.warning("CHROME_BIN not set, using default binary location")
                    console_out.print("[magenta]DEBUG: CHROME_BIN not set, using default binary location[/magenta]")

                if hasattr(options, 'arguments'):
                     logger.debug(f"Chrome arguments: {options.arguments}")
                     console_out.print(f"[magenta]DEBUG: Chrome arguments: {options.arguments}[/magenta]")
                if hasattr(options, 'binary_location'):
                     logger.debug(f"Chrome binary_location: {options.binary_location}")
                     console_out.print(f"[magenta]DEBUG: Chrome binary_location: {options.binary_location}[/magenta]")

            try:
                logger.info("Calling original Chrome.__init__")
                result = original_init(self, *args, **kwargs)
                logger.info("Chrome initialization successful")
                return result
            except Exception as e:
                logger.error(f"Chrome initialization failed: {str(e)}", exc_info=True)
                console_out.print(f"[bold red]Chrome initialization failed: {str(e)}[/bold red]")
                # Print the full command that was attempted
                if hasattr(options, 'arguments'):
                    logger.error(f"Failed Chrome arguments: {' '.join(options.arguments)}")
                    console_out.print(f"[bold red]Chrome arguments: {' '.join(options.arguments)}[/bold red]")
                raise e

        webdriver.Chrome.__init__ = patched_init
        logger.info("Selenium Chrome successfully patched for Docker compatibility")
        console_out.print("[green]Selenium Chrome patched for Docker compatibility[/green]")

    except ImportError:
        logger.warning("Selenium not available, skipping Chrome patch")
        console_out.print("[yellow]Selenium not available, skipping Chrome patch[/yellow]")
    except Exception as e:
        logger.error(f"Failed to patch Selenium Chrome: {str(e)}", exc_info=True)
        console_out.print(f"[bold red]Failed to patch Selenium Chrome: {str(e)}[/bold red]")

# Apply the patch at module import time
logger.info("Applying Selenium Chrome patch at module import")
_patch_selenium_chrome()
logger.info("Module initialization complete")

# Initialize FastAPI app
app = FastAPI(
    title="PAR Scrape API",
    description="Web scraping API with support for Playwright and Selenium",
    version=__version__,
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Incoming request: {request.method} {request.url}")
    try:
        body = await request.body()
        logger.debug(f"Request body: {body.decode()}")
    except Exception as e:
        logger.error(f"Could not read request body: {e}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"Request completed: {request.method} {request.url} - Status: {response.status_code} - Time: {process_time:.4f}s")
    return response


# Pydantic models
class ScrapeRequest(BaseModel):
    """Request model for the scraping endpoint.

    Attributes:
        url: The URL to scrape
        fetch_using: Scraper to use (playwright or selenium)
        sleep_time: Time to wait before scraping in seconds
        timeout: Request timeout in seconds
        headless: Run browser in headless mode
        wait_type: Type of wait strategy (sleep, idle, none, selector, text)
        wait_selector: CSS selector or text to wait for (required for selector/text wait_type)
    """

    url: str = Field(..., description="URL to scrape")
    fetch_using: Literal["playwright", "selenium"] = Field(
        default="selenium", description="Scraper to use (playwright or selenium)"
    )
    sleep_time: int = Field(default=2, ge=0, le=30, description="Sleep time in seconds before scraping")
    timeout: int = Field(default=10, ge=1, le=60, description="Request timeout in seconds")
    headless: bool = Field(default=True, description="Run browser in headless mode")
    wait_type: Literal["sleep", "idle", "none", "selector", "text"] = Field(
        default="sleep", description="Wait strategy to use"
    )
    wait_selector: str | None = Field(default=None, description="CSS selector or text to wait for")



class ScrapeResponse(BaseModel):
    """Response model for the scraping endpoint.

    Attributes:
        url: The URL that was scraped
        urls: List of all URLs found on the page (excluding images)
        text: All visible text content from the page
        fetch_using: The scraper that was used
        processing_time: Time taken to process the request in seconds
    """

    url: str
    urls: list[str]
    text: str
    fetch_using: str
    processing_time: float


class ErrorResponse(BaseModel):
    """Error response model.

    Attributes:
        error: Error message
        type: Error type
        detail: Additional error details
    """

    error: str
    type: str
    detail: str | None = None


# Custom exceptions
class InvalidURLError(HTTPException):
    """Exception raised when URL is invalid."""

    def __init__(self, url: str):
        """Initialize InvalidURLError.

        Args:
            url: The invalid URL
        """
        super().__init__(status_code=400, detail=f"Invalid URL: {url}. URL must start with http:// or https://")


class ScrapingTimeoutError(HTTPException):
    """Exception raised when scraping times out."""

    def __init__(self, timeout: int):
        """Initialize ScrapingTimeoutError.

        Args:
            timeout: The timeout value in seconds
        """
        super().__init__(status_code=504, detail=f"Scraping timeout after {timeout} seconds")


class NetworkError(HTTPException):
    """Exception raised for network-related errors."""

    def __init__(self, message: str):
        """Initialize NetworkError.

        Args:
            message: Error message
        """
        super().__init__(status_code=502, detail=f"Network error: {message}")


class ParsingError(HTTPException):
    """Exception raised when HTML parsing fails."""

    def __init__(self, message: str):
        """Initialize ParsingError.

        Args:
            message: Error message
        """
        super().__init__(status_code=500, detail=f"HTML parsing error: {message}")


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions.

    Args:
        request: The request that caused the exception
        exc: The exception that was raised

    Returns:
        JSONResponse with error details
    """
    console_out.print(f"[bold red]Unhandled exception:[/bold red] {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "type": type(exc).__name__, "detail": "Internal server error"},
    )


# Helper functions
def validate_url(url: str) -> None:
    """Validate that URL has a proper scheme.

    Args:
        url: URL to validate

    Raises:
        InvalidURLError: If URL doesn't have http:// or https:// scheme
    """
    parsed = urlparse(url)
    if not parsed.scheme or parsed.scheme not in ["http", "https"]:
        raise InvalidURLError(url)


def map_wait_type(wait_type: str) -> ScraperWaitType:
    """Map string wait type to ScraperWaitType enum.

    Args:
        wait_type: Wait type as string

    Returns:
        ScraperWaitType enum value
    """
    mapping = {
        "sleep": ScraperWaitType.SLEEP,
        "idle": ScraperWaitType.IDLE,
        "none": ScraperWaitType.NONE,
        "selector": ScraperWaitType.SELECTOR,
        "text": ScraperWaitType.TEXT,
    }
    return mapping.get(wait_type, ScraperWaitType.SLEEP)


def extract_urls_and_text(html: str, base_url: str) -> tuple[list[str], str]:
    """Extract all URLs and visible text from HTML content.

    Args:
        html: HTML content to parse
        base_url: Base URL for resolving relative links

    Returns:
        Tuple of (list of URLs, visible text)
    """
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin, urlparse
    
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



# Endpoints
@app.get("/", tags=["Info"])
async def root() -> dict:
    """Get API information and available endpoints.

    Returns:
        Dictionary with API information
    """
    return {
        "name": __application_title__,
        "version": __version__,
        "description": "Web scraping API with support for Playwright and Selenium",
        "docs": "/docs",
        "endpoints": {
            "scrape": {"method": "POST", "path": "/scrape", "description": "Scrape a URL and return markdown"},
            "health": {"method": "GET", "path": "/health", "description": "Health check endpoint"},
        },
    }


@app.get("/health", tags=["Health"])
async def health() -> dict:
    """Health check endpoint for monitoring and Railway deployment.

    Returns:
        Dictionary with health status and timestamp
    """
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "version": __version__}


@app.post("/scrape", response_model=ScrapeResponse, tags=["Scraping"])
async def scrape_url_endpoint(request: ScrapeRequest) -> ScrapeResponse:
    """Scrape a URL and return all URLs and visible text from the page.

    Args:
        request: Scraping request parameters

    Returns:
        ScrapeResponse with URLs list and visible text content

    Raises:
        InvalidURLError: If URL is invalid
        ScrapingTimeoutError: If scraping times out
        NetworkError: If network error occurs
        ParsingError: If HTML parsing fails
    """
    start_time = time.time()

    # Validate URL
    validate_url(request.url)

    # Validate wait_selector if wait_type requires it
    if request.wait_type in ["selector", "text"] and not request.wait_selector:
        raise HTTPException(
            status_code=400, detail=f"wait_selector is required when wait_type is '{request.wait_type}'"
        )

    try:
        logger.info(f"Starting scrape for URL: {request.url}")
        logger.info(f"Configuration: fetch_using={request.fetch_using}, headless={request.headless}, sleep={request.sleep_time}s")
        logger.info(f"Wait configuration: wait_type={request.wait_type}, wait_selector={request.wait_selector}")
        console_out.print(f"[cyan]Scraping URL:[/cyan] {request.url}")
        console_out.print(f"[cyan]Using:[/cyan] {request.fetch_using}, headless={request.headless}, sleep={request.sleep_time}s")

        # Fetch HTML content
        logger.info("Calling fetch_url...")
        html_list = fetch_url(
            request.url,
            fetch_using=request.fetch_using,
            sleep_time=request.sleep_time,
            timeout=request.timeout,
            headless=request.headless,
            wait_type=map_wait_type(request.wait_type),
            wait_selector=request.wait_selector,
            verbose=True,
            console=console_out,
        )
        
        logger.info(f"fetch_url completed, returned type: {type(html_list)}")
        console_out.print(f"[magenta]DEBUG: fetch_url returned type: {type(html_list)}[/magenta]")
        if html_list:
             logger.info(f"fetch_url returned list of length: {len(html_list)}")
             console_out.print(f"[magenta]DEBUG: fetch_url returned list of length: {len(html_list)}[/magenta]")
        else:
             logger.warning("fetch_url returned empty list or None")
             console_out.print("[magenta]DEBUG: fetch_url returned empty list or None[/magenta]")

        logger.debug(f"Fetch URL returned {len(html_list) if html_list else 0} items")
        console_out.print(f"[yellow]Fetched {len(html_list) if html_list else 0} items[/yellow]")
        if html_list and html_list[0]:
            logger.debug(f"First HTML item length: {len(html_list[0])} chars")
            console_out.print(f"[yellow]HTML length: {len(html_list[0])} chars[/yellow]")

        if not html_list or not html_list[0]:
            raise ParsingError("No content was fetched from the URL")

        # Extract URLs and text from HTML
        logger.info("Extracting URLs and text from HTML...")
        urls, text = extract_urls_and_text(html_list[0], request.url)
        logger.info(f"Extraction complete: {len(urls)} URLs found, text length: {len(text)} chars")

        if not text or not text.strip():
            logger.error("Text extraction resulted in empty content")
            raise ParsingError("Text extraction resulted in empty content")

        processing_time = time.time() - start_time
        console_out.print(f"[green]Successfully scraped {request.url} in {processing_time:.2f}s[/green]")
        console_out.print(f"[cyan]Found {len(urls)} URLs and {len(text)} characters of text[/cyan]")

        return ScrapeResponse(
            url=request.url, 
            urls=urls, 
            text=text, 
            fetch_using=request.fetch_using, 
            processing_time=processing_time
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        error_msg = str(e).lower()
        logger.error(f"Exception caught in scrape endpoint: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")

        # Classify error type
        if "timeout" in error_msg or "timed out" in error_msg:
            logger.error("Classified as timeout error")
            raise ScrapingTimeoutError(request.timeout)
        elif "network" in error_msg or "connection" in error_msg:
            logger.error("Classified as network error")
            raise NetworkError(str(e))
        elif "parse" in error_msg or "html" in error_msg:
            raise ParsingError(str(e))
        else:
            # Re-raise as generic HTTP exception
            logger.error(f"Unexpected error during scraping: {str(e)}", exc_info=True)
            console_out.print(f"[bold red]Unexpected error:[/bold red] {str(e)}")
            import traceback
            console_out.print(f"[bold red]Traceback:[/bold red]\n{traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
