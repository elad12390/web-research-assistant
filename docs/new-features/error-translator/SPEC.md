# Error Translator - Feature Specification

**Status:** Not Started  
**Priority:** P1 (High Impact)  
**Assigned:** Unassigned  
**Created:** 2025-01-15

---

## Overview

MCP tool that accepts error messages/stack traces and returns ranked solutions from Stack Overflow, GitHub issues, and documentation. Saves developers from manual Stack Overflow searching and result filtering.

## User Story

**As a** developer encountering an error  
**I want** instant ranked solutions  
**So that** I can fix issues without manually searching and filtering multiple sources

## Success Criteria

- [ ] Extracts error signatures from stack traces
- [ ] Finds relevant Stack Overflow answers
- [ ] Finds relevant GitHub issues
- [ ] Ranks solutions by quality/relevance
- [ ] Works for Python, JavaScript, TypeScript, Rust, Go errors
- [ ] Response time <10s
- [ ] Returns top 3-5 solutions
- [ ] Fits within MCP response limits

## Technical Design

### Error Signature Extraction

**Goal:** Convert verbose stack trace to searchable signature

**Example Input (Python):**
```
Traceback (most recent call last):
  File "/home/user/project/app.py", line 42, in process_data
    result = data.transform()
AttributeError: 'NoneType' object has no attribute 'transform'
```

**Extracted Signature:**
```
Language: Python
Error Type: AttributeError
Core Message: 'NoneType' object has no attribute 'transform'
Context: method call on None
```

**Signature Rules:**
1. Strip file paths (too specific)
2. Keep error type and core message
3. Detect language from stack trace format
4. Identify common patterns (None access, undefined, etc.)

### Solution Ranking

**Stack Overflow:**
- Accepted answer: +100 points
- Votes: +votes score
- Recency: +points if <2 years old
- Code blocks: +points if includes code

**GitHub Issues:**
- Closed status: +50 points
- Reactions: +reaction count
- Official repo: +bonus points
- Recency: +points if recent

### Implementation

**Module:** `searxng_mcp/error_solver.py`

```python
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class Language(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    RUST = "rust"
    GO = "go"
    UNKNOWN = "unknown"

@dataclass
class ErrorSignature:
    language: Language
    error_type: str
    message: str
    context: Optional[str]

@dataclass
class Solution:
    source: str  # "stackoverflow", "github"
    title: str
    score: int
    url: str
    solution_text: str
    code_snippet: Optional[str]
    votes: int
    accepted: bool

class ErrorSolver:
    async def analyze_error(
        self, 
        error_text: str, 
        language: str = "auto"
    ) -> ErrorSignature:
        """Extract error signature from stack trace."""
    
    async def search_stackoverflow(
        self, 
        signature: ErrorSignature
    ) -> List[Solution]:
        """Search Stack Overflow for solutions."""
    
    async def search_github_issues(
        self,
        signature: ErrorSignature
    ) -> List[Solution]:
        """Search GitHub issues for solutions."""
    
    async def rank_solutions(
        self,
        solutions: List[Solution]
    ) -> List[Solution]:
        """Rank and filter solutions by quality."""
```

**Tool Definition:**

```python
@mcp.tool()
async def solve_error(
    error: Annotated[str, "Error message or full stack trace"],
    language: Annotated[str, "Programming language (auto-detect if not specified)"] = "auto",
    max_solutions: Annotated[int, "Maximum solutions to return"] = 3
) -> str:
    """
    Find solutions for error messages and stack traces.
    
    Searches Stack Overflow and GitHub issues, ranks by quality, and returns
    actionable solutions with code examples. Use this when you hit an error
    and need quick fixes.
    
    Examples:
    - solve_error("TypeError: Cannot read property 'map' of undefined")
    - solve_error(full_stack_trace, language="python")
    """
```

### Response Format

```
Error Analysis
──────────────
Type: AttributeError (Python)
Issue: Attempting to call method on None value
Likely Cause: Variable not initialized or function returned None

Solution #1 ⭐ ACCEPTED (Stack Overflow)
────────────────────────────────────────
Score: 234 votes | Posted: 6 months ago
Source: https://stackoverflow.com/questions/12345/...

Problem: Calling methods on None raises AttributeError
Fix: Check for None before calling methods

Code:
```python
if data is not None:
    result = data.transform()
else:
    result = None  # or handle appropriately
```

Alternative: Use Optional chaining (Python 3.10+)
```python
result = data.transform() if data else None
```

Solution #2 (GitHub Issue - Closed)
───────────────────────────────────
Repository: pandas-dev/pandas #45678
Fix: Ensure DataFrame is not empty before operations

[Solution details...]

Solution #3 (Stack Overflow)
───────────────────────────
[Solution details...]

Common Fixes Summary:
• Always check for None before method calls
• Use try/except for defensive programming  
• Validate function return values
• Consider using Optional type hints
```

