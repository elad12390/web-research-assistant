# Quick Reference - Docker Commands

## Start Everything
```bash
./docker-start.sh
```

## Manual Control

### Start services
```bash
docker-compose up -d
```

### Stop services
```bash
docker-compose down
```

### View logs (all services)
```bash
docker-compose logs -f
```

### View logs (specific service)
```bash
docker-compose logs -f searxng
docker-compose logs -f web-research-assistant
```

### Restart services
```bash
docker-compose restart
```

### Rebuild after code changes
```bash
docker-compose build
docker-compose up -d
```

## Verify Services

### Check service status
```bash
docker-compose ps
```

### Test SearXNG
```bash
curl 'http://localhost:2288/search?q=test&format=json'
```

### Test MCP server
```bash
docker-compose exec web-research-assistant python -c "from searxng_mcp.server import main; print('MCP server OK')"
```

## Troubleshooting

### View full Docker output
```bash
docker-compose logs
```

### Check environment variables
```bash
docker-compose exec web-research-assistant env | grep SEARXNG
```

### Shell into container
```bash
docker-compose exec web-research-assistant bash
docker-compose exec searxng sh
```

### Clean rebuild
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

## Service URLs

- **SearXNG**: http://localhost:2288
- **MCP Server**: Running in container (stdio/network)

## Configuration Files

- `docker-compose.yml` - Service definitions
- `Dockerfile` - MCP server container
- `.env` - Environment variables (API keys)
- `searxng-config/settings.yml` - SearXNG configuration

## Data Persistence

Data is persisted in:
- `./data/` - MCP usage logs
- `./searxng-config/` - SearXNG configuration

To completely reset:
```bash
docker-compose down -v
rm -rf data/ searxng-config/
./docker-start.sh
```
