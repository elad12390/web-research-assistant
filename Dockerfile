# Dockerfile for Web Research Assistant MCP Server
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for crawl4ai
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (for better layer caching)
COPY requirements.txt pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install crawl4ai browser dependencies
RUN pip install --no-cache-dir playwright && \
    playwright install chromium && \
    playwright install-deps chromium

# Copy source code
COPY src/ ./src/

# Install the package in development mode
RUN pip install -e .

# Set environment variables with defaults
ENV SEARXNG_BASE_URL="http://searxng:8080/search" \
    SEARXNG_DEFAULT_CATEGORY="general" \
    SEARXNG_DEFAULT_RESULTS="5" \
    SEARXNG_MAX_RESULTS="10" \
    SEARXNG_CRAWL_MAX_CHARS="8000" \
    MCP_MAX_RESPONSE_CHARS="8000" \
    SEARXNG_MCP_USER_AGENT="web-research-assistant/0.4.0"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; from searxng_mcp.server import main; sys.exit(0)"

# Run the MCP server
CMD ["python", "-m", "searxng_mcp.server"]
