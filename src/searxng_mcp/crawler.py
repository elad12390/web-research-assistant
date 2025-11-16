from __future__ import annotations

from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig

from .config import CRAWL_MAX_CHARS, clamp_text


class CrawlerClient:
    """Lightweight wrapper around crawl4ai's async crawler."""

    def __init__(self, *, cache_mode: CacheMode = CacheMode.BYPASS) -> None:
        self.cache_mode = cache_mode

    async def fetch(self, url: str, *, max_chars: int | None = None) -> str:
        """Fetch *url* and return cleaned markdown, trimmed to *max_chars*."""

        run_config = CrawlerRunConfig(cache_mode=self.cache_mode)

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

    async def fetch_raw(self, url: str, *, max_chars: int = 50000) -> str:
        """Fetch *url* and return raw HTML content.

        Args:
            url: URL to fetch
            max_chars: Maximum number of characters to return

        Returns:
            Raw HTML content, trimmed to max_chars
        """
        run_config = CrawlerRunConfig(cache_mode=self.cache_mode)

        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url, config=run_config)

        if getattr(result, "error", None):
            raise RuntimeError(str(result.error))  # type: ignore

        html = getattr(result, "html", None) or ""

        html = html.strip()
        if not html:
            raise RuntimeError("Crawl completed but returned no HTML content.")

        return clamp_text(html, max_chars)
