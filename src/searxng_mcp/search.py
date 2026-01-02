from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass

import httpx

from .config import (
    DEFAULT_CATEGORY,
    DEFAULT_MAX_RESULTS,
    HTTP_TIMEOUT,
    MAX_RETRIES,
    MAX_SEARCH_RESULTS,
    MAX_SNIPPET_CHARS,
    RETRY_BASE_DELAY,
    RETRY_MAX_DELAY,
    SEARX_BASE_URL,
    USER_AGENT,
    clamp_text,
)


@dataclass(slots=True)
class SearchHit:
    title: str
    url: str
    snippet: str


class SearxSearcher:
    """Minimal async client for the local SearXNG instance."""

    def __init__(self, base_url: str = SEARX_BASE_URL, timeout: float = HTTP_TIMEOUT) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self._headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}

    async def search(
        self,
        query: str,
        *,
        category: str = DEFAULT_CATEGORY,
        max_results: int = DEFAULT_MAX_RESULTS,
        time_range: str | None = None,
    ) -> list[SearchHit]:
        """Return up to *max_results* hits for *query* within *category*.

        Args:
            query: Search query string
            category: SearXNG category (general, it, etc.)
            max_results: Maximum number of results to return
            time_range: Optional time filter (day, week, month, year)

        Includes automatic retry with exponential backoff for connection errors.
        """

        limit = max(1, min(max_results, MAX_SEARCH_RESULTS))
        params = {
            "q": query,
            "categories": category,
            "format": "json",
            "pageno": 1,
        }

        # Add time range filter if specified
        if time_range:
            params["time_range"] = time_range

        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=self.timeout, headers=self._headers) as client:
                    response = await client.get(self.base_url, params=params)
                    response.raise_for_status()
                    payload = response.json()

                hits: list[SearchHit] = []
                for item in payload.get("results", [])[:limit]:
                    title = (
                        item.get("title") or item.get("pretty_url") or item.get("url") or "Untitled"
                    ).strip()
                    url = item.get("url") or ""
                    snippet = (item.get("content") or item.get("snippet") or "").strip()
                    snippet = clamp_text(snippet, MAX_SNIPPET_CHARS, suffix="…") if snippet else ""
                    hits.append(SearchHit(title=title, url=url, snippet=snippet))

                return hits

            except (httpx.RequestError, httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    # Exponential backoff with jitter
                    delay = min(
                        RETRY_BASE_DELAY * (2**attempt) + random.uniform(0, 0.5),
                        RETRY_MAX_DELAY,
                    )
                    await asyncio.sleep(delay)
                continue

        # All retries exhausted
        raise last_error or httpx.RequestError("All connection attempts failed")
