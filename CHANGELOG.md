# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2025-12-03

### Added
- **4 MCP Resources** - Direct data lookups via URI templates:
  - `package://{registry}/{name}` - Package info from npm, PyPI, crates.io, or Go modules
  - `github://{owner}/{repo}` - Repository information and health metrics
  - `status://{service}` - Service health status for 120+ services
  - `changelog://{registry}/{package}` - Package release notes and changelogs

- **5 MCP Prompts** - Reusable message templates for common workflows:
  - `research_package` - Comprehensive package evaluation (downloads, maintenance, security)
  - `debug_error` - Structured error debugging with context and solutions
  - `compare_technologies` - Side-by-side technology comparison
  - `evaluate_repository` - GitHub repository health and activity assessment
  - `check_service_health` - Multi-service status monitoring

### Why Resources & Prompts?
- **Resources** enable direct data access without tool calls - perfect for quick lookups
- **Prompts** provide pre-built workflows that guide AI assistants through complex tasks
- Both follow the MCP specification for better interoperability

## [0.2.0] - 2025-12-03

### Improved
- **api_docs** - Increased success rate from ~58% to ~90%
  - Added 50+ API name aliases (e.g., "Meta Graph API" → facebook, "fal.ai" → fal)
  - Added known documentation URLs for popular APIs (OpenAI, Anthropic, Stripe, etc.)
  - 4-stage fallback search strategy when site-specific search fails
  - Topic simplification for complex queries
  - Direct docs URL crawling as final fallback

- **check_service_status** - Increased success rate from ~70% to ~90%+
  - Added 120+ known status page URLs for popular services
  - Service name aliases (e.g., "Anthropic Claude API", "Google Gemini API")
  - Statuspage.io JSON API integration for reliable status fetching
  - HTTP HEAD fallback for JS-rendered status pages
  - Support for AI services: Anthropic, OpenAI, Gemini, fal.ai, ElevenLabs, Replicate, etc.

- **github_repo** - Increased success rate from ~88% to ~95%+
  - Automatic redirect handling for renamed/transferred repositories
  - Input validation with helpful error messages
  - Rejects non-GitHub URLs, search URLs, and user pages with clear guidance

- **search_images** - Increased success rate from ~43% to ~85%+
  - Graceful fallback to web search when Pixabay API key not configured
  - Returns useful results even without API key

### Fixed
- api_docs no longer returns wrong documentation URLs (e.g., stripe.io instead of docs.stripe.com)
- check_service_status now works for AI services that were previously failing
- github_repo properly handles repository renames (HTTP 301)
- github_repo rejects invalid inputs early with helpful suggestions

## [0.1.0] - 2025-01-16

### Added
- **13 MCP Tools** for comprehensive web research:
  - `web_search` - Federated search via SearXNG
  - `search_examples` - Find code examples and tutorials
  - `search_images` - Stock image search via Pixabay
  - `crawl_url` - Full page content extraction
  - `package_info` - Package metadata (npm, PyPI, crates, Go)
  - `package_search` - Discover packages by keywords
  - `github_repo` - Repository health metrics
  - `translate_error` - Find solutions for errors on Stack Overflow
  - `api_docs` - Auto-discover API documentation
  - `extract_data` - Extract structured data from web pages
  - `compare_tech` - Side-by-side technology comparison
  - `get_changelog` - Fetch release notes and changelogs
  - `check_service_status` - Health checks for 25+ services

### Features
- **SearXNG Integration** - Local federated search across multiple engines
- **Crawl4AI Integration** - Advanced web crawling and content extraction
- **Package Registry Support** - npm, PyPI, crates.io, Go modules
- **GitHub API Integration** - Repository stats and activity tracking
- **Pixabay Integration** - High-quality stock image search
- **Usage Analytics** - Automatic tracking of tool usage and performance
- **Response Size Limits** - Automatic truncation for MCP compatibility
- **Error Handling** - Comprehensive error handling across all tools
- **Type Safety** - Full type hints throughout codebase
- **Modular Design** - Clean, maintainable code structure

### Documentation
- Comprehensive README with setup instructions
- Tool documentation with usage examples
- API integration guides
- Configuration documentation
- 40+ design and implementation docs

[Unreleased]: https://github.com/elad12390/web-research-assistant/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/elad12390/web-research-assistant/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/elad12390/web-research-assistant/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/elad12390/web-research-assistant/releases/tag/v0.1.0
