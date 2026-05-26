---
name: "@elad12390/web-research-assistant"
description: |
  Comprehensive MCP server for web research with 14 tools: SearXNG + Exa AI
  search, URL crawling, stealth scraping (Cloudflare bypass), package
  registry lookup (npm/PyPI/crates), GitHub stats, changelog fetching, tech
  comparison, error translation, API docs discovery, stock image search,
  and service health.

  Trigger phrases: "web search", "find packages", "crawl url",
  "scrape website", "translate error", "compare frameworks",
  "stock images", "service status", "search github", "api docs",
  "get changelog", "compare tech", "search examples", "extract data"
---

# Web Research Assistant MCP

## Summary

A Model Context Protocol server providing 14 research tools, 4 resources, and 5 prompts for AI agents.
Works with SearXNG (local search), Exa AI (neural search), Crawl4AI (page extraction), Pixabay (images),
and direct registry/GitHub APIs.

## Installation

```bash
tank install @elad12390/web-research-assistant
```

See the package [README](https://github.com/elad12390/web-research-assistant) for environment variables,
required services (SearXNG instance, optional Exa/Pixabay API keys), and the full tool reference.
