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

# Monkey-patch Selenium Chrome for Docker compatibility
def _patch_selenium_chrome():
    """Patch selenium.webdriver.Chrome to add --no-sandbox flag for Docker compatibility."""
    logger.info("Starting Selenium Chrome patch for Docker compatibility")
    try:
        logger.debug("Importing selenium and webdriver modules")
        import os
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        original_init = webdriver.Chrome.__init__

        def patched_init(self, *args, **kwargs):
            logger.info("Chrome initialization called with patched init")
            console_out.print("[magenta]DEBUG: Entering patched webdriver.Chrome.__init__[/magenta]")
            logger.debug(f"Chrome init args: {args}")
            logger.debug(f"Chrome init kwargs: {list(kwargs.keys())}")
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
        include_images: Include images in the markdown output
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
    include_images: bool = Field(default=True, description="Include images in markdown output")


class ScrapeResponse(BaseModel):
    """Response model for the scraping endpoint.

    Attributes:
        url: The URL that was scraped
        markdown: The extracted content in markdown format
        fetch_using: The scraper that was used
        processing_time: Time taken to process the request in seconds
    """

    url: str
    markdown: str
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
    """Scrape a URL and return the content as markdown.

    Args:
        request: Scraping request parameters

    Returns:
        ScrapeResponse with markdown content

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

        # Convert HTML to markdown
        logger.info("Converting HTML to markdown...")
        markdown = html_to_markdown(html_list[0], url=request.url, include_images=request.include_images)
        logger.info(f"Markdown conversion complete, length: {len(markdown) if markdown else 0} chars")

        if not markdown or not markdown.strip():
            logger.error("Markdown conversion resulted in empty content")
            raise ParsingError("Markdown conversion resulted in empty content")

        processing_time = time.time() - start_time
        console_out.print(f"[green]Successfully scraped {request.url} in {processing_time:.2f}s[/green]")

        return ScrapeResponse(
            url=request.url, markdown=markdown, fetch_using=request.fetch_using, processing_time=processing_time
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
