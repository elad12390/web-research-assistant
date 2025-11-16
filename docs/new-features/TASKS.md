# Development Tasks - SearXNG MCP Server

**Last Updated:** 2025-01-15  
**Update this file whenever you start/complete/block on a task!**

---

## Task Status Legend

- 🔴 **Not Started** - No work begun
- 🟡 **In Progress** - Active development
- 🟢 **Complete** - Done and tested
- ⚫ **Blocked** - Waiting on dependency or decision
- 🔵 **Testing** - Implementation done, needs verification

---

## Phase 1: Core Infrastructure ✅

### Task #0: Project Setup
**Status:** 🟢 Complete  
**Priority:** P0 (Critical)  
**Complexity:** Low  
**Estimated Time:** 2-3 hours  
**Actual Time:** ~3 hours  

**Description:**
Set up minimal MCP server with SearXNG integration and crawl4ai page fetching.

**Implementation Checklist:**
- [x] Create modular package structure (`searxng_mcp/`)
- [x] Implement `config.py` with env-based settings
- [x] Implement `search.py` with SearXNG JSON API client
- [x] Implement `crawler.py` with crawl4ai wrapper
- [x] Implement `server.py` with FastMCP and two tools
- [x] Add `pyproject.toml` with dependencies and console script
- [x] Write `README.md` with setup/usage instructions
- [x] Register in OpenCode global config (`~/.config/opencode/opencode.json`)
- [x] Test with `uv run searxng-mcp`

**Completion Notes:**
- Successfully tested with OpenCode
- Response limits work correctly (8KB default)
- Both tools (`web_search`, `crawl_url`) operational
- Environment variables properly override defaults

**Files Modified:**
- Created: `searxng_mcp/` package
- Created: `pyproject.toml`, `requirements.txt`, `README.md`
- Modified: `~/.config/opencode/opencode.json`

---

## Phase 2: High-Impact Tools 🚧

### Task #1: Package Registry Search Tool
**Status:** 🟢 Complete  
**Priority:** P1 (High)  
**Complexity:** Medium  
**Estimated Time:** 4-6 hours  
**Actual Time:** ~2 hours  
**Completed:** 2025-01-15  

**Description:**
Add tool to search npm, PyPI, crates.io, and Go packages. Return structured info: downloads, last update, dependencies, security advisories.

**User Story:**
As a developer, I want to quickly check package details without leaving my coding environment, so I can evaluate libraries faster.

**Implementation Plan:**

1. **Create module:** `searxng_mcp/registry.py`
   - Class: `PackageRegistryClient`
   - Methods:
     - `async search_npm(name: str) -> PackageInfo`
     - `async search_pypi(name: str) -> PackageInfo`
     - `async search_crates(name: str) -> PackageInfo`
     - `async search_go(name: str) -> PackageInfo`
   - Use official registry APIs (not scraping)

2. **Add constants to config.py:**
   ```python
   NPM_REGISTRY_URL = "https://registry.npmjs.org"
   PYPI_API_URL = "https://pypi.org/pypi"
   CRATES_API_URL = "https://crates.io/api/v1"
   GO_PROXY_URL = "https://proxy.golang.org"
   ```

3. **Add tool to server.py:**
   ```python
   @mcp.tool()
   async def package_info(
       name: str,
       registry: Literal["npm", "pypi", "crates", "go"] = "npm"
   ) -> str:
       """Fetch package information from registries."""
   ```

4. **Response format:**
   ```
   Package: express (npm)
   Version: 4.18.2 (latest)
   Downloads: 25M/week
   Last Updated: 2023-12-15
   License: MIT
   Dependencies: 30
   Security: ✅ No known vulnerabilities
   Repository: https://github.com/expressjs/express
   Description: Fast, unopinionated, minimalist web framework
   ```

**Testing Checklist:**
- [x] npm package lookup works
- [x] PyPI package lookup works
- [x] crates.io package lookup works
- [x] Go module lookup works
- [x] Handles non-existent packages gracefully
- [x] Response fits within 8KB limit
- [x] Error handling for network failures
- [ ] Caching for repeated lookups (deferred)

