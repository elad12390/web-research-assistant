from __future__ import annotations

import os
from typing import Final


def _env_str(key: str, default: str) -> str:
    return os.environ.get(key, default)


def _env_int(key: str, default: int) -> int:
    value = os.environ.get(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_float(key: str, default: float) -> float:
    value = os.environ.get(key)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


SEARX_BASE_URL: Final[str] = _env_str("SEARXNG_BASE_URL", "http://localhost:2288/search")
DEFAULT_CATEGORY: Final[str] = _env_str("SEARXNG_DEFAULT_CATEGORY", "general")
USER_AGENT: Final[str] = _env_str("SEARXNG_MCP_USER_AGENT", "searxng-mcp/0.1")
HTTP_TIMEOUT: Final[float] = _env_float("SEARXNG_HTTP_TIMEOUT", 15.0)
MAX_SEARCH_RESULTS: Final[int] = _env_int("SEARXNG_MAX_RESULTS", 10)
DEFAULT_MAX_RESULTS: Final[int] = _env_int("SEARXNG_DEFAULT_RESULTS", 5)
MAX_SNIPPET_CHARS: Final[int] = _env_int("SEARXNG_MAX_SNIPPET_CHARS", 400)
MAX_RESPONSE_CHARS: Final[int] = _env_int("MCP_MAX_RESPONSE_CHARS", 8000)
CRAWL_MAX_CHARS: Final[int] = _env_int("SEARXNG_CRAWL_MAX_CHARS", 8000)
PIXABAY_API_KEY: Final[str] = _env_str("PIXABAY_API_KEY", "")

TRUNCATION_SUFFIX: Final[str] = (
    "\n\n… [output truncated to stay within MCP response limits. Ask for a specific section if"
    " you need more.]"
)


def clamp_text(text: str, limit: int = MAX_RESPONSE_CHARS, *, suffix: str | None = None) -> str:
    """Trim *text* to *limit* characters and append the provided suffix when truncated."""

    if limit <= 0 or len(text) <= limit:
        return text

    trimmed = text[:limit].rstrip()
    note = suffix if suffix is not None else TRUNCATION_SUFFIX
    return f"{trimmed}{note}"


__all__ = [
    "SEARX_BASE_URL",
    "DEFAULT_CATEGORY",
    "USER_AGENT",
    "HTTP_TIMEOUT",
    "MAX_SEARCH_RESULTS",
    "DEFAULT_MAX_RESULTS",
    "MAX_SNIPPET_CHARS",
    "MAX_RESPONSE_CHARS",
    "CRAWL_MAX_CHARS",
    "PIXABAY_API_KEY",
    "clamp_text",
]