### Error Handling

**Malformed error text:**
```
Could not extract error signature from provided text.

Please provide:
- Full stack trace, OR
- Error message including error type

Example: "TypeError: Cannot read property 'x' of undefined"
```

**No solutions found:**
```
No solutions found for: AttributeError: 'NoneType' object has no attribute 'transform'

Suggestions:
1. Check variable initialization
2. Verify function return values
3. Add None checks before method calls
4. Search manually: https://stackoverflow.com/search?q=...
```

## Testing Plan

### Unit Tests
- [ ] `test_extract_python_error()` - Parse Python stack trace
- [ ] `test_extract_javascript_error()` - Parse JS error
- [ ] `test_extract_typescript_error()` - Parse TS error
- [ ] `test_language_detection()` - Auto-detect language
- [ ] `test_stackoverflow_search()` - API integration
- [ ] `test_github_search()` - API integration
- [ ] `test_solution_ranking()` - Ranking algorithm
- [ ] `test_malformed_input()` - Error handling

### Integration Tests
- [ ] Test with real Stack Overflow API
- [ ] Test with real GitHub API
- [ ] Verify response times <10s
- [ ] Test rate limiting

### Manual Testing
- [ ] Common Python errors (TypeError, AttributeError, etc.)
- [ ] Common JavaScript errors (undefined, null reference)
- [ ] Rust errors (borrow checker, lifetime errors)
- [ ] Go errors (nil pointer, interface errors)

## Dependencies

**Required:**
- `httpx` - Already available
- Stack Overflow API access (no key needed for search, has rate limits)
- GitHub API access (optional key for higher limits)

**Optional:**
- `beautifulsoup4` - Already in crawl4ai deps (for scraping if API insufficient)

## Performance Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| Response time | <10s | Acceptable for error solving |
| Solutions returned | 3-5 | Enough variety, not overwhelming |
| Response size | <6KB | Leave room under 8KB limit |
| Cache TTL | 24 hours | Errors/solutions don't change often |

## API Considerations

### Stack Overflow API
- **Endpoint:** `https://api.stackexchange.com/2.3/search`
- **Rate Limit:** 300 requests/day without key
- **With Key:** 10,000 requests/day
- **Recommendation:** Start without key, add key if needed

### GitHub Search API
- **Endpoint:** `https://api.github.com/search/issues`
- **Rate Limit:** 10 requests/min (unauthenticated), 30/min (authenticated)
- **Recommendation:** Use authenticated requests with personal token

## Security Considerations

- [ ] Sanitize error text (remove sensitive data like API keys in URLs)
- [ ] Don't log full stack traces (may contain sensitive paths)
- [ ] Validate language parameter (whitelist only)
- [ ] Respect API rate limits
- [ ] Cache aggressively to reduce API calls

## Future Enhancements

**Phase 3+:**
- Multi-language error translation (e.g., explain Rust error in plain English)
- Custom solution database (learn from user feedback)
- Integration with project context (suggest fixes specific to your codebase)
- Automatic fix application (generate PR with suggested fix)
- Error pattern learning (detect recurring errors in your project)

## Implementation Checklist

- [ ] Create `searxng_mcp/error_solver.py`
- [ ] Implement `ErrorSignature` dataclass
- [ ] Implement `Solution` dataclass
- [ ] Implement `ErrorSolver` class
- [ ] Add error signature extraction (Python, JS, TS, Rust, Go)
- [ ] Implement Stack Overflow search
- [ ] Implement GitHub issues search
- [ ] Implement solution ranking algorithm
- [ ] Add response formatter
- [ ] Register tool in `server.py`
- [ ] Add constants to `config.py`
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Manual testing with various errors
- [ ] Update `TASKS.md`
- [ ] Update `HISTORY.md`
- [ ] Update `README.md`

## Open Questions

- [ ] Should we support Stack Overflow API key? (Recommendation: Yes, optional env var)
- [ ] Should we scrape if API is insufficient? (Recommendation: API first, scrape as fallback)
- [ ] Should we cache solutions? (Recommendation: Yes, 24 hour TTL)
- [ ] Should we support error fingerprinting for tracking? (Defer to Phase 3)
- [ ] Should we include documentation links? (Nice to have if easy)

## Example Usage

```python
# User pastes error
await solve_error("""
Traceback (most recent call last):
  File "app.py", line 42, in process_data
    result = data.transform()
AttributeError: 'NoneType' object has no attribute 'transform'
""")

# Tool returns ranked solutions with fixes
```

---

**Next Step:** Review spec, address open questions, assign to developer for implementation.
