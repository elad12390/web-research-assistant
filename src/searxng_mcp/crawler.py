from __future__ import annotations

import asyncio
import random

from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig

from .config import (
    CRAWL_MAX_CHARS,
    MAX_RETRIES,
    RETRY_BASE_DELAY,
    RETRY_MAX_DELAY,
    clamp_text,
)


class CrawlerClient:
    """Lightweight wrapper around crawl4ai's async crawler with retry support."""

    def __init__(self, *, cache_mode: CacheMode = CacheMode.BYPASS) -> None:
        self.cache_mode = cache_mode

    async def fetch(self, url: str, *, max_chars: int | None = None) -> str:
        """Fetch *url* and return cleaned markdown, trimmed to *max_chars*.

        Includes automatic retry with exponential backoff for connection errors.
        """

        run_config = CrawlerRunConfig(cache_mode=self.cache_mode)
        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                async with AsyncWebCrawler() as crawler:
                    result = await crawler.arun(url=url, config=run_config)

                if getattr(result, "error", None):
                    raise RuntimeError(str(result.error))  # type: ignore

                text = (
                    getattr(result, "markdown", None)
                    or getattr(result, "content", None)
                    or getattr(result, "html", None)
                    or ""
                )

                text = text.strip()
                if not text:
                    raise RuntimeError("Crawl completed but returned no readable content.")

                limit = max_chars or CRAWL_MAX_CHARS
                return clamp_text(text, limit)

            except (OSError, ConnectionError, TimeoutError) as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    delay = min(
                        RETRY_BASE_DELAY * (2**attempt) + random.uniform(0, 0.5),
                        RETRY_MAX_DELAY,
                    )
                    await asyncio.sleep(delay)
                continue

        # All retries exhausted
        raise last_error or RuntimeError("All connection attempts failed")

    async def fetch_raw(self, url: str, *, max_chars: int = 50000) -> str:
        """Fetch *url* and return raw HTML content.

        Args:
            url: URL to fetch
            max_chars: Maximum number of characters to return

        Returns:
            Raw HTML content, trimmed to max_chars

        Includes automatic retry with exponential backoff for connection errors.
        """
        run_config = CrawlerRunConfig(cache_mode=self.cache_mode)
        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                async with AsyncWebCrawler() as crawler:
                    result = await crawler.arun(url=url, config=run_config)

                if getattr(result, "error", None):
                    raise RuntimeError(str(result.error))  # type: ignore

                html = getattr(result, "html", None) or ""

                html = html.strip()
                if not html:
                    raise RuntimeError("Crawl completed but returned no HTML content.")

                return clamp_text(html, max_chars)

            except (OSError, ConnectionError, TimeoutError) as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    delay = min(
                        RETRY_BASE_DELAY * (2**attempt) + random.uniform(0, 0.5),
                        RETRY_MAX_DELAY,
                    )
                    await asyncio.sleep(delay)
                continue

        # All retries exhausted
        raise last_error or RuntimeError("All connection attempts failed")
