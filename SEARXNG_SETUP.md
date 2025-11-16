# SearXNG Setup Guide for Web Research Assistant

This guide will help you set up a local SearXNG instance optimized for the Web Research Assistant MCP server.

## Quick Start (Docker - Recommended)

### Option 1: Docker Compose (Easiest)

Create a `docker-compose.yml` file:

```yaml
version: '3.7'

services:
  searxng:
    container_name: searxng
    image: searxng/searxng:latest
    ports:
      - "2288:8080"
    volumes:
      - ./searxng:/etc/searxng:rw
    environment:
      - SEARXNG_BASE_URL=http://localhost:2288/
    restart: unless-stopped
```

Then run:

```bash
# Create config directory
mkdir -p searxng

# Download the optimized settings.yml (see below)
# or copy from this repository

# Start SearXNG
docker compose up -d

# Verify it's running
curl http://localhost:2288/search?q=test&format=json
```

### Option 2: Docker Run (Quick)

```bash
# Create config directory
mkdir -p ~/searxng-config

# Run SearXNG
docker run -d \
  --name searxng \
  -p 2288:8080 \
  -v ~/searxng-config:/etc/searxng:rw \
  -e SEARXNG_BASE_URL=http://localhost:2288/ \
  --restart unless-stopped \
  searxng/searxng:latest

# Verify it's running
curl http://localhost:2288/search?q=test&format=json
```

## Optimized Configuration

Create `searxng/settings.yml` with this configuration:

```yaml
# SearXNG Configuration - Optimized for Web Research Assistant MCP
# Save this as searxng/settings.yml (or /etc/searxng/settings.yml)

use_default_settings: true

general:
  debug: false
  instance_name: "Web Research Assistant"
  privacypolicy_url: false
  donation_url: false
  contact_url: false
  enable_metrics: false

search:
  safe_search: 0
  autocomplete: "duckduckgo"
  default_lang: "en"
  formats:
    - html
    - json

server:
  port: 8080
  bind_address: "0.0.0.0"
  secret_key: "change-this-to-random-string"  # Change this!
  limiter: false  # Disable rate limiting for local use
  image_proxy: true

outgoing:
  request_timeout: 10.0
  max_request_timeout: 15.0

# Essential engines for code search and web research
engines:
  # ===== GENERAL WEB SEARCH =====
  - name: duckduckgo
    engine: duckduckgo
    shortcut: ddg
    disabled: false

  - name: brave
    engine: brave
    shortcut: br
    disabled: false

  - name: qwant
    engine: qwant
    shortcut: qw
    disabled: false

  # ===== CODE & DEVELOPER (CRITICAL!) =====
  - name: github
    engine: github
    shortcut: gh
    disabled: false

  - name: stackoverflow
    engine: stackoverflow
    shortcut: so
    disabled: false

  - name: gitlab
    engine: gitlab
    shortcut: gl
    disabled: false

  - name: codeberg
    engine: codeberg
    shortcut: cb
    disabled: false

  # ===== DOCUMENTATION =====
  - name: mdn
    engine: mdn
    shortcut: mdn
    disabled: false

  - name: devdocs
    engine: devdocs
    shortcut: dd
    disabled: false

  - name: wikipedia
    engine: wikipedia
    shortcut: wp
    disabled: false

  # ===== TECH COMMUNITY =====
  - name: reddit
    engine: reddit
    shortcut: re
    disabled: false

  - name: hackernews
    engine: hackernews
    shortcut: hn
    disabled: false

  # ===== PACKAGE REGISTRIES =====
  - name: pypi
    engine: pypi
    shortcut: pypi
    disabled: false

  - name: npm
    engine: npm
    shortcut: npm
    disabled: false

  - name: crates
    engine: crates
    shortcut: cr
    disabled: false

  # ===== VIDEO (Optional) =====
  - name: youtube
    engine: youtube_noapi
    shortcut: yt
    disabled: false

  # ===== DISABLE EXPENSIVE ENGINES =====
  - name: google
    disabled: true  # Requires API key

  - name: bing
    disabled: true  # Requires API key

# Category configuration (IMPORTANT!)
categories_as_tabs:
  general:
    - duckduckgo
    - brave
    - qwant
    - wikipedia

  it:
    - github
    - stackoverflow
    - gitlab
    - codeberg
    - mdn
    - devdocs
    - hackernews
    - reddit
    - pypi
    - npm
    - crates

  science:
    - wikipedia
    - stackoverflow

  news:
    - reddit
    - hackernews

  videos:
    - youtube
```

## After Setup

1. **Restart SearXNG** to apply configuration:
   ```bash
   docker restart searxng
   ```

2. **Test the connection**:
   ```bash
   curl "http://localhost:2288/search?q=test&format=json"
   ```

3. **Test with the MCP server**:
   ```bash
   uv run web-research-assistant
   ```

4. **Verify in Claude Desktop**: You should see all 13 tools available

## Configuration Explanation

### Why Port 2288?
This is the default port expected by the MCP server. You can change it by setting the `SEARXNG_BASE_URL` environment variable.

### Critical Engines for Code Search

