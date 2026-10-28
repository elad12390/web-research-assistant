---
name: "@elad12390/web-research-assistant"
description: |
  Comprehensive MCP server for web research with 16 tools: SearXNG + Exa AI
  search, batch search and batch crawling, URL crawling, stealth scraping (Cloudflare bypass), package
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

A Model Context Protocol server providing 16 research tools, 4 resources, and 5 prompts for AI agents.
Works with SearXNG (local search), Exa AI (neural search), Scrapling (page extraction), Pixabay (images),
and direct registry/GitHub APIs.

## Batch, don't loop

- Several pages to read: call `batch_crawl_urls` once with every URL in `urls` (up to 20), never
  `crawl_url` once per URL. Pages come back in request order; a failed page does not stop the others.
- Several searches: call `batch_web_search` once with every query in `queries` (up to 20), never
  `web_search` once per query.
- In code, build the array inside the loop and make one batch call after it.
- When `batch_crawl_urls` cuts pages to fit its shared budget, its result ends with the exact
  arguments that continue all of them; send those in one more call.

## Installation

```bash
tank install @elad12390/web-research-assistant
```

See the package [README](https://github.com/elad12390/web-research-assistant) for environment variables,
required services (SearXNG instance, optional Exa/Pixabay API keys), and the full tool reference.
