from __future__ import annotations

import logging

from tavily import AsyncTavilyClient

from .config import MAX_SNIPPET_CHARS, TAVILY_API_KEY, clamp_text
from .search import SearchHit

logger = logging.getLogger(__name__)


class TavilySearcher:
    """Async client for the Tavily search API.

    Tavily provides AI-optimised web search, acting as a middle-tier
    fallback between Exa and SearXNG in the 'auto' provider chain.
    """

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
        max_results: int = 5,
        search_depth: str = "basic",
        topic: str = "general",
        time_range: str | None = None,
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
    ) -> list[SearchHit]:
        """Search using the Tavily API.

        Args:
            query: Search query string (max 400 chars recommended).
            max_results: Number of results to return.
            search_depth: "basic" or "advanced".
            topic: "general", "news", or "finance".
            time_range: Time filter - "day", "week", "month", "year".
            include_domains: Limit results to these domains.
            exclude_domains: Exclude results from these domains.

        Returns:
            List of SearchHit objects.

        Raises:
            ValueError: If no API key is configured.
        """
        if not self.api_key:
            raise ValueError("Tavily API key not configured. Set TAVILY_API_KEY environment variable.")

        client = self._get_client()

        kwargs: dict = {
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
            "topic": topic,
        }
        if time_range:
            kwargs["time_range"] = time_range
        if include_domains:
            kwargs["include_domains"] = include_domains
        if exclude_domains:
            kwargs["exclude_domains"] = exclude_domains

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
