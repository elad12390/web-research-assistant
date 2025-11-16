# New Feature Added: search_examples Tool

**Date:** November 15, 2025  
**Status:** ✅ Complete

## Overview

Added a new `search_examples` tool specifically designed for finding code examples, tutorials, and technical articles. This tool is optimized for developers looking to learn new APIs, find usage patterns, or discover how others solve technical problems.

## Feature Details

### Tool: `search_examples`

**Purpose:** Search for code examples, tutorials, and technical articles with content type filtering and optional time range filtering.

**Parameters:**
- `query` (required): What to search for (e.g., "Python async examples", "React hooks tutorial")
- `reasoning` (optional): Why searching (for analytics tracking) - defaults to "Code examples search"
- `content_type` (optional): Type of content - "code", "articles", or "both" (default: "both")
  - `code`: GitHub repos, Stack Overflow, gists, code snippets
  - `articles`: Blog posts, tutorials, documentation, guides
  - `both`: Mixed results
- `time_range` (optional): Recency filter - "day", "week", "month", "year", or "all" (default: "all")
- `max_results` (optional): Number of results (1-10, default: 5)

**Key Features:**
1. **Smart Query Enhancement**: Automatically adds site filters and keywords based on content type
   - Code searches: Adds `site:github.com OR site:stackoverflow.com OR site:gist.github.com`
   - Article searches: Adds `tutorial OR guide OR article OR blog OR how to OR documentation`
   
2. **IT Category Optimization**: Uses SearXNG's "it" category for better technical content

3. **Source Indicators**: Results show source type (GitHub, Stack Overflow, Article) for quick scanning

4. **Time Filtering**: Optional time range for finding recent content

5. **Complete Tracking**: Full usage analytics with reasoning, parameters, and performance metrics

## Implementation Changes

### Files Modified:
1. **`searxng_mcp/search.py`**: 
   - Added `time_range` parameter to `search()` method
   - Enables SearXNG time filtering

2. **`searxng_mcp/server.py`**:
   - Added complete `search_examples` tool (lines ~130-230)
   - Includes tracking, error handling, and formatted output
   - Smart query enhancement logic based on content type

3. **`README.md`**:
   - Updated tool count (5 → 6 tools)
   - Added `search_examples` to tool list
   - Documented parameters and use cases

## Example Usage

```python
# Find code examples on GitHub/Stack Overflow
search_examples(
    query="FastAPI dependency injection",
    content_type="code",
    max_results=5
)

# Find recent tutorials and articles
search_examples(
    query="React Server Components",
    content_type="articles",
    time_range="year",
    max_results=3
)

# Mixed results (default)
search_examples(
    query="Python asyncio examples",
    max_results=5
)
```

## Example Output

```
Code Examples & Articles for: Python asyncio examples
Time Range: All time | Content Type: Both
──────────────────────────────────────────────────

1. [GitHub] python/asyncio - Official asyncio repository
   https://github.com/python/asyncio
   Collection of asyncio examples and patterns...

2. [Stack Overflow] How to use asyncio with aiohttp?
   https://stackoverflow.com/q/12345678
   Comprehensive guide to combining asyncio and aiohttp...

3. [Article] Understanding Python Asyncio
   https://realpython.com/async-io-python/
   Deep dive into Python's asyncio library...
```

## Testing

Verified:
- ✅ Tool accepts all parameters correctly
- ✅ Smart query enhancement works for all content types
- ✅ Time filtering works (when SearXNG returns results)
- ✅ Source indicators display correctly
- ✅ Tracking captures all usage data
- ✅ Error handling for no results
- ✅ Integration with existing server infrastructure

## Tracking Data

The tool tracks:
- Search queries and parameters
- Content type preferences
- Time range usage patterns
- Response times
- Success/failure rates
- Common reasoning patterns

Example tracking entry:
```json
{
  "timestamp": "2025-11-15T23:31:36Z",
  "tool": "search_examples",
  "reasoning": "Code examples search",
  "parameters": {
    "query": "Python asyncio examples",
    "content_type": "code",
    "time_range": "all",
    "max_results": 3
  },
  "response_time_ms": 49.34,
  "success": true,
  "response_size_bytes": 1234
}
```

## Benefits

1. **Optimized for Learning**: Specifically designed to find educational content
2. **Source Filtering**: Quickly find code vs. articles based on needs
3. **Recency Control**: Optional time filtering for latest practices
4. **Developer-Friendly**: Understands common developer search patterns
5. **Analytics-Enabled**: Full tracking to understand usage patterns

## Current Tool Count: 6

1. ✅ `web_search` - General web search
2. ✅ `search_examples` - Code examples & tutorials (NEW!)
3. ✅ `crawl_url` - Page content extraction
4. ✅ `package_info` - Package metadata lookup
5. ✅ `package_search` - Package discovery
6. ✅ `github_repo` - Repository information

All tools have complete tracking implementation with the `reasoning` parameter.

---

**Feature Status:** Production Ready ✅