**Completion Notes:**
- All four registries (npm, PyPI, crates.io, Go) working perfectly
- Added weekly download stats for npm (51M/week for express)
- Proper error handling for 404s with helpful messages
- Response formatting clean and readable
- Time-ago formatting (e.g., "7 months ago") improves UX
- No new dependencies required (used existing httpx)

**Files Created:**
- `searxng_mcp/registry.py` (237 lines) - Registry client with all 4 APIs
- Updated: `searxng_mcp/server.py` - Added `package_info` tool

**Performance:**
- npm lookups: ~1-2s
- PyPI lookups: ~1s
- crates.io lookups: ~1s
- Go lookups: ~1-2s

**Related Files:**
- Spec: `docs/new-features/package-registry/SPEC.md`
- Tests: Manual testing completed, unit tests optional

---

### Task #2: Error Translator Tool
**Status:** 🔴 Not Started  
**Priority:** P1 (High)  
**Complexity:** High  
**Estimated Time:** 8-10 hours  
**Assigned To:** Unassigned  

**Description:**
Tool that takes error messages/stack traces and returns ranked solutions from Stack Overflow, GitHub issues, and documentation.

**User Story:**
As a developer hitting an error, I want instant ranked solutions instead of manually searching Stack Overflow and clicking through multiple answers.

**Implementation Plan:**

1. **Create module:** `searxng_mcp/error_solver.py`
   - Class: `ErrorSolver`
   - Methods:
     - `async analyze_error(error_text: str, context: dict) -> List[Solution]`
     - `async search_stackoverflow(error_sig: str) -> List[SOAnswer]`
     - `async search_github_issues(error_sig: str) -> List[GitHubIssue]`

2. **Error signature extraction:**
   - Strip file paths, line numbers (too specific)
   - Keep error type, core message
   - Identify language/framework from stack trace

3. **Ranking algorithm:**
   - Stack Overflow: accepted answer > votes > recency
   - GitHub: closed issues > issue reactions > recency
   - Filter: solutions must be <2 years old (default)

4. **Add tool to server.py:**
   ```python
   @mcp.tool()
   async def solve_error(
       error: str,
       language: str = "auto",
       max_solutions: int = 3
   ) -> str:
       """Find solutions for error messages/stack traces."""
   ```

5. **Response format:**
   ```
   Error Analysis:
   Type: TypeError
   Language: Python
   Likely Cause: NoneType attribute access
   
   Solution #1 (Stack Overflow - Accepted, 234 votes)
   Check for None before accessing attributes:
   if obj is not None:
       obj.method()
   Source: https://stackoverflow.com/...
   
   Solution #2 (GitHub Issue - Closed)
   [Solution details...]
   ```

**Testing Checklist:**
- [ ] Extracts error signatures correctly
- [ ] Python errors work
- [ ] JavaScript errors work
- [ ] Type errors, syntax errors, runtime errors all handled
- [ ] Solutions ranked appropriately
- [ ] No duplicate solutions
- [ ] Handles malformed error text gracefully
- [ ] Response fits size limits

**Dependencies:**
- May need: `beautifulsoup4` (already in crawl4ai deps)
- May need: Stack Overflow API token (optional, higher rate limits)

**Blockers:**
- Need to decide: Use Stack Overflow API or scrape? (API has rate limits but cleaner)

**Related Files:**
- Spec: `docs/new-features/error-translator/SPEC.md`
- Tests: `tests/test_error_solver.py`

---

### Task #3: GitHub Repository Info Tool
**Status:** 🟢 Complete  
**Priority:** P2 (Medium)  
**Complexity:** Low  
**Estimated Time:** 3-4 hours  
**Actual Time:** ~1.5 hours  
**Completed:** 2025-01-15  

**Description:**
Tool to fetch GitHub repo metadata: stars, issues, recent commits, README, contributors.

**User Story:**
As a developer evaluating a library, I want quick repo health metrics without opening GitHub in browser.

**Implementation Plan:**

1. **Create module:** `searxng_mcp/github.py`
   - Class: `GitHubClient`
   - Use GitHub REST API (no auth needed for public repos, but support token for rate limits)
   - Methods:
     - `async get_repo_info(owner: str, repo: str) -> RepoInfo`
     - `async get_recent_commits(owner: str, repo: str, count: int) -> List[Commit]`

