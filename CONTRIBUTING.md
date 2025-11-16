# Contributing to Web Research Assistant

Thanks for your interest in contributing! This MCP server helps AI agents perform comprehensive web research.

## Getting Started

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR-USERNAME/web-research-assistant.git
   cd web-research-assistant
   ```

2. **Set up your development environment**
   ```bash
   # Install uv if you don't have it
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Install dependencies (including dev dependencies)
   uv sync --all-extras
   
   # Install Playwright browsers for crawl4ai
   uv run crawl4ai-setup
   ```

3. **Set up SearXNG**
   You need a running SearXNG instance on `http://localhost:2288`. See the [README](README.md) for setup instructions.

4. **Optional: Get API keys**
   - Pixabay API key for image search: https://pixabay.com/api/docs/
   - GitHub token for higher rate limits (optional)

## Development Workflow

1. **Create a branch** for your feature or bugfix
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Keep modules under 400 lines for maintainability
   - Add type hints to all functions
   - Update docstrings
   - Follow existing code style (we use ruff for formatting)

3. **Run tests**
   ```bash
   uv run pytest tests/ -v
   ```

4. **Run linting and formatting**
   ```bash
   # Format code
   uv run ruff format src/
   
   # Check for issues
   uv run ruff check src/
   
   # Type checking (optional but recommended)
   uv run mypy src/ --ignore-missing-imports
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add awesome new feature"
   ```
   
   We follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` new features
   - `fix:` bug fixes
   - `docs:` documentation changes
   - `refactor:` code refactoring
   - `test:` adding tests
   - `chore:` maintenance tasks

6. **Push and create a Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

## Project Structure

```
web-research-assistant/
├── src/searxng_mcp/     # Source code
│   ├── server.py        # MCP server + tool definitions
│   ├── search.py        # SearXNG integration
│   ├── crawler.py       # Crawl4AI wrapper
│   ├── registry.py      # Package registries (npm, PyPI, etc.)
│   ├── github.py        # GitHub API client
│   ├── images.py        # Pixabay client
│   ├── errors.py        # Error translator
│   ├── api_docs.py      # API docs discovery
│   ├── extractor.py     # Structured data extraction
│   ├── comparison.py    # Tech comparison
│   ├── changelog.py     # Changelog fetcher
│   ├── service_health.py # Service status checker
│   ├── tracking.py      # Usage analytics
│   └── config.py        # Configuration
├── tests/               # Test suite
└── docs/                # Documentation
```

## Adding New Tools

To add a new MCP tool:

1. **Create a new module** in `src/searxng_mcp/` if needed
2. **Add the tool** to `server.py` using `@mcp.tool()` decorator
3. **Include error handling** and response size limits
4. **Add usage tracking** via `tracker.track_tool_use()`
5. **Update README.md** with tool documentation
6. **Add tests** in `tests/`

Example:
```python
@mcp.tool()
async def my_new_tool(
    query: Annotated[str, "Search query"],
    reasoning: Annotated[str, "Why you need this information"]
) -> str:
    """Tool description here."""
    try:
        tracker.track_tool_use("my_new_tool", reasoning=reasoning)
        # Your implementation
        result = await do_something(query)
        return clamp_text(result, MAX_RESPONSE_CHARS)
    except Exception as e:
        tracker.track_tool_use("my_new_tool", reasoning=reasoning, success=False)
        return f"Error: {str(e)}"
```

## Testing

- Write tests for new features in `tests/`
- Tests use real API calls (integration tests)
- Run tests: `uv run pytest tests/ -v`
- Check coverage: `uv run pytest --cov=src/searxng_mcp --cov-report=html`

## Code Style

- **Formatting**: We use `ruff format` (auto-formatted)
- **Linting**: We use `ruff check` (catches common issues)
- **Type hints**: All functions should have type annotations
- **Docstrings**: All public functions and classes should be documented
- **Line length**: 100 characters max
- **Imports**: Organized with `from __future__ import annotations` at the top

## Documentation

- Update `README.md` if you add new features or change setup steps
- Add design docs to `docs/` for major features
- Keep examples simple and runnable

## Questions?

- Open an issue: https://github.com/elad12390/web-research-assistant/issues
- Check existing issues and discussions first

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
