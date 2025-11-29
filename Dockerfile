# Use Python 3.13 slim image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    curl \
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

# Install Playwright and its system dependencies (automatically installs everything needed)
RUN uv run playwright install chromium
RUN uv run playwright install-deps chromium

# Expose port
EXPOSE 8000

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

# Run the API
CMD ["uv", "run", "par_scrape_api"]