2. **Add constants to config.py:**
   ```python
   GITHUB_API_URL = "https://api.github.com"
   GITHUB_TOKEN = _env_str("GITHUB_TOKEN", "")  # Optional, for higher rate limits
   ```

3. **Add tool to server.py:**
   ```python
   @mcp.tool()
   async def github_repo(
       repo: str,  # Format: "owner/repo" or full URL
       include_commits: bool = True
   ) -> str:
       """Fetch GitHub repository information and health metrics."""
   ```

4. **Response format:**
   ```
   Repository: unclecode/crawl4ai
   Stars: 15.2k | Forks: 1.3k | Watchers: 234
   License: Apache-2.0
   Last Updated: 2 hours ago
   Open Issues: 45 | Open PRs: 12
   
   Recent Activity (Last 5 Commits):
   - [2h ago] feat: add webhook support (unclecode)
   - [1d ago] fix: memory leak in crawler (contributor)
   ...
   
   Description: Open-source LLM Friendly Web Crawler & Scraper
   Homepage: https://crawl4ai.com
   ```

**Testing Checklist:**
- [x] Parses "owner/repo" format
- [x] Parses full GitHub URLs
- [x] Works without GitHub token
- [x] Respects rate limits (60/hr without token, 5000/hr with)
- [x] Handles non-existent repos
- [x] Handles private repos (returns "not accessible")
- [x] Response fits size limits

**Completion Notes:**
- Full GitHub REST API integration working perfectly
- Supports both `owner/repo` and full URL formats
- Returns comprehensive repo health metrics: stars, forks, issues, PRs, language, license
- Includes recent commit history (optional)
- Proper error handling for 404s and rate limits
- Optional GitHub token support via `GITHUB_TOKEN` env var
- Response time: ~2-3s per request

**Files Created:**
- `searxng_mcp/github.py` (209 lines) - Complete GitHub API client
- Updated: `searxng_mcp/server.py` - Added `github_repo` tool

**Performance:**
- Repo info: ~1-2s
- With commits: ~2-3s
- Rate limits: 60 req/hr (no token), 5000 req/hr (with token)

**Related Files:**
- Spec: `docs/new-features/github-info/SPEC.md`
- Tests: Manual testing completed

---

### Task #4: Structured Data Extraction Enhancement
**Status:** 🔴 Not Started  
**Priority:** P2 (Medium)  
**Complexity:** Medium  
**Estimated Time:** 5-7 hours  
**Assigned To:** Unassigned  

**Description:**
Enhance existing `crawl_url` or add new tool to extract structured data (tables, prices, specs) using CSS selectors or LLM extraction.

**User Story:**
As a developer, I want to extract specific fields from web pages (e.g., "get all prices from this e-commerce page") without processing full page markdown.

**Implementation Plan:**

1. **Enhance crawler.py:**
   - Add method: `async extract_structured(url: str, schema: dict) -> dict`
   - Use crawl4ai's built-in extraction strategies:
     - `JsonCssExtractionStrategy` for CSS selector-based extraction
     - `LLMExtractionStrategy` for AI-powered extraction (optional)

2. **Add tool to server.py:**
   ```python
   @mcp.tool()
   async def extract_data(
       url: str,
       fields: str,  # JSON string describing what to extract
       method: Literal["css", "llm"] = "css"
   ) -> str:
       """Extract structured data from a web page."""
   ```

3. **Example usage:**
   ```
   extract_data(
       url="https://example.com/products",
       fields='{"name": "h2.product-title", "price": "span.price"}',
       method="css"
   )
   
   Returns:
   [
     {"name": "Product A", "price": "$29.99"},
     {"name": "Product B", "price": "$39.99"}
   ]
   ```

**Testing Checklist:**
- [ ] CSS selector extraction works
- [ ] Handles missing elements gracefully
- [ ] Works with tables
- [ ] Works with lists
- [ ] LLM extraction works (if implemented)
- [ ] Response is valid JSON
- [ ] Handles extraction failures

**Dependencies:**
- Already have crawl4ai with extraction support
- Optional: LLM provider API key for LLM extraction mode

**Blockers:**
- Need to decide: CSS-only first, or include LLM extraction from start?

