# Docker Setup Guide

This guide explains how to run the entire Web Research Assistant stack using Docker, eliminating the need for local Python installation.

## Quick Start

### 1. Prerequisites

- Docker Desktop (or Docker Engine + Docker Compose)
- Git (to clone the repository)

### 2. Start Everything

```bash
./docker-start.sh
```

This script will:
- Create `.env` file if it doesn't exist
- Build Docker images
- Start SearXNG and Web Research Assistant containers
- Display service URLs and helpful commands

### 3. Verify Services

```bash
docker-compose ps
curl 'http://localhost:2288/search?q=test&format=json'
```

## What Gets Installed

The Docker setup includes:

1. **SearXNG** (port 2288)
   - Federated search engine
   - Configured with GitHub, Stack Overflow, and other code-focused engines
   - Optimized for AI research

2. **Web Research Assistant MCP Server**
   - Python MCP server with 13 tools
   - Crawl4AI with Playwright and Chromium
   - All dependencies pre-installed

## Configuration

### API Keys (Optional but Recommended)

Edit `.env` file to add your API keys:

```bash
EXA_API_KEY=your_exa_api_key_here
PIXABAY_API_KEY=your_pixabay_api_key_here
```

**Get API keys:**
- Exa AI: https://dashboard.exa.ai/api-keys
- Pixabay: https://pixabay.com/api/docs/

### SearXNG Configuration

The SearXNG configuration is in `searxng-config/settings.yml`. It's pre-configured with optimal settings for code search.

To customize:
1. Edit `searxng-config/settings.yml`
2. Restart SearXNG: `docker-compose restart searxng`

## Using with Claude Desktop

To use the Dockerized MCP server with Claude Desktop, you have two options:

### Option A: Use stdio bridge (Recommended for Docker)

Create a wrapper script `run-mcp-docker.sh`:

```bash
#!/bin/bash
docker-compose exec -T web-research-assistant python -m searxng_mcp.server
```

Make it executable:
```bash
chmod +x run-mcp-docker.sh
```

Add to Claude Desktop config:
```json
{
  "mcpServers": {
    "web-research-assistant": {
      "command": "/absolute/path/to/web-research-assistant/run-mcp-docker.sh"
    }
  }
}
```

### Option B: Expose MCP over network (Advanced)

Modify `docker-compose.yml` to expose port and configure network transport.

## Common Commands

### View logs
```bash
docker-compose logs -f
docker-compose logs searxng
docker-compose logs web-research-assistant
```

### Restart services
```bash
docker-compose restart
docker-compose restart searxng
```

### Stop services
```bash
docker-compose down
```

### Rebuild after code changes
```bash
docker-compose build
docker-compose up -d
```

### Clean everything (including volumes)
```bash
docker-compose down -v
rm -rf data/ searxng-config/
```

## Development Mode

To mount your local source code for live development:

Uncomment in `docker-compose.yml`:
```yaml
volumes:
  - ./src:/app/src:ro
```

Then restart:
```bash
docker-compose up -d
```

Changes to Python files will require container restart:
```bash
docker-compose restart web-research-assistant
```

## Troubleshooting

### SearXNG won't start

Check logs:
```bash
docker-compose logs searxng
```

Common issues:
- Invalid `settings.yml` syntax
- Port 2288 already in use

### MCP server can't connect to SearXNG

1. Verify SearXNG is running:
   ```bash
   curl 'http://localhost:2288/search?q=test&format=json'
   ```

2. Check network connectivity:
   ```bash
   docker-compose exec web-research-assistant curl http://searxng:8080/search?q=test
   ```

3. Check environment variables:
   ```bash
   docker-compose exec web-research-assistant env | grep SEARXNG
   ```

### Browser/Chromium issues

The Dockerfile installs Playwright Chromium. If you get browser errors:

1. Check browser installation:
   ```bash
   docker-compose exec web-research-assistant playwright install chromium
   ```

2. Rebuild container:
   ```bash
   docker-compose build --no-cache web-research-assistant
   docker-compose up -d
   ```

### Out of disk space

Docker images can be large. Clean up:
```bash
docker system prune -a
```

## Architecture

```
┌─────────────────────────────────────┐
│  Claude Desktop / MCP Client        │
└──────────────┬──────────────────────┘
               │ stdio / network
┌──────────────▼──────────────────────┐
│  web-research-assistant container   │
│  - Python 3.11                      │
│  - MCP server                       │
│  - crawl4ai + Playwright            │
│  - Chromium browser                 │
└──────────────┬──────────────────────┘
               │ HTTP
┌──────────────▼──────────────────────┐
│  searxng container                  │
│  - SearXNG search engine            │
│  - Configured engines               │
└─────────────────────────────────────┘
```

## Performance

- **First build**: ~5 minutes (downloads images, installs Chromium)
- **Subsequent builds**: ~30 seconds (uses layer cache)
- **Container size**: ~2GB (includes Chromium)
- **Memory usage**: ~500MB idle, ~1.5GB during heavy crawling

## Security Notes

This setup is designed for **local development only**:

- SearXNG binds to 0.0.0.0 inside container but maps to localhost
- No authentication on SearXNG
- Rate limiting disabled for convenience
- Don't expose ports 2288 or any service to the internet

For production use, add:
- Reverse proxy with authentication
- Rate limiting
- HTTPS/TLS
- Network isolation

## Benefits of Docker Setup

✅ No Python version conflicts  
✅ No local dependency installation  
✅ Consistent environment across machines  
✅ Easy cleanup (just delete containers)  
✅ Isolated from system Python  
✅ Pre-configured SearXNG  
✅ All browsers/dependencies included  

## Alternative: Non-Docker Setup

If you prefer running directly on your machine, see the main [README.md](README.md) for:
- Using `uvx web-research-assistant`
- Installing with pip/uv
- Running from source with `uv run`

The Docker setup is equivalent but fully containerized.
