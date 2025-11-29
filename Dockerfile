# Use Python 3.13 slim image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Chromium/Selenium
RUN apt-get update && apt-get install -y \
    curl \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Create a wrapper for Chromium to force necessary flags for Docker
RUN mv /usr/bin/chromium /usr/bin/chromium-original && \
    echo '#!/bin/bash\n/usr/bin/chromium-original --no-sandbox --disable-dev-shm-usage --disable-gpu "$@"' > /usr/bin/chromium && \
    chmod +x /usr/bin/chromium

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY README.md CLAUDE.md LICENSE ./

# Install dependencies with uv
RUN uv sync --no-dev

# Expose port
EXPOSE 8000

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8000
ENV PYTHONUNBUFFERED=1
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Run the API
CMD ["uv", "run", "par_scrape_api"]