The `search_examples` tool heavily relies on:
- **GitHub** - Code repositories and examples
- **Stack Overflow** - Q&A and solutions
- **GitLab/Codeberg** - More code repositories
- **Reddit** - Tutorials and discussions
- **MDN** - Web API documentation

**Without these, `search_examples` will give poor results!**

### Categories

The `it` category is crucial - this is what the `search_examples` tool uses when searching for code examples.

## Troubleshooting

### Port Already in Use

If port 2288 is taken:

```bash
# Use a different port
docker run -d \
  --name searxng \
  -p 3000:8080 \
  -v ~/searxng-config:/etc/searxng:rw \
  searxng/searxng:latest

# Update your MCP server environment
export SEARXNG_BASE_URL="http://localhost:3000/search"
```

### Container Won't Start

Check logs:
```bash
docker logs searxng
```

Common issues:
- Invalid `settings.yml` syntax (YAML is indent-sensitive!)
- Missing secret_key in settings.yml
- Port conflict

### Settings Not Applied

```bash
# Stop container
docker stop searxng

# Remove container (keeps volumes)
docker rm searxng

# Start fresh
docker compose up -d
# or
docker run ... (same command as before)
```

### Testing Specific Engines

Test individual engines:

```bash
# Test GitHub
curl "http://localhost:2288/search?q=react+hooks&engines=github&format=json"

# Test Stack Overflow
curl "http://localhost:2288/search?q=python+async&engines=stackoverflow&format=json"

# Test IT category
curl "http://localhost:2288/search?q=rust+examples&category=it&format=json"
```

## Minimal Configuration

If you want the absolute minimum:

```yaml
use_default_settings: true

engines:
  # Just these 6 engines
  - name: duckduckgo
    disabled: false
  - name: github
    disabled: false
  - name: stackoverflow
    disabled: false
  - name: mdn
    disabled: false
  - name: reddit
    disabled: false
  - name: wikipedia
    disabled: false
```

But the full configuration above is **strongly recommended** for best results.

## Performance Tuning

For better performance:

1. **Increase timeouts** if searches are slow:
   ```yaml
   outgoing:
     request_timeout: 15.0
     max_request_timeout: 20.0
   ```

2. **Reduce engines** if too many results:
   - Start with 8-10 engines
   - Add more as needed

3. **Enable caching** (optional):
   ```yaml
   server:
     cache:
       type: "simple"
       size: 1000
   ```

## Security Notes

⚠️ **This setup is for LOCAL USE ONLY**

- SearXNG binds to `0.0.0.0` in the container but is mapped to localhost
- Rate limiting is disabled for local convenience
- Don't expose port 2288 to the internet
- Change the `secret_key` in settings.yml

If you need external access, use a reverse proxy with authentication.

## Updating SearXNG

```bash
# Pull latest image
docker pull searxng/searxng:latest

# Recreate container
docker stop searxng
docker rm searxng
docker compose up -d  # or docker run command
```

Your configuration in the volume will be preserved.

## Alternative: Native Installation

If you prefer not to use Docker:

```bash
# Install SearXNG (Ubuntu/Debian)
sudo apt install python3-searxng

# Configure
sudo nano /etc/searxng/settings.yml
# (paste the configuration above)

# Start service
sudo systemctl start searxng
sudo systemctl enable searxng
```

See [SearXNG docs](https://docs.searxng.org/) for other platforms.

## Verification Checklist

After setup, verify:

- [ ] SearXNG running on http://localhost:2288
- [ ] JSON API works: `curl http://localhost:2288/search?q=test&format=json`
- [ ] GitHub engine enabled and working
- [ ] Stack Overflow engine enabled and working
- [ ] `it` category configured with code engines
- [ ] MCP server can connect
- [ ] `search_examples` returns code results

## Expected Results

With this configuration, `search_examples("React hooks tutorial")` should return:

✅ GitHub repositories with React hooks examples  
✅ Stack Overflow Q&A about React hooks  
✅ Reddit discussions and tutorials  
✅ MDN documentation  
✅ Dev.to articles  

❌ Without proper configuration, you might only get:
- Generic web results
- Only documentation
- Irrelevant results

## Next Steps

Once SearXNG is configured:

1. Test it: `curl http://localhost:2288/search?q=python&format=json`
2. Start the MCP server: `uv run web-research-assistant`
3. Try the tools in Claude Desktop
4. Adjust engine configuration based on your needs

## Resources

- [SearXNG Documentation](https://docs.searxng.org/)
- [SearXNG GitHub](https://github.com/searxng/searxng)
- [Engine List](https://docs.searxng.org/admin/engines/configured_engines.html)
- [Settings Reference](https://docs.searxng.org/admin/settings/settings.html)

## Getting Help

If you have issues:

1. Check logs: `docker logs searxng`
2. Test the API: `curl http://localhost:2288/search?q=test&format=json`
3. Verify settings.yml syntax (use a YAML validator)
4. Open an issue: https://github.com/elad12390/web-research-assistant/issues

---

**With this configuration, you'll have a powerful search backend for AI-powered web research!** 🚀
