# Web Research Assistant MCP Server

[![PyPI](https://img.shields.io/pypi/v/web-research-assistant?color=blue)](https://pypi.org/project/web-research-assistant/)
[![Python Version](https://img.shields.io/pypi/pyversions/web-research-assistant)](https://pypi.org/project/web-research-assistant/)
[![License](https://img.shields.io/github/license/elad12390/web-research-assistant)](https://github.com/elad12390/web-research-assistant/blob/main/LICENSE)
[![CI](https://github.com/elad12390/web-research-assistant/workflows/CI/badge.svg)](https://github.com/elad12390/web-research-assistant/actions)

Comprehensive Model Context Protocol (MCP) server that provides web research and discovery capabilities.
Includes **16 tools**, **4 resources**, and **5 prompts** for searching, crawling, and analyzing web content, powered by your local Docker SearXNG
instance, [Exa AI](https://exa.ai/) neural search, [Scrapling](https://github.com/D4Vinci/Scrapling), and Pixabay API:

1. `web_search` &mdash; federated search across multiple engines via SearXNG
2. `batch_web_search` &mdash; run up to 20 searches in one call instead of looping `web_search`
3. `search_examples` &mdash; find code examples, tutorials, and articles (defaults to recent content)
4. `search_images` &mdash; find high-quality stock photos, illustrations, and vectors via Pixabay
5. `crawl_url` &mdash; full page content extraction with advanced crawling
6. `batch_crawl_urls` &mdash; read up to 20 pages in parallel in one call instead of looping `crawl_url`
7. `package_info` &mdash; detailed package metadata from npm, PyPI, crates.io, Go
8. `package_search` &mdash; discover packages by keywords and functionality  
9. `github_repo` &mdash; repository health metrics and development activity
10. `translate_error` &mdash; find solutions for error messages and stack traces from Stack Overflow (auto-detects CORS, fetch, and web errors)
11. `api_docs` &mdash; auto-discover and crawl official API documentation with examples (works for any API - no hardcoded URLs)
12. `extract_data` &mdash; extract structured data (tables, lists, fields, JSON-LD) from web pages with automatic detection
13. `compare_tech` &mdash; compare technologies side-by-side with NPM downloads, GitHub stars, and aspect analysis (React vs Vue, PostgreSQL vs MongoDB, etc.)
14. `get_changelog` &mdash; **NEW!** Get release notes and changelogs with breaking change detection (upgrade safely from version X to Y)
15. `check_service_status` &mdash; **NEW!** Instant health checks for 25+ services (Stripe, AWS, GitHub, OpenAI, etc.) - "Is it down or just me?"

The server's MCP instructions tell agents to batch: several pages or searches go into one
`batch_crawl_urls` or `batch_web_search` call, never one `crawl_url` or `web_search` call per item.

All tools feature comprehensive error handling, response size limits, usage tracking, and clear documentation
for optimal AI agent integration.

### MCP Resources (Direct Data Lookups)

- `package://{registry}/{name}` - Package info from npm, PyPI, crates.io, or Go modules
- `github://{owner}/{repo}` - Repository information and health metrics
- `status://{service}` - Service health status for 120+ services
- `changelog://{registry}/{package}` - Package release notes and changelogs

### MCP Prompts (Reusable Workflows)

- `research_package` - Comprehensive package evaluation
- `debug_error` - Structured error debugging with solutions
- `compare_technologies` - Side-by-side technology comparison
- `evaluate_repository` - GitHub repository health assessment
- `check_service_health` - Multi-service status monitoring

## Quick Start

### Option 1: Full Docker Setup (Recommended)

Everything runs in Docker - no Python installation needed:

```bash
./docker-start.sh
```

This starts both SearXNG and the MCP server in containers. See [DOCKER_SETUP.md](DOCKER_SETUP.md) for details.

### Option 2: Python + Docker SearXNG

1. **Set up SearXNG** (5 minutes):
   ```bash
   # Using Docker (recommended)
   docker run -d -p 2288:8080 searxng/searxng:latest
   ```
   Then configure search engines - see [SEARXNG_SETUP.md](SEARXNG_SETUP.md) for optimized settings.

2. **Install the MCP server**:
   ```bash
   uvx web-research-assistant  # or: pip install web-research-assistant
   ```

3. **Configure Claude Desktop** - add to `claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "web-research-assistant": {
         "command": "uvx",
         "args": ["web-research-assistant"]
       }
     }
   }
   ```

4. **Restart Claude Desktop** and start researching!

> ⚠️ **For best results**: Configure SearXNG with GitHub, Stack Overflow, and other code-focused search engines. See [SEARXNG_SETUP.md](SEARXNG_SETUP.md) for the recommended configuration.

## Prerequisites

### Required

- **Python 3.10+**
- **A running SearXNG instance** on `http://localhost:2288`
  - **📖 See [SEARXNG_SETUP.md](SEARXNG_SETUP.md) for complete Docker setup guide**
  - ⚠️ **IMPORTANT**: For best results, enable these search engines in SearXNG:
    - **GitHub, Stack Overflow, GitLab** (for code search - critical!)
    - **DuckDuckGo, Brave** (for web search)
    - **MDN, Wikipedia** (for documentation)
    - **Reddit, HackerNews** (for tutorials and discussions)
    - See [SEARXNG_SETUP.md](SEARXNG_SETUP.md) for the full optimized configuration

### Optional

- **Exa API key** for neural search - [Get API key](https://dashboard.exa.ai/api-keys) (recommended for better search results)
- **Pixabay API key** for image search - [Get free key](https://pixabay.com/api/docs/)
- **Playwright browsers** for advanced crawling (installed with `scrapling install`)

### Developer Setup (if running from source)

```bash
uv tool install uv  # if you do not already have uv
uv sync --all-extras --all-groups  # creates the virtual environment
uv run scrapling install           # installs Chromium for Scrapling
```

> You can also use `pip install -e .` if you prefer pip over uv (deps come from `pyproject.toml`).

## Installation

### Option 1: Using uvx (Recommended - No installation needed!)

```bash
uvx web-research-assistant
```

This runs the server directly from PyPI without installing it globally.

### Option 2: Install with pip

```bash
pip install web-research-assistant
web-research-assistant
```

### Option 3: Install with uv

```bash
uv tool install web-research-assistant
web-research-assistant
```

By default the server communicates over stdio, which makes it easy to wire into
Claude Desktop or any other MCP host.

### MCP Client Configuration

#### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

**Option 1: Using uvx (Recommended - No installation needed!)**

```json
{
  "mcpServers": {
    "web-research-assistant": {
      "command": "uvx",
      "args": ["web-research-assistant"]
    }
  }
}
```

**Option 2: Using installed package**

```json
{
  "mcpServers": {
    "web-research-assistant": {
      "command": "web-research-assistant"
    }
  }
}
```

#### OpenCode

Add to `~/.config/opencode/opencode.json`:

**Using uvx (Recommended)**

```json
{
  "mcp": {
    "web-research-assistant": {
      "type": "local",
      "command": ["uvx", "web-research-assistant"],
      "enabled": true
    }
  }
}
```

**Using installed package**

```json
{
  "mcp": {
    "web-research-assistant": {
      "type": "local",
      "command": ["web-research-assistant"],
      "enabled": true
    }
  }
}
```

#### Development (Running from source)

For Claude Desktop:
```json
{
  "mcpServers": {
    "web-research-assistant": {
      "command": "uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/TO/web-research-assistant",
        "run",
        "web-research-assistant"
      ]
    }
  }
}
```

For OpenCode:
```json
{
  "mcp": {
    "web-research-assistant": {
      "type": "local",
      "command": [
        "uv",
        "--directory",
        "/ABSOLUTE/PATH/TO/web-research-assistant",
        "run",
        "web-research-assistant"
      ],
      "enabled": true
    }
  }
}
```

**Restart your MCP client** afterwards. The MCP tools will be available immediately.

## Tool behavior

| Tool | When to use | Arguments |
| ---- | ----------- | --------- |
| `web_search` | Use first to gather recent information and URLs from SearXNG. Returns 1&ndash;10 ranked snippets with clickable URLs. | `query` (required), optional `reasoning`, `category` (defaults to `general`), and `max_results` (defaults to 5). |
| `batch_web_search` | Use instead of calling `web_search` more than once. Runs every query in parallel and returns each query's hits in request order; a failed query does not stop the others. | `queries` (required list of 1&ndash;20), optional `reasoning`, `category`, and `max_results` per query (defaults to 5). |
| `search_examples` | Find code examples, tutorials, and technical articles. Optimized for technical content with optional time filtering. Perfect for learning APIs or finding usage patterns. | `query` (required, e.g., "Python async examples"), optional `reasoning`, `content_type` (code/articles/both, defaults to both), `time_range` (day/week/month/year/all, defaults to all), and `max_results` (defaults to 5). |
| `search_images` | Find high-quality royalty-free stock images from Pixabay. Returns photos, illustrations, or vectors. Requires `PIXABAY_API_KEY` environment variable. | `query` (required, e.g., "mountain landscape"), optional `reasoning`, `image_type` (all/photo/illustration/vector, defaults to all), `orientation` (all/horizontal/vertical, defaults to all), and `max_results` (defaults to 10). |
| `crawl_url` | Call immediately after search when you need the actual article body for quoting, summarizing, or extracting data. Continue long pages with the returned `start_char` value. | `url` (required), optional `reasoning`, `max_chars` (defaults to 12000), `start_char` (defaults to 0), and `country`. |
| `batch_crawl_urls` | Use instead of calling `crawl_url` more than once. Fetches every page in parallel and returns each one in request order; a failed, blocked, or slow page does not stop the others. | `urls` (required list of 1&ndash;20), optional `reasoning`, `max_chars` per page (defaults to 12000), `start_chars` (URL to offset map for continuing cut pages), and `country`. |
| `package_info` | Look up specific npm, PyPI, crates.io, or Go package metadata including version, downloads, license, and dependencies. Use when you know the package name. | `name` (required package name), optional `reasoning`, and `registry` (npm/pypi/crates/go, defaults to npm). |
| `package_search` | Search for packages by keywords or functionality (e.g., "web framework", "json parser"). Use when you need to find packages that solve a specific problem. | `query` (required search terms), optional `reasoning`, `registry` (npm/pypi/crates/go, defaults to npm), and `max_results` (defaults to 5). |
| `github_repo` | Get GitHub repository health metrics including stars, forks, issues, recent commits, and project details. Use when evaluating open source projects. | `repo` (required, owner/repo or full URL), optional `reasoning` and `include_commits` (defaults to true). |
| `translate_error` | Find Stack Overflow solutions for error messages and stack traces. Auto-detects language/framework, extracts key terms, filters irrelevant results, and prioritizes Stack Overflow solutions. | `error_message` (required stack trace or error text), optional `reasoning`, `language`, `framework`, and `max_results` (defaults to 5). |
| `api_docs` | Auto-discover and crawl official API documentation, then extract overviews, parameters, examples, and related links. | `api_name` and `topic` (required), optional `reasoning` and `max_results` (defaults to 2 pages). |
| `extract_data` | Extract tables, lists, fields, JSON-LD, or auto-detected structured data from HTML pages. | `url` (required), optional `reasoning`, `extract_type`, `selectors`, and `max_items` (defaults to 100). |
| `compare_tech` | Compare 2-5 technologies side-by-side using package, repository, and web evidence. | `technologies` (required list of 2-5 names), optional `reasoning`, `category`, `aspects`, and `max_results_per_tech`. |
| `get_changelog` | Get release notes, identify breaking changes, and provide upgrade guidance. Automatically tries npm and PyPI when the registry is unknown. | `package` (required name), optional `reasoning`, `registry` (defaults to auto), and `max_releases` (defaults to 5). |
| `check_service_status` | Check whether a supported external service has an active incident. | `service` (required name), optional `reasoning`. |

Tool responses are capped at 30,000 characters by default. `crawl_url` returns an exact
`start_char` continuation value when a page is longer than the requested chunk.

The batch tools share one 50,000-character budget across their items: short pages come back
whole and long ones are cut evenly. A cut `batch_crawl_urls` result ends with the exact
arguments that continue every cut page in one more call. Items still running after 45 seconds
are reported as timed out, so the batch returns before typical 60-second client timeouts.

## Resources

MCP Resources provide direct data access via URI templates - perfect for quick lookups without tool calls.

| Resource URI | Description | Example |
| ------------ | ----------- | ------- |
| `package://{registry}/{name}` | Package metadata (version, downloads, license, dependencies) | `package://npm/express` |
| `github://{owner}/{repo}` | Repository info (stars, forks, issues, activity) | `github://facebook/react` |
| `status://{service}` | Service health status | `status://stripe` |
| `changelog://{registry}/{package}` | Release notes and changelogs | `changelog://npm/typescript` |

## Prompts

MCP Prompts are reusable message templates that guide AI assistants through common workflows.

| Prompt | Arguments | Use Case |
| ------ | --------- | -------- |
| `research_package` | `package_name`, `registry` | Evaluate a package before adding it as a dependency |
| `debug_error` | `error_message`, `language` (optional), `framework` (optional) | Debug an error with context and solutions |
| `compare_technologies` | `tech1`, `tech2`, `tech3` (optional), `tech4` (optional), `tech5` (optional) | Compare frameworks, databases, or languages |
| `evaluate_repository` | `owner`, `repo` | Assess a GitHub project's health and activity |
| `check_service_health` | `services` (comma-separated) | Monitor multiple services at once |

## Configuration

Environment variables let you adapt the server without touching code:

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `SEARXNG_BASE_URL` | `http://localhost:2288/search` | Endpoint queried by `web_search`. |
| `SEARXNG_DEFAULT_CATEGORY` | `general` | Category used when none is provided. |
| `SEARXNG_DEFAULT_RESULTS` | `5` | Default number of search hits. |
| `SEARXNG_MAX_RESULTS` | `10` | Hard cap on hits per request. |
| `SEARXNG_CRAWL_MAX_CHARS` | `12000` | Default character budget for each `crawl_url` page. |
| `MCP_MAX_RESPONSE_CHARS` | `30000` | Overall response limit applied to every tool reply. |
| `MCP_MAX_BATCH_RESPONSE_CHARS` | `50000` | Output budget shared by all items of one `batch_crawl_urls` or `batch_web_search` call. |
| `BATCH_TIMEOUT_SECONDS` | `45` | Items of a batch call still running after this many seconds are reported as timed out. |
| `SEARXNG_MCP_USER_AGENT` | `web-research-assistant/0.1` | User-Agent header for outward HTTP calls. |
| `PIXABAY_API_KEY` | _(empty)_ | API key for Pixabay image search. Get free key at [pixabay.com/api/docs](https://pixabay.com/api/docs/). |
| `EXA_API_KEY` | _(empty)_ | API key for Exa AI neural search. Get key at [dashboard.exa.ai](https://dashboard.exa.ai/api-keys). |
| `SEARCH_PROVIDER` | `auto` | Search provider: `exa` (Exa only), `searxng` (SearXNG only), or `auto` (try Exa first, fallback to SearXNG). |
| `MCP_USAGE_LOG` | `~/.config/web-research-assistant/usage.json` | Location for usage analytics data. |

## Development

The codebase is intentionally modular and organized:

```
web-research-assistant/
├── src/searxng_mcp/     # Source code
│   ├── config.py        # Configuration and environment
│   ├── search.py        # SearXNG integration
│   ├── exa.py           # Exa AI neural search client
│   ├── crawler.py       # Scrapling wrapper
│   ├── images.py        # Pixabay client
│   ├── registry.py      # Package registries (npm, PyPI, crates, Go)
│   ├── github.py        # GitHub API client
│   ├── errors.py        # Error parser (language/framework detection)
│   ├── api_docs.py      # API docs discovery (NO hardcoded URLs)
│   ├── tracking.py      # Usage analytics
│   ├── batch.py         # Batch tool helpers (parallel runs, shared output budget)
│   ├── instructions.py  # MCP instructions sent to every agent
│   └── server.py        # MCP server + 16 tools
├── docs/                # Documentation (27 files)
└── [config files]
```

Each module is well under 400 lines, making the codebase easy to understand and extend.

### Usage Analytics

All tools automatically track usage metrics including:
- Tool invocation counts and success rates
- Response times and performance trends
- Common use case patterns (via the `reasoning` parameter)
- Error frequencies and types

Analytics data is stored in `~/.config/web-research-assistant/usage.json`. The optional
`reasoning` parameter improves use-case grouping, but omitting analytics context never blocks
a tool call.

## Documentation

Comprehensive documentation is available in the [`docs/`](docs/) directory:

- **[Project Status](docs/PROJECT_STATUS.md)** - Current status, metrics, roadmap
- **[API Docs Implementation](docs/API_DOCS_IMPLEMENTATION.md)** - NEW tool documentation
- **[Error Translator Design](docs/ERROR_TRANSLATOR_DESIGN.md)** - Error translator details
- **[Tool Ideas Ranked](docs/tool-ideas-ranked.md)** - Prioritization and progress
- **[SearXNG Configuration](docs/SEARXNG_OPTIMAL_CONFIG.md)** - Recommended setup
- **[Quick Start Examples](docs/QUICK_START_EXAMPLES.md)** - Usage examples

See the [docs README](docs/README.md) for a complete index.