**Related Files:**
- Spec: `docs/new-features/structured-extract/SPEC.md`
- Tests: `tests/test_extraction.py`

---

### Task #5: API Explorer Tool
**Status:** 🔴 Not Started  
**Priority:** P2 (Medium)  
**Complexity:** High  
**Estimated Time:** 8-10 hours  
**Assigned To:** Unassigned  

**Description:**
Tool to fetch OpenAPI/Swagger specs, generate example requests, test endpoints.

**User Story:**
As a developer integrating with an API, I want to explore endpoints and see example requests without leaving my environment.

**Implementation Plan:**

1. **Create module:** `searxng_mcp/api_explorer.py`
   - Class: `APIExplorer`
   - Methods:
     - `async fetch_openapi_spec(url: str) -> dict`
     - `async list_endpoints(spec: dict) -> List[Endpoint]`
     - `async generate_example(endpoint: str, method: str) -> str`
     - `async test_endpoint(url: str, method: str, headers: dict) -> Response`

2. **Add tool to server.py:**
   ```python
   @mcp.tool()
   async def explore_api(
       spec_url: str,  # URL to OpenAPI/Swagger JSON
       endpoint: str = "",  # Optional: specific endpoint to explore
   ) -> str:
       """Explore API using OpenAPI/Swagger specification."""
   ```

3. **Response format:**
   ```
   API: Stripe API v1
   Base URL: https://api.stripe.com/v1
   Authentication: Bearer token
   
   Available Endpoints (showing 5 of 234):
   
   1. POST /v1/charges
      Description: Create a charge
      Required: amount, currency
      Example:
      curl -X POST https://api.stripe.com/v1/charges \
        -H "Authorization: Bearer sk_test_..." \
        -d amount=2000 \
        -d currency=usd
   
   2. GET /v1/customers/{id}
   ...
   ```

**Testing Checklist:**
- [ ] Fetches OpenAPI 3.0 specs
- [ ] Fetches Swagger 2.0 specs
- [ ] Lists all endpoints
- [ ] Generates valid curl examples
- [ ] Handles authentication schemes
- [ ] Identifies required vs optional params
- [ ] Response fits size limits
- [ ] Handles invalid/malformed specs

**Dependencies:**
- May need: `pydantic` for spec validation (already transitive dep of crawl4ai)
- May need: `openapi-spec-validator` (optional)

**Blockers:**
- None

**Related Files:**
- Spec: `docs/new-features/api-explorer/SPEC.md`
- Tests: `tests/test_api_explorer.py`

---

## Phase 3: Advanced Features 📅

### Task #6: Multi-Source Aggregation
**Status:** 🔴 Not Started  
**Priority:** P3 (Low)  
**Complexity:** Medium  
**Estimated Time:** 6-8 hours  

**Description:**
Tool that searches multiple sources, crawls top results, and summarizes findings.

**Deferred:** Will design after Phase 2 completion.

---

### Task #7: Site-Specific Search Filters
**Status:** 🔴 Not Started  
**Priority:** P3 (Low)  
**Complexity:** Low  
**Estimated Time:** 2-3 hours  

**Description:**
Add `site:` parameter to `web_search` tool for domain-scoped queries.

**Deferred:** Will implement after Phase 2.

---

### Task #8: Security/CVE Monitoring
**Status:** 🔴 Not Started  
**Priority:** P3 (Low)  
**Complexity:** High  
**Estimated Time:** 10-12 hours  

**Description:**
Tool to check CVE databases and security advisories for specific tech stacks.

**Deferred:** Requires more research into CVE APIs.

---

## Notes & Decisions

### 2025-01-15: Initial Planning
- Prioritized based on daily usage frequency analysis
- Package registry ranked #1 for quick win (high frequency, low complexity)
- Error translator ranked high for impact but higher complexity
- GitHub info easy to implement, good ROI
- Structured extraction builds on existing crawler
- API explorer more complex but very useful for integration work

### Future Considerations
- Add caching layer for frequently accessed data (npm packages, GitHub repos)
- Consider rate limiting to respect external API quotas
- May want to add telemetry to track which tools are most used
- Should add comprehensive error logging for debugging

---

**Remember:** Update this file every time you start, progress, or complete a task!
