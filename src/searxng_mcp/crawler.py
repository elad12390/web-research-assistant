from __future__ import annotations

import asyncio
import random
import time
import urllib.parse
from dataclasses import dataclass
from enum import Enum

from typing import Any

import html2text
from scrapling.fetchers import AsyncFetcher

from .config import (
    CRAWL_MAX_CHARS,
    DOMAIN_MAX_CONCURRENT,
    DOMAIN_MIN_DELAY,
    MAX_RETRIES,
    PROXY_URL,
    RETRY_BASE_DELAY,
    RETRY_MAX_DELAY,
    STEALTH_TIMEOUT,
    clamp_text,
)

_BLOCK_SIGNATURES = (
    "Attention Required",
    "cf-browser-verification",
    "Just a moment",
    "Checking your browser",
    "datadome",
    "cf-challenge",
    "challenge-platform",
)

_GENERIC_TLDS = frozenset(
    {
        "com",
        "org",
        "net",
        "edu",
        "gov",
        "mil",
        "int",
        "io",
        "ai",
        "tv",
        "me",
        "co",
        "app",
        "dev",
        "xyz",
        "info",
        "biz",
        "pro",
        "name",
        "museum",
        "aero",
    }
)

_CCTLD_TO_COUNTRY: dict[str, str] = {
    "uk": "GB",
}


def _detect_country_code(domain: str) -> str:
    """Derive ISO 3166-1 alpha-2 country code from domain's ccTLD. Returns '' if generic."""
    tld = domain.rstrip(".").rsplit(".", maxsplit=1)[-1].lower()
    if tld in _GENERIC_TLDS or len(tld) != 2:
        return ""
    return _CCTLD_TO_COUNTRY.get(tld, tld.upper())


def _geo_targeted_proxy(proxy_url: str, country_code: str) -> str:
    """Inject _country-XX into Evomi-style proxy password. Skips if already targeted."""
    if not country_code or not proxy_url:
        return proxy_url
    parsed = urllib.parse.urlparse(proxy_url)
    if not parsed.password:
        return proxy_url
    if "_country-" in parsed.password:
        return proxy_url
    new_password = f"{parsed.password}_country-{country_code}"
    netloc = f"{parsed.username}:{new_password}@{parsed.hostname}"
    if parsed.port:
        netloc += f":{parsed.port}"
    return urllib.parse.urlunparse(parsed._replace(netloc=netloc))


class FetchStatus(Enum):
    OK = "ok"
    BLOCKED = "blocked"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"
    EMPTY = "empty"


class FetchMethod(Enum):
    NORMAL = "normal"
    NORMAL_PROXY = "normal+proxy"
    STEALTH = "stealth"
    STEALTH_PROXY = "stealth+proxy"


@dataclass
class FetchResult:
    """Result of a resilient fetch operation."""

    content: str
    status: FetchStatus
    method: FetchMethod
    domain: str
    http_status: int | None = None
    error_message: str | None = None
    response_time_ms: float = 0.0


def _extract_domain(url: str) -> str:
    return urllib.parse.urlparse(url).netloc


def _is_blocked_html(html: str) -> bool:
    snippet = html[:5000].lower()
    return any(sig.lower() in snippet for sig in _BLOCK_SIGNATURES)


_html_converter = html2text.HTML2Text()
_html_converter.ignore_links = False
_html_converter.body_width = 0
_html_converter.ignore_images = True
_html_converter.ignore_emphasis = False
_html_converter.skip_internal_links = True


class DomainThrottle:
    def __init__(
        self,
        max_concurrent: int = DOMAIN_MAX_CONCURRENT,
        min_delay: float = DOMAIN_MIN_DELAY,
    ) -> None:
        self._max_concurrent = max_concurrent
        self._min_delay = min_delay
        self._semaphores: dict[str, asyncio.Semaphore] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._last_request: dict[str, float] = {}

    def _get_semaphore(self, domain: str) -> asyncio.Semaphore:
        if domain not in self._semaphores:
            self._semaphores[domain] = asyncio.Semaphore(self._max_concurrent)
        return self._semaphores[domain]

    def _get_lock(self, domain: str) -> asyncio.Lock:
        if domain not in self._locks:
            self._locks[domain] = asyncio.Lock()
        return self._locks[domain]

    async def acquire(self, domain: str) -> None:
        sem = self._get_semaphore(domain)
        await sem.acquire()
        lock = self._get_lock(domain)
        async with lock:
            last = self._last_request.get(domain, 0.0)
            elapsed = time.monotonic() - last
            needed = self._min_delay + random.uniform(0, 0.3)
            if elapsed < needed:
                await asyncio.sleep(needed - elapsed)
            self._last_request[domain] = time.monotonic()

    def release(self, domain: str) -> None:
        sem = self._semaphores.get(domain)
        if sem is not None:
            sem.release()


