# Quick Start: search_examples Tool

## Common Use Cases

### 1. Find Code Examples
```python
# GitHub repos, Stack Overflow, code snippets
search_examples(
    query="Python async await patterns",
    content_type="code"
)

search_examples(
    query="FastAPI WebSocket example",
    content_type="code",
    max_results=3
)
```

### 2. Find Tutorials & Articles
```python
# Blog posts, guides, documentation
search_examples(
    query="React Server Components tutorial",
    content_type="articles"
)

search_examples(
    query="Rust ownership explained",
    content_type="articles",
    time_range="year"  # Only recent content
)
```

### 3. Mixed Search (Default)
```python
# Both code and articles
search_examples(
    query="GraphQL best practices"
)

search_examples(
    query="Docker multi-stage builds",
    content_type="both",
    max_results=10
)
```

### 4. Time-Filtered Searches
```python
# Find the most recent content
search_examples(
    query="Next.js 14 app router",
    time_range="month"  # Last month only
)

search_examples(
    query="TypeScript 5 features",
    time_range="year",  # Last year
    content_type="articles"
)

# All-time search (default, best for most queries)
search_examples(
    query="Python design patterns",
    time_range="all"
)
```

## Tips for Best Results

### ✅ DO:
- Use specific technology names: "FastAPI", "React", "Rust"
- Include what you're looking for: "examples", "tutorial", "patterns"
- Be specific about the feature: "dependency injection", "hooks", "async"
- Use `content_type="code"` when you want to see implementations
- Use `content_type="articles"` when you want explanations
- Default to `time_range="all"` for best coverage

### ❌ DON'T:
- Use very generic terms: "programming", "coding"
- Include year in query when using time_range filter
- Over-specify with both framework version AND time filter
- Use time filters unless you specifically need recent content

## Example Queries

| Query | Content Type | When to Use |
|-------|--------------|-------------|
| `"FastAPI authentication examples"` | `"code"` | Need to see working code |
| `"Understanding React useEffect"` | `"articles"` | Need conceptual explanation |
| `"Python asyncio"` | `"both"` | Want both code and docs |
| `"Rust error handling"` | `"code"` | Want to see patterns |
| `"GraphQL tutorial"` | `"articles"` | Learning from scratch |
| `"Docker Compose examples"` | `"code"` | Need configuration examples |
| `"TypeScript generics"` | `"both"` | Want comprehensive resources |

## Output Format

Results include source indicators for quick scanning:

```
Code Examples & Articles for: FastAPI dependency injection
Time Range: All time | Content Type: Code
──────────────────────────────────────────────────

1. [GitHub] tiangolo/fastapi - Official FastAPI repository
   https://github.com/tiangolo/fastapi
   Modern web framework with dependency injection...

2. [Stack Overflow] How to use dependency injection in FastAPI?
   https://stackoverflow.com/q/12345678
   Complete example of FastAPI DI system...

3. [Article] FastAPI Dependency Injection Guide
   https://realpython.com/fastapi-python-dependency-injection/
   Comprehensive tutorial on using DI in FastAPI...
```

## Combining with Other Tools

### Complete Research Workflow

```python
# 1. Find examples and tutorials
examples = search_examples(
    query="Pydantic V2 validation examples",
    content_type="both"
)

# 2. Crawl the most promising article
content = crawl_url(
    url="https://docs.pydantic.dev/latest/concepts/validators/",
    max_chars=12000
)

# 3. Check the package details
info = package_info(
    name="pydantic",
    registry="pypi"
)

# 4. Look at the GitHub repo
repo = github_repo(
    repo="pydantic/pydantic",
    include_commits=True
)
```

## Pro Tips

1. **Start broad, then narrow**: Begin with `time_range="all"`, only filter by time if too many results

2. **Content type matters**: 
   - Learning? Use `"articles"`
   - Implementing? Use `"code"`
   - Exploring? Use `"both"`

3. **Source indicators help**: Look for:
   - `[GitHub]` - Official repos and real implementations
   - `[Stack Overflow]` - Q&A with working code
   - `[Article]` - In-depth tutorials and guides

4. **Combine terms effectively**:
   - ✅ "FastAPI dependency injection"
   - ✅ "React hooks patterns"
   - ✅ "Rust lifetime examples"
   - ❌ "how to code in python" (too generic)

5. **Use time filters strategically**:
   - New features: `time_range="month"` or `"year"`
   - Established tech: `time_range="all"`
   - Rapidly changing frameworks: `time_range="year"`

---

**Tool Location:** `searxng_mcp.server.search_examples`  
**Added:** November 15, 2025  
**Status:** Production Ready ✅
