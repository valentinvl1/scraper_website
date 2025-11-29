"""Entry point for the PAR Scrape API server.

This module provides the main entry point for running the FastAPI application
using uvicorn as the ASGI server.
"""

import os

import uvicorn


def main() -> None:
    """Run the FastAPI application using uvicorn.

    Configuration is read from environment variables:
    - HOST: Host to bind to (default: 0.0.0.0)
    - PORT: Port to listen on (default: 8000)
    - RELOAD: Enable auto-reload for development (default: false)
    """
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "false").lower() == "true"

    uvicorn.run("par_scrape.api:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    main()
