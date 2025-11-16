# Package Registry Search - Feature Specification

**Status:** Not Started  
**Priority:** P1 (Highest)  
**Assigned:** Unassigned  
**Created:** 2025-01-15

---

## Overview

Add MCP tool to search package registries (npm, PyPI, crates.io, Go modules) and return structured package information including downloads, versions, dependencies, and security status.

## User Story

**As a** developer evaluating libraries  
**I want** quick package metadata lookup  
**So that** I can assess quality/security without leaving my coding environment

## Success Criteria

- [ ] Works for npm packages
- [ ] Works for PyPI packages  
- [ ] Works for crates.io packages
- [ ] Works for Go modules
- [ ] Response time <3s per query
- [ ] Handles non-existent packages gracefully
- [ ] Returns structured, readable output
- [ ] Fits within MCP response limits (8KB)

## Technical Design

### API Endpoints

**npm:**
- Endpoint: `https://registry.npmjs.org/<package-name>`
- Returns: JSON with all versions, metadata
- Rate limit: None (public API)

**PyPI:**
- Endpoint: `https://pypi.org/pypi/<package-name>/json`
- Returns: JSON with releases, metadata
- Rate limit: None (public API)

**crates.io:**
- Endpoint: `https://crates.io/api/v1/crates/<crate-name>`
- Returns: JSON with crate metadata
- Rate limit: Documented at https://crates.io/data-access

**Go:**
- Endpoint: `https://proxy.golang.org/<module>/@latest`
- Returns: Module info, version
- Rate limit: None (public proxy)

### Implementation

**Module:** `searxng_mcp/registry.py`

```python
from dataclasses import dataclass
from typing import Optional, List
import httpx

@dataclass
class PackageInfo:
    name: str
    registry: str
    version: str
    description: str
    license: Optional[str]
    downloads: Optional[str]  # "25M/week" format
    last_updated: str
    repository: Optional[str]
    dependencies_count: Optional[int]
    security_issues: int
    homepage: Optional[str]

class PackageRegistryClient:
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self._headers = {"User-Agent": USER_AGENT}
    
    async def search_npm(self, name: str) -> PackageInfo:
        """Fetch npm package info."""
        # Implementation
    
    async def search_pypi(self, name: str) -> PackageInfo:
        """Fetch PyPI package info."""
        # Implementation
    
    async def search_crates(self, name: str) -> PackageInfo:
        """Fetch crates.io package info."""
        # Implementation
    
    async def search_go(self, module: str) -> PackageInfo:
        """Fetch Go module info."""
        # Implementation
```

**Tool Definition:**

```python
@mcp.tool()
async def package_info(
    name: Annotated[str, "Package or module name to look up"],
    registry: Annotated[
        Literal["npm", "pypi", "crates", "go"],
        "Package registry to search"
    ] = "npm"
) -> str:
    """
    Look up package information from npm, PyPI, crates.io, or Go modules.
    
    Returns version, downloads, license, dependencies, security status, and more.
    Use this to quickly evaluate libraries before adding them to your project.
    """
    try:
        if registry == "npm":
            info = await registry_client.search_npm(name)
        elif registry == "pypi":
            info = await registry_client.search_pypi(name)
        elif registry == "crates":
            info = await registry_client.search_crates(name)
        else:  # go
            info = await registry_client.search_go(name)
        
        return format_package_info(info)
    except Exception as exc:
        return f"Failed to fetch {registry} package '{name}': {exc}"
```

### Response Format

```
Package: express (npm)
─────────────────────────────────────
Version: 4.18.2 (latest)
License: MIT
Downloads: 25.4M/week
Last Updated: 2023-12-15 (2 months ago)

Repository: https://github.com/expressjs/express
Homepage: https://expressjs.com
Dependencies: 30 direct

Security: ✅ No known vulnerabilities
Description: Fast, unopinionated, minimalist web framework for Node.js

Popular Alternatives:
- fastify (22M/wk) - Faster, modern alternative
- koa (2.5M/wk) - From Express team, async/await focused
```

### Error Handling

**Non-existent package:**
```
Package 'nonexistent-pkg' not found on npm.

Did you mean:
- similar-package-name
- another-match
```

**Network error:**
```
Failed to fetch npm package 'express': Network timeout after 10s.
The npm registry may be temporarily unavailable. Try again in a moment.
```

**Rate limit:**
```
Rate limit exceeded for crates.io API.
Please wait 60 seconds before retrying.
```

## Testing Plan

### Unit Tests
- [ ] `test_npm_valid_package()` - Popular package (express)
- [ ] `test_npm_nonexistent()` - Non-existent package
- [ ] `test_pypi_valid_package()` - Popular package (requests)
- [ ] `test_pypi_nonexistent()` - Non-existent package
- [ ] `test_crates_valid()` - Popular crate (serde)
- [ ] `test_go_valid()` - Popular module (github.com/gin-gonic/gin)
- [ ] `test_timeout_handling()` - Network timeout simulation
- [ ] `test_response_size()` - Ensure <8KB output

### Integration Tests
- [ ] Test with real registry APIs
- [ ] Verify response times <3s
- [ ] Test error handling paths
- [ ] Verify MCP tool registration

### Manual Testing
- [ ] Query various npm packages
- [ ] Query various PyPI packages
- [ ] Test with scoped packages (@org/package)
- [ ] Test with very new packages (limited data)
- [ ] Test with deprecated packages

## Dependencies

**No new dependencies needed:**
- Use existing `httpx` for HTTP requests
- Use existing `config.py` for settings

**Optional enhancements:**
- Could cache results for 1 hour (reduce API calls)
- Could add package comparison mode

## Performance Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| Response time | <3s | Fast enough for interactive use |
| Cache TTL | 1 hour | Balance freshness vs API load |
| Response size | <4KB | Leave headroom under 8KB limit |
| Concurrent requests | 5 | Support parallel lookups |

## Security Considerations

- [ ] Sanitize package names (no code injection)
- [ ] Validate registry parameter (whitelist only)
- [ ] Handle HTTPS only (no HTTP fallback)
- [ ] Don't expose API tokens in responses
- [ ] Rate limit client-side to respect APIs

## Future Enhancements

**Phase 3+:**
- Package comparison: `compare_packages(["express", "fastify", "koa"])`
- Dependency tree visualization
- Security vulnerability details (CVE links)
- Historical download trends
- Similar package suggestions
- License compatibility checker

## Implementation Checklist

- [ ] Create `searxng_mcp/registry.py`
- [ ] Add `PackageInfo` dataclass
- [ ] Add `PackageRegistryClient` class
- [ ] Implement `search_npm()`
- [ ] Implement `search_pypi()`
- [ ] Implement `search_crates()`
- [ ] Implement `search_go()`
- [ ] Add `format_package_info()` helper
- [ ] Register tool in `server.py`
- [ ] Add constants to `config.py`
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Update `TASKS.md` (mark in-progress)
- [ ] Update `HISTORY.md` (log decisions)
- [ ] Manual testing
- [ ] Update `TASKS.md` (mark complete)
- [ ] Update `README.md` (add to completed features)

## Open Questions

- [ ] Should we cache results? (Recommendation: Yes, 1 hour TTL)
- [ ] Should we support version-specific lookups? (e.g., `express@4.17.0`)
- [ ] Should we include download charts/trends? (Defer to Phase 3)
- [ ] Should we auto-detect registry from package syntax? (Nice to have)

---

**Next Step:** Assign to developer and begin implementation following this spec.