class CrawlerClient:
    def __init__(self) -> None:
        self._throttle = DomainThrottle()

    async def resilient_fetch(
        self,
        url: str,
        *,
        max_chars: int | None = None,
        raw: bool = False,
        country: str = "",
    ) -> FetchResult:
        """Fetch with automatic escalation: normal → normal+proxy → stealth → stealth+proxy."""
        domain = _extract_domain(url)
        limit = max_chars or CRAWL_MAX_CHARS
        start = time.monotonic()

        normal_result = await self._try_normal(url, domain=domain, limit=limit, raw=raw)
        if normal_result.status == FetchStatus.OK:
            return normal_result

        if normal_result.status not in (FetchStatus.BLOCKED, FetchStatus.RATE_LIMITED):
            return normal_result

        geo_code = country.upper() if country else _detect_country_code(domain)
        geo_proxy = _geo_targeted_proxy(PROXY_URL, geo_code)

        if geo_proxy:
            proxy_result = await self._try_normal(
                url, domain=domain, limit=limit, raw=raw, proxy=geo_proxy
            )
            proxy_result.method = FetchMethod.NORMAL_PROXY
            proxy_result.response_time_ms = (time.monotonic() - start) * 1000
            if proxy_result.status == FetchStatus.OK:
                return proxy_result

        stealth_result = await self._try_stealth(url, domain=domain, limit=limit, raw=raw)
        stealth_result.response_time_ms = (time.monotonic() - start) * 1000
        if stealth_result.status == FetchStatus.OK:
            return stealth_result

        if geo_proxy and stealth_result.status in (FetchStatus.BLOCKED, FetchStatus.RATE_LIMITED):
            stealth_proxy_result = await self._try_stealth(
                url, domain=domain, limit=limit, raw=raw, proxy=geo_proxy
            )
            stealth_proxy_result.method = FetchMethod.STEALTH_PROXY
            stealth_proxy_result.response_time_ms = (time.monotonic() - start) * 1000
            return stealth_proxy_result

        return stealth_result

    async def _try_normal(
        self,
        url: str,
        *,
        domain: str,
        limit: int,
        raw: bool,
        proxy: str = "",
    ) -> FetchResult:
        start = time.monotonic()
        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            await self._throttle.acquire(domain)
            try:
                kwargs: dict[str, Any] = {
                    "stealthy_headers": True,
                    "timeout": 30,
                    "verify": False,
                    "retries": 1,
                    "follow_redirects": True,
                }
                if proxy:
                    kwargs["proxy"] = proxy

                response = await AsyncFetcher.get(url, **kwargs)

                elapsed_ms = (time.monotonic() - start) * 1000

                if response.status == 429:
                    return FetchResult(
                        content="",
                        status=FetchStatus.RATE_LIMITED,
                        method=FetchMethod.NORMAL,
                        domain=domain,
                        http_status=429,
                        response_time_ms=elapsed_ms,
                    )

                if response.status == 403:
                    return FetchResult(
                        content="",
                        status=FetchStatus.BLOCKED,
                        method=FetchMethod.NORMAL,
                        domain=domain,
                        http_status=403,
                        response_time_ms=elapsed_ms,
                    )

                if response.status >= 400:
                    return FetchResult(
                        content="",
                        status=FetchStatus.ERROR,
                        method=FetchMethod.NORMAL,
                        domain=domain,
                        http_status=response.status,
                        error_message=f"HTTP {response.status} for {url}",
                        response_time_ms=elapsed_ms,
                    )

                html = response.html_content or ""
                if _is_blocked_html(html):
                    return FetchResult(
                        content="",
                        status=FetchStatus.BLOCKED,
                        method=FetchMethod.NORMAL,
                        domain=domain,
                        http_status=response.status,
                        response_time_ms=elapsed_ms,
                    )

                content = self._extract_content(response, html, raw=raw)
                if not content:
                    return FetchResult(
                        content="",
                        status=FetchStatus.EMPTY,
                        method=FetchMethod.NORMAL,
                        domain=domain,
                        http_status=response.status,
                        response_time_ms=elapsed_ms,
                    )

                return FetchResult(
                    content=clamp_text(content, limit),
                    status=FetchStatus.OK,
                    method=FetchMethod.NORMAL,
                    domain=domain,
                    http_status=response.status,
                    response_time_ms=elapsed_ms,
                )

            except (OSError, ConnectionError, TimeoutError) as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    delay = min(
                        RETRY_BASE_DELAY * (2**attempt) + random.uniform(0, 0.5),
                        RETRY_MAX_DELAY,
                    )
                    await asyncio.sleep(delay)
                continue
            finally:
                self._throttle.release(domain)

        elapsed_ms = (time.monotonic() - start) * 1000
        return FetchResult(
            content="",
            status=FetchStatus.ERROR,
            method=FetchMethod.NORMAL,
            domain=domain,
            error_message=str(last_error) if last_error else "All connection attempts failed",
            response_time_ms=elapsed_ms,
        )

    async def _try_stealth(
        self,
        url: str,
        *,
        domain: str,
        limit: int,
        raw: bool,
        proxy: str = "",
    ) -> FetchResult:
        start = time.monotonic()
        await self._throttle.acquire(domain)
        try:
            from scrapling.fetchers import StealthyFetcher

            kwargs: dict[str, Any] = {
                "headless": True,
                "solve_cloudflare": True,
                "block_webrtc": True,
                "google_search": True,
                "network_idle": True,
                "timeout": STEALTH_TIMEOUT,
            }
            if proxy:
                kwargs["proxy"] = proxy

            response = await StealthyFetcher.async_fetch(url, **kwargs)

            elapsed_ms = (time.monotonic() - start) * 1000

            if response.status == 429:
                return FetchResult(
                    content="",
                    status=FetchStatus.RATE_LIMITED,
                    method=FetchMethod.STEALTH,
                    domain=domain,
                    http_status=429,
                    response_time_ms=elapsed_ms,
                )

            if response.status == 403:
                return FetchResult(
                    content="",
                    status=FetchStatus.BLOCKED,
                    method=FetchMethod.STEALTH,
                    domain=domain,
                    http_status=403,
                    response_time_ms=elapsed_ms,
                )

            html = response.html_content or ""
            if _is_blocked_html(html):
                return FetchResult(
                    content="",
                    status=FetchStatus.BLOCKED,
                    method=FetchMethod.STEALTH,
                    domain=domain,
                    http_status=response.status,
                    response_time_ms=elapsed_ms,
                )

            content = self._extract_content(response, html, raw=raw)
            if not content:
                return FetchResult(
                    content="",
                    status=FetchStatus.EMPTY,
                    method=FetchMethod.STEALTH,
                    domain=domain,
                    http_status=response.status,
                    response_time_ms=elapsed_ms,
                )

            return FetchResult(
                content=clamp_text(content, limit),
                status=FetchStatus.OK,
                method=FetchMethod.STEALTH,
                domain=domain,
                http_status=response.status,
                response_time_ms=elapsed_ms,
            )

        except Exception as e:
            elapsed_ms = (time.monotonic() - start) * 1000
            return FetchResult(
                content="",
                status=FetchStatus.ERROR,
                method=FetchMethod.STEALTH,
                domain=domain,
                error_message=str(e),
                response_time_ms=elapsed_ms,
            )
        finally:
            self._throttle.release(domain)

    @staticmethod
    def _extract_content(response: object, html: str, *, raw: bool) -> str:
        if raw:
            return html.strip()

        text = _html_converter.handle(html).strip()
        if not text:
            get_all_text = getattr(response, "get_all_text", None)
            if callable(get_all_text):
                raw_text = get_all_text(separator="\n", strip=True)
                text = str(raw_text).strip() if raw_text else ""
        return text

    async def fetch(self, url: str, *, max_chars: int | None = None) -> str:
        result = await self.resilient_fetch(url, max_chars=max_chars)
        if result.status in (FetchStatus.BLOCKED, FetchStatus.ERROR, FetchStatus.EMPTY):
            msg = (
                result.error_message or f"Fetch failed with status {result.status.value} for {url}"
            )
            raise RuntimeError(msg)
        return result.content

    async def fetch_raw(self, url: str, *, max_chars: int = 50000) -> str:
        result = await self.resilient_fetch(url, max_chars=max_chars, raw=True)
        if result.status in (FetchStatus.BLOCKED, FetchStatus.ERROR, FetchStatus.EMPTY):
            msg = (
                result.error_message or f"Fetch failed with status {result.status.value} for {url}"
            )
            raise RuntimeError(msg)
        return result.content
