from __future__ import annotations

import asyncio
import random

import html2text
from scrapling.fetchers import AsyncFetcher

from .config import (
    CRAWL_MAX_CHARS,
    MAX_RETRIES,
    RETRY_BASE_DELAY,
    RETRY_MAX_DELAY,
    clamp_text,
)

_html_converter = html2text.HTML2Text()
_html_converter.ignore_links = False
_html_converter.body_width = 0
_html_converter.ignore_images = True
_html_converter.ignore_emphasis = False
_html_converter.skip_internal_links = True


class CrawlerClient:
    """Lightweight wrapper around scrapling's AsyncFetcher with retry support."""

    async def fetch(self, url: str, *, max_chars: int | None = None) -> str:
        """Fetch *url* and return cleaned markdown, trimmed to *max_chars*.

        Uses scrapling AsyncFetcher with html2text for markdown conversion.
        Includes automatic retry with exponential backoff for connection errors.
        """
        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                response = await AsyncFetcher.get(
                    url,
                    stealthy_headers=True,
                    timeout=30,
                    verify=False,
                    retries=1,
                    follow_redirects=True,
                )

                if response.status >= 400:
                    raise RuntimeError(f"HTTP {response.status} for {url}")

                html = response.html_content or ""
                if not html.strip():
                    raise RuntimeError("Crawl completed but returned no readable content.")

                text = _html_converter.handle(html).strip()
                if not text:
                    text = response.get_all_text(separator="\n", strip=True) or ""
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
        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                response = await AsyncFetcher.get(
                    url,
                    stealthy_headers=True,
                    timeout=30,
                    verify=False,
                    retries=1,
                    follow_redirects=True,
                )

                if response.status >= 400:
                    raise RuntimeError(f"HTTP {response.status} for {url}")

                html = response.html_content or ""
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

        raise last_error or RuntimeError("All connection attempts failed")
