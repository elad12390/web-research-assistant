# Breaking Change: Reasoning Parameter Now Required

**Date:** November 15, 2025  
**Change Type:** Breaking Change  
**Affected:** All 7 tools

---

## What Changed

The reasoning parameter is now REQUIRED for all tools. Previously it had default values.

### Before (Had Defaults):
```python
web_search("Python tutorial")  # Used default: "General web search"
```

### After (Must Provide):
```python
web_search("Python tutorial", reasoning="Learning Python basics")
```

---

## Why This Change?

- 82% of calls used generic defaults
- Analytics showed no meaningful differentiation
- Couldn't identify actual use cases
- Data wasn't actionable

---

## All 7 Tools Now Require Reasoning

1. web_search
2. search_examples
3. search_images
4. crawl_url
5. package_info
6. package_search
7. github_repo

---

## Verification

All tools verified - reasoning is now required with no defaults!

