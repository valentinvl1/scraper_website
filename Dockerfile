# Use Python 3.13 slim image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for Chromium/Selenium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    unzip \
    chromium \
    chromium-driver \
    # Additional libraries for Chromium
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libxss1 \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libgdk-pixbuf2.0-0 \
    libnspr4 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    fonts-liberation \
    libgbm1 \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY README.md CLAUDE.md LICENSE ./

# Install dependencies with uv
RUN uv sync --no-dev

# Install Playwright browsers (works better in Docker than Selenium)
RUN uv run playwright install chromium
RUN uv run playwright install-deps chromium

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
