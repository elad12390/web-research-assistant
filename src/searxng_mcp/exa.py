from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from typing import Any

import httpx

from .config import (
    EXA_API_KEY,
    HTTP_TIMEOUT,
    MAX_RETRIES,
    MAX_SNIPPET_CHARS,
    RETRY_BASE_DELAY,
    RETRY_MAX_DELAY,
    clamp_text,
)
from .search import SearchHit


@dataclass(slots=True)
class ExaResult:
    """A search result from the Exa API."""

    title: str
    url: str
    snippet: str
    published_date: str | None = None
    author: str | None = None
    score: float | None = None


class ExaSearcher:
    """Async client for the Exa AI search API.

    Exa provides neural search that finds semantically similar content,
    making it excellent for finding relevant technical content.
    """

    API_BASE = "https://api.exa.ai"

    def __init__(self, api_key: str | None = None, timeout: float = HTTP_TIMEOUT) -> None:
        self.api_key = api_key or EXA_API_KEY
        self.timeout = timeout
        self._quota_limit: int | None = None
        self._quota_remaining: int | None = None
        self._quota_reset: int | None = None
        self._quota_exhausted: bool = False

    def has_api_key(self) -> bool:
        """Check if an API key is configured."""
        return bool(self.api_key)

    def _update_quota_from_headers(self, headers: httpx.Headers) -> None:
        """Extract and store rate-limit info from response headers."""
        if "x-ratelimit-limit" in headers:
            try:
                self._quota_limit = int(headers["x-ratelimit-limit"])
            except (ValueError, TypeError):
                pass
        if "x-ratelimit-remaining" in headers:
            try:
                self._quota_remaining = int(headers["x-ratelimit-remaining"])
            except (ValueError, TypeError):
                pass
        if "x-ratelimit-reset" in headers:
            try:
                self._quota_reset = int(headers["x-ratelimit-reset"])
            except (ValueError, TypeError):
                pass

    async def search(
        self,
        query: str,
        *,
        num_results: int = 10,
        search_type: str = "auto",
        category: str | None = None,
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
        start_published_date: str | None = None,
        end_published_date: str | None = None,
        include_text: bool = True,
    ) -> list[SearchHit]:
        """Search using the Exa API.

        Args:
            query: Search query string
            num_results: Number of results to return (max 100)
            search_type: Search type - "auto", "neural", "fast", or "deep"
            category: Optional category filter (company, research paper, news, pdf, github, tweet, etc.)
            include_domains: Limit results to these domains
            exclude_domains: Exclude results from these domains
            start_published_date: Only include content published after this date (ISO 8601)
            end_published_date: Only include content published before this date (ISO 8601)
            include_text: Whether to include text content in results

        Returns:
            List of SearchHit objects

        Raises:
            ValueError: If no API key is configured
            httpx.RequestError: If the request fails after all retries
        """
        if not self.api_key:
            raise ValueError("Exa API key not configured. Set EXA_API_KEY environment variable.")

        # Build request payload
        payload: dict[str, Any] = {
            "query": query,
            "numResults": min(num_results, 100),
            "type": search_type,
        }

        # Add optional content retrieval
        if include_text:
            payload["text"] = True

        # Add optional filters
        if category:
            payload["category"] = category
        if include_domains:
            payload["includeDomains"] = include_domains
        if exclude_domains:
            payload["excludeDomains"] = exclude_domains
        if start_published_date:
            payload["startPublishedDate"] = start_published_date
        if end_published_date:
            payload["endPublishedDate"] = end_published_date

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.API_BASE}/search",
                        headers=headers,
                        json=payload,
                    )
                    response.raise_for_status()
                    self._update_quota_from_headers(response.headers)
                    data = response.json()

                hits: list[SearchHit] = []
                for result in data.get("results", []):
                    title = result.get("title", "Untitled").strip()
                    url = result.get("url", "")

                    # Get snippet from text or highlights
                    snippet = ""
                    if result.get("text"):
                        snippet = result["text"][:MAX_SNIPPET_CHARS]
                    elif result.get("highlights"):
                        snippet = " ".join(result["highlights"])[:MAX_SNIPPET_CHARS]

                    snippet = (
                        clamp_text(snippet, MAX_SNIPPET_CHARS, suffix="...") if snippet else ""
                    )

                    hits.append(SearchHit(title=title, url=url, snippet=snippet))

                return hits

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    self._quota_exhausted = True
                    self._update_quota_from_headers(e.response.headers)
                    raise
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    delay = min(
                        RETRY_BASE_DELAY * (2**attempt) + random.uniform(0, 0.5),
                        RETRY_MAX_DELAY,
                    )
                    await asyncio.sleep(delay)
                continue
            except (httpx.RequestError, httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    delay = min(
                        RETRY_BASE_DELAY * (2**attempt) + random.uniform(0, 0.5),
                        RETRY_MAX_DELAY,
                    )
                    await asyncio.sleep(delay)
                continue

        raise last_error or httpx.RequestError("All connection attempts failed")

    async def search_with_contents(
        self,
        query: str,
        *,
        num_results: int = 5,
        search_type: str = "auto",
        include_summary: bool = False,
        include_highlights: bool = True,
        max_chars: int = 5000,
    ) -> list[ExaResult]:
        """Search and retrieve full content from results.

        This is useful when you need more than just snippets.

        Args:
            query: Search query string
            num_results: Number of results to return
            search_type: Search type - "auto", "neural", "fast", or "deep"
            include_summary: Include AI-generated summary
            include_highlights: Include relevant text highlights
            max_chars: Maximum characters of text content to retrieve

        Returns:
            List of ExaResult objects with full content
        """
        if not self.api_key:
            raise ValueError("Exa API key not configured. Set EXA_API_KEY environment variable.")

        payload: dict[str, Any] = {
            "query": query,
            "numResults": min(num_results, 100),
            "type": search_type,
            "text": {"maxCharacters": max_chars},
        }

        if include_summary:
            payload["summary"] = True
        if include_highlights:
            payload["highlights"] = True

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.API_BASE}/search",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                self._update_quota_from_headers(response.headers)
                data = response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                self._quota_exhausted = True
                self._update_quota_from_headers(e.response.headers)
            raise

        results: list[ExaResult] = []
        for item in data.get("results", []):
            # Build snippet from text, summary, or highlights
            snippet = ""
            if item.get("summary"):
                snippet = item["summary"]
            elif item.get("text"):
                snippet = item["text"]
            elif item.get("highlights"):
                snippet = " ".join(item["highlights"])

            results.append(
                ExaResult(
                    title=item.get("title", "Untitled"),
                    url=item.get("url", ""),
                    snippet=snippet,
                    published_date=item.get("publishedDate"),
                    author=item.get("author"),
                    score=item.get("score"),
                )
            )

        return results

    def is_quota_healthy(self) -> bool:
        """Returns False if quota is exhausted or remaining < 10%."""
        if self._quota_exhausted:
            return False
        if self._quota_limit and self._quota_remaining is not None:
            return self._quota_remaining >= (self._quota_limit * 0.1)
        return True

    def get_quota_status(self) -> dict[str, Any]:
        """Returns dict with limit, remaining, reset, exhausted, healthy."""
        return {
            "limit": self._quota_limit,
            "remaining": self._quota_remaining,
            "reset": self._quota_reset,
            "exhausted": self._quota_exhausted,
            "healthy": self.is_quota_healthy(),
        }

    @property
    def quota_exhausted(self) -> bool:
        """Returns True if quota is exhausted or remaining < 10% of limit."""
        return not self.is_quota_healthy()


__all__ = ["ExaSearcher", "ExaResult"]
