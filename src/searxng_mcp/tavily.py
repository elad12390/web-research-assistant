from __future__ import annotations

import logging
from typing import Any

from tavily import AsyncTavilyClient

from .config import MAX_SNIPPET_CHARS, TAVILY_API_KEY, clamp_text
from .search import SearchHit

logger = logging.getLogger(__name__)


class TavilySearcher:
    """Async wrapper around the Tavily search API.

    Returns ``list[SearchHit]`` so it can be used as a drop-in alternative
    to :class:`ExaSearcher` and :class:`SearxSearcher` inside the provider
    dispatch logic.
    """

    # Map SearXNG time_range values to Tavily time_range values
    _TIME_RANGE_MAP: dict[str, str] = {
        "day": "day",
        "week": "week",
        "month": "month",
        "year": "year",
    }

    # Map SearXNG categories to Tavily topics
    _TOPIC_MAP: dict[str, str] = {
        "general": "general",
        "news": "news",
        "science": "general",
        "it": "general",
    }

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or TAVILY_API_KEY
        self._client: AsyncTavilyClient | None = None

    def has_api_key(self) -> bool:
        """Check if an API key is configured."""
        return bool(self.api_key)

    def _get_client(self) -> AsyncTavilyClient:
        if self._client is None:
            self._client = AsyncTavilyClient(api_key=self.api_key)
        return self._client

    async def search(
        self,
        query: str,
        *,
        category: str | None = None,
        max_results: int = 10,
        time_range: str | None = None,
    ) -> list[SearchHit]:
        """Search using the Tavily API.

        Args:
            query: Search query string (max 400 chars recommended).
            category: SearXNG-style category mapped to a Tavily topic.
            max_results: Number of results to return (max 20).
            time_range: Time filter (day, week, month, year).

        Returns:
            List of SearchHit objects.

        Raises:
            ValueError: If no API key is configured.
        """
        if not self.api_key:
            raise ValueError(
                "Tavily API key not configured. Set TAVILY_API_KEY environment variable."
            )

        client = self._get_client()

        kwargs: dict[str, Any] = {
            "query": query,
            "max_results": min(max_results, 20),
            "search_depth": "basic",
        }

        if category:
            kwargs["topic"] = self._TOPIC_MAP.get(category, "general")

        if time_range:
            mapped = self._TIME_RANGE_MAP.get(time_range)
            if mapped:
                kwargs["time_range"] = mapped

        response = await client.search(**kwargs)

        hits: list[SearchHit] = []
        for result in response.get("results", []):
            title = (result.get("title") or "Untitled").strip()
            url = result.get("url", "")
            snippet = result.get("content", "")
            if snippet:
                snippet = clamp_text(snippet, MAX_SNIPPET_CHARS, suffix="...")

            hits.append(SearchHit(title=title, url=url, snippet=snippet))

        return hits


__all__ = ["TavilySearcher"]
