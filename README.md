# Web Research Assistant MCP Server

[![PyPI](https://img.shields.io/pypi/v/web-research-assistant?color=blue)](https://pypi.org/project/web-research-assistant/)
[![Python Version](https://img.shields.io/pypi/pyversions/web-research-assistant)](https://pypi.org/project/web-research-assistant/)
[![License](https://img.shields.io/github/license/elad12390/web-research-assistant)](https://github.com/elad12390/web-research-assistant/blob/main/LICENSE)
[![CI](https://github.com/elad12390/web-research-assistant/workflows/CI/badge.svg)](https://github.com/elad12390/web-research-assistant/actions)

Comprehensive Model Context Protocol (MCP) server that provides web research and discovery capabilities.
Includes 13 tools for searching, crawling, and analyzing web content, powered by your local Docker SearXNG 
instance, the [`crawl4ai`](https://github.com/unclecode/crawl4ai) project, and Pixabay API:

1. `web_search` &mdash; federated search across multiple engines via SearXNG
2. `search_examples` &mdash; find code examples, tutorials, and articles (defaults to recent content)
3. `search_images` &mdash; find high-quality stock photos, illustrations, and vectors via Pixabay
4. `crawl_url` &mdash; full page content extraction with advanced crawling
5. `package_info` &mdash; detailed package metadata from npm, PyPI, crates.io, Go
6. `package_search` &mdash; discover packages by keywords and functionality  
7. `github_repo` &mdash; repository health metrics and development activity
8. `translate_error` &mdash; find solutions for error messages and stack traces from Stack Overflow (auto-detects CORS, fetch, and web errors)
9. `api_docs` &mdash; auto-discover and crawl official API documentation with examples (works for any API - no hardcoded URLs)
10. `extract_data` &mdash; extract structured data (tables, lists, fields, JSON-LD) from web pages with automatic detection
11. `compare_tech` &mdash; compare technologies side-by-side with NPM downloads, GitHub stars, and aspect analysis (React vs Vue, PostgreSQL vs MongoDB, etc.)
12. `get_changelog` &mdash; **NEW!** Get release notes and changelogs with breaking change detection (upgrade safely from version X to Y)
13. `check_service_status` &mdash; **NEW!** Instant health checks for 25+ services (Stripe, AWS, GitHub, OpenAI, etc.) - "Is it down or just me?"

All tools feature comprehensive error handling, response size limits, usage tracking, and clear documentation
for optimal AI agent integration.

## Quick Start

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

- **Pixabay API key** for image search - [Get free key](https://pixabay.com/api/docs/)
- **Playwright browsers** for advanced crawling (auto-installed with `crawl4ai-setup`)

### Developer Setup (if running from source)

```bash
uv tool install uv  # if you do not already have uv
uv sync              # creates the virtual environment
uv run crawl4ai-setup  # installs Chromium for crawl4ai
```

> You can also use `pip install -r requirements.txt` if you prefer pip over uv.

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

### Claude Desktop Configuration

Add the server to `~/Library/Application Support/Claude/claude_desktop_config.json`:

#### Option 1: Using uvx (Recommended - No local installation needed!)

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

#### Option 2: Using installed package

```json
{
  "mcpServers": {
    "web-research-assistant": {
      "command": "web-research-assistant"
    }
  }
}
```

#### Option 3: Running from source (development)

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

Restart Claude Desktop afterwards. The MCP slider will show all available tools.

## Tool behavior

| Tool | When to use | Arguments |
| ---- | ----------- | --------- |
| `web_search` | Use first to gather recent information and URLs from SearXNG. Returns 1&ndash;10 ranked snippets with clickable URLs. | `query` (required), `reasoning` (required), optional `category` (defaults to `general`), and `max_results` (defaults to 5). |
| `search_examples` | Find code examples, tutorials, and technical articles. Optimized for technical content with optional time filtering. Perfect for learning APIs or finding usage patterns. | `query` (required, e.g., "Python async examples"), `reasoning` (required), `content_type` (code/articles/both, defaults to both), `time_range` (day/week/month/year/all, defaults to all), optional `max_results` (defaults to 5). |
| `search_images` | Find high-quality royalty-free stock images from Pixabay. Returns photos, illustrations, or vectors. Requires `PIXABAY_API_KEY` environment variable. | `query` (required, e.g., "mountain landscape"), `reasoning` (required), `image_type` (all/photo/illustration/vector, defaults to all), `orientation` (all/horizontal/vertical, defaults to all), optional `max_results` (defaults to 10). |
| `crawl_url` | Call immediately after search when you need the actual article body for quoting, summarizing, or extracting data. | `url` (required), `reasoning` (required), optional `max_chars` (defaults to 8000 characters). |
| `package_info` | Look up specific npm, PyPI, crates.io, or Go package metadata including version, downloads, license, and dependencies. Use when you know the package name. | `name` (required package name), `reasoning` (required), `registry` (npm/pypi/crates/go, defaults to npm). |
| `package_search` | Search for packages by keywords or functionality (e.g., "web framework", "json parser"). Use when you need to find packages that solve a specific problem. | `query` (required search terms), `reasoning` (required), `registry` (npm/pypi/crates/go, defaults to npm), optional `max_results` (defaults to 5). |
| `github_repo` | Get GitHub repository health metrics including stars, forks, issues, recent commits, and project details. Use when evaluating open source projects. | `repo` (required, owner/repo or full URL), `reasoning` (required), optional `include_commits` (defaults to true). |
| `translate_error` | Find Stack Overflow solutions for error messages and stack traces. Auto-detects language/framework, extracts key terms (CORS, map, undefined, etc.), filters irrelevant results, and prioritizes Stack Overflow solutions. Handles web-specific errors (CORS, fetch). | `error_message` (required stack trace or error text), `reasoning` (required), optional `language` (auto-detected), optional `framework` (auto-detected), optional `max_results` (defaults to 5). |
| `api_docs` | Auto-discover and crawl official API documentation. Dynamically finds docs URLs using patterns (docs.{api}.com, {api}.com/docs, etc.), searches for specific topics, crawls pages, and extracts overview, parameters, examples, and related links. Works for ANY API - no hardcoded URLs. Perfect for API integration and learning. | `api_name` (required, e.g., "stripe", "react"), `topic` (required, e.g., "create customer", "hooks"), `reasoning` (required), optional `max_results` (defaults to 2 pages). |
| `extract_data` | Extract structured data from HTML pages. Supports tables, lists, fields (via CSS selectors), JSON-LD, and auto-detection. Returns clean JSON output. More efficient than parsing full page text. Perfect for scraping pricing tables, package specs, release notes, or any structured content. | `url` (required), `reasoning` (required), `extract_type` (table/list/fields/json-ld/auto, defaults to auto), optional `selectors` (CSS selectors for fields mode), optional `max_items` (defaults to 100). |
| `compare_tech` | Compare 2-5 technologies side-by-side. Auto-detects category (framework/database/language) and gathers data from NPM, GitHub, and web search. Returns structured comparison with popularity metrics (downloads, stars), performance insights, and best-use summaries. Fast parallel processing (3-4s). | `technologies` (required list of 2-5 names), `reasoning` (required), optional `category` (auto-detects if not provided), optional `aspects` (auto-selected by category), optional `max_results_per_tech` (defaults to 3). |
| `get_changelog` | **NEW!** Get release notes and changelogs for package upgrades. Fetches GitHub releases, highlights breaking changes, and provides upgrade recommendations. Answers "What changed in version X → Y?" and "Are there breaking changes?" Perfect for planning dependency updates. | `package` (required name), `reasoning` (required), optional `registry` (npm/pypi/auto, defaults to auto), optional `max_releases` (defaults to 5). |
| `check_service_status` | **NEW!** Instantly check if external services are experiencing issues. Covers 25+ popular services (Stripe, AWS, GitHub, OpenAI, Vercel, etc.). Returns operational status, current incidents, and component health. Critical for production debugging - know immediately if the issue is external. Response time < 2s. | `service` (required name, e.g., "stripe", "aws"), `reasoning` (required). |

Results are automatically trimmed (default 8 KB) so they stay well within MCP
response expectations. If truncation happens, the text ends with a note reminding the
model that more detail is available on request.

## Configuration

Environment variables let you adapt the server without touching code:

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `SEARXNG_BASE_URL` | `http://localhost:2288/search` | Endpoint queried by `web_search`. |
| `SEARXNG_DEFAULT_CATEGORY` | `general` | Category used when none is provided. |
| `SEARXNG_DEFAULT_RESULTS` | `5` | Default number of search hits. |
| `SEARXNG_MAX_RESULTS` | `10` | Hard cap on hits per request. |
| `SEARXNG_CRAWL_MAX_CHARS` | `8000` | Default character budget for `crawl_url`. |
| `MCP_MAX_RESPONSE_CHARS` | `8000` | Overall response limit applied to every tool reply. |
| `SEARXNG_MCP_USER_AGENT` | `web-research-assistant/0.1` | User-Agent header for outward HTTP calls. |
| `PIXABAY_API_KEY` | _(empty)_ | API key for Pixabay image search. Get free key at [pixabay.com/api/docs](https://pixabay.com/api/docs/). |
| `MCP_USAGE_LOG` | `~/.config/web-research-assistant/usage.json` | Location for usage analytics data. |

## Development

The codebase is intentionally modular and organized:

```
web-research-assistant/
├── src/searxng_mcp/     # Source code
│   ├── config.py        # Configuration and environment
│   ├── search.py        # SearXNG integration
│   ├── crawler.py       # Crawl4AI wrapper
│   ├── images.py        # Pixabay client
│   ├── registry.py      # Package registries (npm, PyPI, crates, Go)
│   ├── github.py        # GitHub API client
│   ├── errors.py        # Error parser (language/framework detection)
│   ├── api_docs.py      # API docs discovery (NO hardcoded URLs)
│   ├── tracking.py      # Usage analytics
│   └── server.py        # MCP server + 9 tools
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

Analytics data is stored in `~/.config/web-research-assistant/usage.json` and can be analyzed
to optimize tool usage and identify patterns. Each tool requires a `reasoning` parameter
that helps categorize why tools are being used, enabling better analytics and insights.

**Note:** As of the latest update, the `reasoning` parameter is **required** for all tools (previously optional with defaults). This ensures meaningful analytics data collection.

## Documentation

Comprehensive documentation is available in the [`docs/`](docs/) directory:

- **[Project Status](docs/PROJECT_STATUS.md)** - Current status, metrics, roadmap
- **[API Docs Implementation](docs/API_DOCS_IMPLEMENTATION.md)** - NEW tool documentation
- **[Error Translator Design](docs/ERROR_TRANSLATOR_DESIGN.md)** - Error translator details
- **[Tool Ideas Ranked](docs/tool-ideas-ranked.md)** - Prioritization and progress
- **[SearXNG Configuration](docs/SEARXNG_OPTIMAL_CONFIG.md)** - Recommended setup
- **[Quick Start Examples](docs/QUICK_START_EXAMPLES.md)** - Usage examples

See the [docs README](docs/README.md) for a complete index.
