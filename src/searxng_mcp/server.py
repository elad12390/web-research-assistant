from __future__ import annotations

import logging
import re
import time
from typing import Annotated, Literal

import httpx
from mcp.server.fastmcp import FastMCP

from .api_docs import APIDocsDetector, APIDocsExtractor, APIDocumentation
from .cache import api_docs_cache
from .changelog import ChangelogFetcher
from .comparison import CATEGORY_ASPECTS, TechComparator, detect_category
from .config import (
    CRAWL_MAX_CHARS,
    DEFAULT_CATEGORY,
    DEFAULT_MAX_RESULTS,
    MAX_RESPONSE_CHARS,
    PROXY_URL,
    SEARCH_PROVIDER,
    clamp_text,
)
from .crawler import CrawlerClient, FetchMethod, FetchResult, FetchStatus
from .domain_health import get_domain_health_tracker
from .errors import ErrorParser
from .exa import ExaSearcher
from .extractor import DataExtractor
from .github import GitHubClient, RepoInfo
from .images import PixabayClient
from .registry import PackageInfo, PackageRegistryClient
from .search import SearchHit, SearxSearcher
from .service_health import ServiceHealthChecker
from .tracking import get_tracker

mcp = FastMCP("web-research-assistant")
searxng_searcher = SearxSearcher()
exa_searcher = ExaSearcher()
crawler_client = CrawlerClient()


async def unified_search(
    query: str,
    *,
    category: str = "general",
    max_results: int = 5,
    time_range: str | None = None,
) -> list[SearchHit]:
    """Unified search that uses Exa or SearXNG based on configuration.

    Provider selection:
    - "exa": Use Exa AI only
    - "searxng": Use SearXNG only
    - "auto" (default): Try Exa first if API key is set, fallback to SearXNG

    Args:
        query: Search query string
        category: Search category (used for SearXNG, mapped to Exa categories)
        max_results: Maximum number of results
        time_range: Time filter (day, week, month, year)

    Returns:
        List of SearchHit objects
    """
    provider = SEARCH_PROVIDER.lower()

    # Map SearXNG categories to Exa categories where applicable
    exa_category_map = {
        "it": None,  # No direct mapping, use general search
        "science": "research paper",
        "news": "news",
        "general": None,
    }

    # Try Exa first if configured and quota is healthy
    exa_available = (
        provider in ("exa", "auto")
        and exa_searcher.has_api_key()
        and not exa_searcher.quota_exhausted
    )
    if exa_available:
        try:
            exa_category = exa_category_map.get(category)

            # Build date filters from time_range
            start_date = None
            if time_range:
                from datetime import datetime, timedelta

                now = datetime.utcnow()
                if time_range == "day":
                    start_date = (now - timedelta(days=1)).isoformat() + "Z"
                elif time_range == "week":
                    start_date = (now - timedelta(weeks=1)).isoformat() + "Z"
                elif time_range == "month":
                    start_date = (now - timedelta(days=30)).isoformat() + "Z"
                elif time_range == "year":
                    start_date = (now - timedelta(days=365)).isoformat() + "Z"

            return await exa_searcher.search(
                query,
                num_results=max_results,
                category=exa_category,
                start_published_date=start_date,
            )
        except Exception as e:
            # If Exa fails and we're in auto mode, try SearXNG
            if provider == "auto":
                logging.warning(f"Exa search failed, falling back to SearXNG: {e}")
            else:
                raise

    # Use SearXNG
    return await searxng_searcher.search(
        query,
        category=category,
        max_results=max_results,
        time_range=time_range,
    )


# Backward compatibility: keep 'searcher' as alias for use in tech_comparator etc.
searcher = searxng_searcher


registry_client = PackageRegistryClient()
github_client = GitHubClient()
pixabay_client = PixabayClient()
error_parser = ErrorParser()
api_docs_detector = APIDocsDetector()
api_docs_extractor = APIDocsExtractor()
data_extractor = DataExtractor()
tech_comparator = TechComparator(searcher, github_client, registry_client)
changelog_fetcher = ChangelogFetcher(github_client, registry_client)
service_health_checker = ServiceHealthChecker(crawler_client)
tracker = get_tracker()
domain_tracker = get_domain_health_tracker()


def _record_domain_health(result: FetchResult) -> None:
    domain_tracker.record(result)


def _format_search_hits(hits):
    lines = []
    for idx, hit in enumerate(hits, 1):
        snippet = f"\n{hit.snippet}" if hit.snippet else ""
        lines.append(f"{idx}. {hit.title} — {hit.url}{snippet}")
    body = "\n\n".join(lines)
    return clamp_text(body, MAX_RESPONSE_CHARS)


@mcp.tool()
async def web_search(
    query: Annotated[str, "Natural-language web query"],
    reasoning: Annotated[str, "Why you're using this tool (required for analytics)"],
    category: Annotated[
        str, "Optional category (general, images, news, it, science, etc.)"
    ] = DEFAULT_CATEGORY,
    max_results: Annotated[int, "How many ranked hits to return (1-10)"] = DEFAULT_MAX_RESULTS,
) -> str:
    """Use this first to gather fresh web search results via the local SearXNG instance."""

    start_time = time.time()
    success = False
    error_msg = None
    result = ""
    provider_used = SEARCH_PROVIDER

    try:
        hits = await unified_search(query, category=category, max_results=max_results)
        if not hits:
            result = f"No results for '{query}' in category '{category}'."
        else:
            result = _format_search_hits(hits)
        success = True
    except Exception as exc:  # noqa: BLE001
        error_msg = str(exc)
        result = f"Search failed: {exc}"
    finally:
        # Track usage
        response_time = (time.time() - start_time) * 1000  # Convert to ms
        tracker.track_usage(
            tool_name="web_search",
            reasoning=reasoning,
            parameters={
                "query": query,
                "category": category,
                "max_results": max_results,
                "provider": provider_used,
            },
            response_time_ms=response_time,
            success=success,
            error_message=error_msg,
            response_size=len(result.encode("utf-8")),
        )

    return result


@mcp.tool()
async def crawl_url(
    url: Annotated[str, "HTTP(S) URL (ideally from web_search output)"],
    reasoning: Annotated[str, "Why you're crawling this URL (required for analytics)"],
    max_chars: Annotated[int, "Trim textual result to this many characters"] = CRAWL_MAX_CHARS,
    country: Annotated[
        str,
        "ISO 3166-1 alpha-2 country code to route proxy through (e.g. 'IL', 'DE', 'US')."
        " Auto-detected from domain ccTLD if not specified.",
    ] = "",
) -> str:
    """Fetch a URL and return the page text as markdown for quoting or analysis."""

    start_time = time.time()
    success = False
    error_msg = None
    result = ""
    fetch_result: FetchResult | None = None

    try:
        fetch_result = await crawler_client.resilient_fetch(
            url, max_chars=max_chars, country=country
        )
        _record_domain_health(fetch_result)

        if fetch_result.status == FetchStatus.OK:
            result = clamp_text(fetch_result.content, MAX_RESPONSE_CHARS)
            success = True
        elif fetch_result.status == FetchStatus.BLOCKED:
            result = (
                f"Blocked by anti-bot protection on {fetch_result.domain} "
                f"(HTTP {fetch_result.http_status}). Tried: {fetch_result.method.value}."
            )
        elif fetch_result.status == FetchStatus.RATE_LIMITED:
            result = f"Rate limited by {fetch_result.domain} (HTTP 429). Please wait and retry."
        else:
            error_msg = fetch_result.error_message
            result = (
                f"Crawl failed for {url}: {fetch_result.error_message or fetch_result.status.value}"
            )
    except Exception as exc:  # noqa: BLE001
        error_msg = str(exc)
        result = f"Crawl failed for {url}: {exc}"
    finally:
        response_time = (time.time() - start_time) * 1000
        tracker.track_usage(
            tool_name="crawl_url",
            reasoning=reasoning,
            parameters={
                "url": url,
                "max_chars": max_chars,
                "domain": fetch_result.domain if fetch_result else "",
                "fetch_method": fetch_result.method.value if fetch_result else "",
                "fetch_status": fetch_result.status.value if fetch_result else "",
            },
            response_time_ms=response_time,
            success=success,
            error_message=error_msg,
            response_size=len(result.encode("utf-8")),
        )

    return result


@mcp.tool()
async def stealth_scrape(
    url: Annotated[str, "HTTP(S) URL of a page protected by anti-bot measures (Cloudflare, etc.)"],
    reasoning: Annotated[
        str, "Why you need stealth scraping for this URL (required for analytics)"
    ],
    max_chars: Annotated[int, "Trim textual result to this many characters"] = CRAWL_MAX_CHARS,
    wait_selector: Annotated[
        str | None, "CSS selector to wait for before extracting content"
    ] = None,
    solve_cloudflare: Annotated[
        bool, "Attempt to solve Cloudflare challenges automatically"
    ] = True,
    headless: Annotated[bool, "Run browser in headless mode (no visible window)"] = True,
    country: Annotated[
        str,
        "ISO 3166-1 alpha-2 country code to route proxy through (e.g. 'IL', 'DE', 'US')."
        " Auto-detected from domain ccTLD if not specified.",
    ] = "",
) -> str:
    """Scrape a URL using a stealth browser that bypasses anti-bot protections.

    Uses scrapling's StealthyFetcher with Patchright (hardened Playwright) to evade
    Cloudflare, DataDome, and similar anti-bot systems. Much slower than crawl_url
    but works on protected sites.

    Requires browser binaries: run 'scrapling install' once before first use.

    When to use:
    - crawl_url returns a Cloudflare challenge page or empty content
    - The target site blocks automated requests
    - JavaScript rendering is required for the content to appear
    - You need to wait for a specific element to load

    Examples:
    - stealth_scrape("https://protected-site.com/pricing")
    - stealth_scrape("https://spa-app.com/data", wait_selector=".results-table")
    """
    import urllib.parse

    import html2text
    from scrapling.fetchers import StealthyFetcher

    domain = urllib.parse.urlparse(url).netloc
    start_time = time.time()
    success = False
    error_msg = None
    result = ""

    try:
        from .crawler import _detect_country_code, _geo_targeted_proxy

        fetch_kwargs: dict = {
            "headless": headless,
            "solve_cloudflare": solve_cloudflare,
            "block_webrtc": True,
            "google_search": True,
            "network_idle": True,
            "timeout": 30000,
        }
        if wait_selector:
            fetch_kwargs["wait_selector"] = wait_selector
            fetch_kwargs["wait_selector_state"] = "visible"

        if country or PROXY_URL:
            geo_code = country.upper() if country else _detect_country_code(domain)
            geo_proxy = _geo_targeted_proxy(PROXY_URL, geo_code)
            if geo_proxy:
                fetch_kwargs["proxy"] = geo_proxy

        response = await StealthyFetcher.async_fetch(url, **fetch_kwargs)

        html = response.html_content or ""
        if not html.strip():
            raise RuntimeError("Stealth scrape returned no content.")

        converter = html2text.HTML2Text()
        converter.ignore_links = False
        converter.body_width = 0
        converter.ignore_images = True
        text = converter.handle(html).strip()

        if not text:
            text = response.get_all_text(separator="\n", strip=True) or ""
            text = text.strip()

        if not text:
            raise RuntimeError("Stealth scrape returned no readable content.")

        limit = max_chars or CRAWL_MAX_CHARS
        result = clamp_text(text, min(limit, MAX_RESPONSE_CHARS))
        success = True

        _record_domain_health(
            FetchResult(
                content=result,
                status=FetchStatus.OK,
                method=FetchMethod.STEALTH,
                domain=domain,
                http_status=getattr(response, "status", None),
            )
        )

    except Exception as exc:  # noqa: BLE001
        error_msg = str(exc)
        result = (
            f"Stealth scrape failed for {url}: {exc}\n\n"
            "Make sure browser binaries are installed: run 'scrapling install'"
        )
        _record_domain_health(
            FetchResult(
                content="",
                status=FetchStatus.ERROR,
                method=FetchMethod.STEALTH,
                domain=domain,
                error_message=error_msg,
            )
        )
    finally:
        response_time = (time.time() - start_time) * 1000
        tracker.track_usage(
            tool_name="stealth_scrape",
            reasoning=reasoning,
            parameters={
                "url": url,
                "max_chars": max_chars,
                "wait_selector": wait_selector,
                "solve_cloudflare": solve_cloudflare,
                "domain": domain,
                "fetch_method": "stealth",
            },
            response_time_ms=response_time,
            success=success,
            error_message=error_msg,
            response_size=len(result.encode("utf-8")),
        )

    return result


def _format_package_info(info: PackageInfo) -> str:
    lines = [
        f"Package: {info.name} ({info.registry})",
        "─" * 50,
        f"Version: {info.version}",
    ]

    if info.license:
        lines.append(f"License: {info.license}")

    if info.downloads:
        lines.append(f"Downloads: {info.downloads}")

    lines.append(f"Last Updated: {info.last_updated}")

    if info.dependencies_count is not None:
        lines.append(f"Dependencies: {info.dependencies_count}")

    if info.security_issues > 0:
        lines.append(f"⚠️  Security Issues: {info.security_issues}")
    else:
        lines.append("Security: ✅ No known vulnerabilities")

    lines.append("")  # blank line

    if info.repository:
        lines.append(f"Repository: {info.repository}")

    if info.homepage and info.homepage != info.repository:
        lines.append(f"Homepage: {info.homepage}")

    if info.description:
        lines.append(f"\nDescription: {info.description}")

    return "\n".join(lines)


@mcp.tool()
async def package_info(
    name: Annotated[str, "Package or module name to look up"],
    reasoning: Annotated[str, "Why you're looking up this package (required for analytics)"],
    registry: Annotated[
        Literal["npm", "pypi", "crates", "go"],
        "Package registry to search (npm, pypi, crates, go)",
    ] = "npm",
) -> str:
    """
    Look up package information from npm, PyPI, crates.io, or Go modules.

    Returns version, downloads, license, dependencies, security status, and repository links.
    Use this to quickly evaluate libraries before adding them to your project.

    Examples:
    - package_info("express", reasoning="Need web framework", registry="npm")
    - package_info("requests", reasoning="HTTP client for API", registry="pypi")
    - package_info("serde", reasoning="JSON serialization", registry="crates")
    """
    start_time = time.time()
    success = False
    error_msg = None
    result = ""

    try:
        if registry == "npm":
            info = await registry_client.search_npm(name)
        elif registry == "pypi":
            info = await registry_client.search_pypi(name)
        elif registry == "crates":
            info = await registry_client.search_crates(name)
        else:  # go
            info = await registry_client.search_go(name)

        result = clamp_text(_format_package_info(info), MAX_RESPONSE_CHARS)
        success = True
    except httpx.HTTPStatusError as exc:
        error_msg = f"HTTP {exc.response.status_code}"
        if exc.response.status_code == 404:
            result = f"Package '{name}' not found on {registry}.\n\nDouble-check the package name and try again."
        else:
            result = f"Failed to fetch {registry} package '{name}': HTTP {exc.response.status_code}"
    except Exception as exc:  # noqa: BLE001
        error_msg = str(exc)
        result = f"Failed to fetch {registry} package '{name}': {exc}"
    finally:
        # Track usage
        response_time = (time.time() - start_time) * 1000
        tracker.track_usage(
            tool_name="package_info",
            reasoning=reasoning,
            parameters={"name": name, "registry": registry},
            response_time_ms=response_time,
            success=success,
            error_message=error_msg,
            response_size=len(result.encode("utf-8")),
        )

    return result


@mcp.tool()
async def search_examples(
    query: Annotated[
        str,
        "What you're looking for (e.g., 'Python async await examples', 'React hooks tutorial', 'Rust error handling patterns')",
    ],
    reasoning: Annotated[str, "Why you're searching for examples (required for analytics)"],
    content_type: Annotated[
        Literal["code", "articles", "both"],
        "Type of content to find: 'code' for code examples, 'articles' for tutorials/blogs, 'both' for mixed results",
    ] = "both",
    time_range: Annotated[
        Literal["day", "week", "month", "year", "all"],
        "How recent the content should be (use 'all' for best results, filter down if too many results)",
    ] = "all",
    max_results: Annotated[int, "How many results to return (1-10)"] = DEFAULT_MAX_RESULTS,
) -> str:
    """
    Search for code examples, tutorials, and technical articles.

    Optimized for finding practical examples and learning resources. Can optionally filter by
    time range for the most recent content. Perfect for learning new APIs, finding usage patterns,
    or discovering how others solve specific technical problems.

    Content Types:
    - 'code': GitHub repos, code snippets, gists, Stack Overflow code examples
    - 'articles': Blog posts, tutorials, documentation, technical articles
    - 'both': Mix of code and written content (default)

    Time Ranges:
    - 'all': Search all available content (default, recommended for best results)
    - 'year', 'month', 'week', 'day': Filter to recent content only

    Examples:
    - search_examples("FastAPI dependency injection examples", content_type="code")
    - search_examples("React hooks tutorial", content_type="articles", time_range="year")
    - search_examples("Rust lifetime examples", content_type="both")
    """
    start_time = time.time()
    success = False
    error_msg = None
    result = ""

    try:
        max_results = max(1, min(max_results, 10))

        # Build optimized search query based on content type
        enhanced_query = query
        if content_type == "code":
            # Prioritize code-heavy sources
            enhanced_query = f"{query} (site:github.com OR site:stackoverflow.com OR site:gist.github.com OR example OR snippet)"
        elif content_type == "articles":
            # Prioritize articles and tutorials
            enhanced_query = (
                f"{query} (tutorial OR guide OR article OR blog OR how to OR documentation)"
            )
        else:  # both
            enhanced_query = f"{query} (example OR tutorial OR guide)"

        # Use 'it' category for better tech content
        hits = await unified_search(
            enhanced_query,
            category="it",  # IT/tech category for better results
            max_results=max_results,
            time_range=time_range if time_range != "all" else None,
        )

        if not hits:
            result = (
                f"No examples found for '{query}' in the {time_range if time_range != 'all' else 'all time'} range.\n\n"
                "Try:\n"
                "- Broader search terms\n"
                "- Different time range\n"
                "- Removing version numbers or very specific constraints\n\n"
                "Note: Results depend on your SearXNG instance configuration. If you're only seeing MDN docs,\n"
                "your SearXNG may need additional search engines enabled (GitHub, Stack Overflow, dev.to, etc.)."
            )
        else:
            # Format results with additional context
            lines = [
                f"Code Examples & Articles for: {query}",
                f"Time Range: {time_range.title() if time_range != 'all' else 'All time'} | Content Type: {content_type.title()}",
                "─" * 50,
                "",
            ]

            for idx, hit in enumerate(hits, 1):
                # Add source indicator
                source = ""
                if "github.com" in hit.url:
                    source = "[GitHub] "
                elif "stackoverflow.com" in hit.url:
                    source = "[Stack Overflow] "
                elif "medium.com" in hit.url or "dev.to" in hit.url:
                    source = "[Article] "

                snippet = f"\n   {hit.snippet}" if hit.snippet else ""
                lines.append(f"{idx}. {source}{hit.title}")
                lines.append(f"   {hit.url}{snippet}")
                lines.append("")

            result_text = "\n".join(lines)

            # Add note if results seem limited (all from same domain)
            domains = set()
            for hit in hits:
                if "://" in hit.url:
                    domain = hit.url.split("://")[1].split("/")[0]
                    domains.add(domain)

            if len(domains) == 1 and len(hits) > 2:
                result_text += (
                    "\n\n──────────────────────────────────────────────────\n"
                    "ℹ️ Note: All results are from the same source. Your SearXNG instance may need\n"
                    "   additional search engines configured (GitHub, Stack Overflow, dev.to, Medium)\n"
                    "   to get diverse code examples and tutorials."
                )

            result = clamp_text(result_text, MAX_RESPONSE_CHARS)

        success = True
    except Exception as exc:  # noqa: BLE001
        error_msg = str(exc)
        result = f"Search failed for '{query}': {exc}"
    finally:
        # Track usage
        response_time = (time.time() - start_time) * 1000
        tracker.track_usage(
            tool_name="search_examples",
            reasoning=reasoning,
            parameters={
                "query": query,
                "content_type": content_type,
                "time_range": time_range,
                "max_results": max_results,
            },
            response_time_ms=response_time,
            success=success,
            error_message=error_msg,
            response_size=len(result.encode("utf-8")),
        )

    return result


@mcp.tool()
async def search_images(
    query: Annotated[
        str,
        "What to search for (e.g., 'sunset beach', 'office workspace', 'technology abstract')",
    ],
    reasoning: Annotated[str, "Why you're searching for images (required for analytics)"],
    image_type: Annotated[
        Literal["all", "photo", "illustration", "vector"],
        "Type of image to search for",
    ] = "all",
    orientation: Annotated[
        Literal["all", "horizontal", "vertical"],
        "Image orientation preference",
    ] = "all",
    max_results: Annotated[int, "Maximum number of results (1-20)"] = 10,
) -> str:
    """
    Search for high-quality stock images using Pixabay.

    Returns royalty-free images that are safe to use. Perfect for finding photos,
    illustrations, and vector graphics for projects, presentations, or design work.

    Image Types:
    - 'photo': Real photographs
    - 'illustration': Digital illustrations and artwork
    - 'vector': Vector graphics (SVG format available)
    - 'all': All types (default)

    Examples:
    - search_images("mountain landscape", image_type="photo")
    - search_images("business icons", image_type="vector")
    - search_images("technology background", orientation="horizontal")
    """
    start_time = time.time()
    success = False
    error_msg = None
    result = ""

    try:
        # Check if API key is configured
        if not pixabay_client.has_api_key():
            # Fallback: Use web search for images instead (use SearXNG directly for images)
            fallback_results = await searxng_searcher.search(
                f"{query} stock photo free",
                category="images",
                max_results=max_results,
            )

            if fallback_results:
                lines = [
                    f"Image Search Results for: {query}",
                    "(Using web search - configure PIXABAY_API_KEY for better stock photo results)",
                    "─" * 70,
                    "",
                ]
                for idx, hit in enumerate(fallback_results, 1):
                    lines.append(f"{idx}. {hit.title}")
                    lines.append(f"   {hit.url}")
                    if hit.snippet:
                        lines.append(f"   {hit.snippet[:100]}")
                    lines.append("")

                lines.extend(
                    [
                        "─" * 70,
                        "For better stock photo results with resolution info:",
                        "1. Get a free API key from: https://pixabay.com/api/docs/",
                        "2. Set: PIXABAY_API_KEY=your_key_here",
                    ]
                )
                result = clamp_text("\n".join(lines), MAX_RESPONSE_CHARS)
                success = True  # Mark as success since we provided useful results
            else:
                result = (
                    "⚠️ Pixabay API key not configured and web search returned no results.\n\n"
                    "To enable full image search:\n"
                    "1. Get a free API key from: https://pixabay.com/api/docs/\n"
                    "2. Set the environment variable: PIXABAY_API_KEY=your_key_here\n"
                    "3. Restart the MCP server"
                )
                error_msg = "API key not configured"
                success = False
        else:
            max_results = max(1, min(max_results, 20))

            images = await pixabay_client.search_images(
                query=query,
                image_type=image_type,
                orientation=orientation,
                per_page=max_results,
            )

            if not images:
                result = f"No images found for '{query}'.\n\nTry:\n- Different search terms\n- Broader keywords\n- Different image type or orientation"
            else:
                # Format results
                lines = [
                    f"Stock Images for: {query}",
                    f"Type: {image_type.title()} | Orientation: {orientation.title()} | Found: {len(images)} images",
                    "─" * 70,
                    "",
                ]

                for idx, img in enumerate(images, 1):
                    lines.append(f"{idx}. {img.tags}")
                    lines.append(
                        f"   Resolution: {img.width}x{img.height} | 👁️ {img.views:,} | ⬇️ {img.downloads:,} | ❤️ {img.likes:,}"
                    )
                    lines.append(f"   By: {img.user}")
                    lines.append(f"   Preview: {img.preview_url}")
                    lines.append(f"   Large: {img.large_url}")
                    if img.full_url != img.large_url:
                        lines.append(f"   Full HD: {img.full_url}")
                    lines.append("")

                result = clamp_text("\n".join(lines), MAX_RESPONSE_CHARS)

            success = True

    except ValueError as exc:
        # API key not configured
        error_msg = str(exc)
        result = f"⚠️ {exc}\n\nPlease configure your Pixabay API key as described above."
    except httpx.HTTPStatusError as exc:
        error_msg = f"HTTP {exc.response.status_code}"
        if exc.response.status_code == 400:
            result = f"Invalid search parameters for '{query}'. Please check your search terms and filters."
        elif exc.response.status_code == 429:
            result = "Rate limit exceeded. Please wait a moment and try again."
        else:
            result = f"Failed to search images: HTTP {exc.response.status_code}"
    except Exception as exc:  # noqa: BLE001
        error_msg = str(exc)
        result = f"Image search failed for '{query}': {exc}"
    finally:
        # Track usage
        response_time = (time.time() - start_time) * 1000
        tracker.track_usage(
            tool_name="search_images",
            reasoning=reasoning,
            parameters={
                "query": query,
                "image_type": image_type,
                "orientation": orientation,
                "max_results": max_results,
            },
            response_time_ms=response_time,
            success=success,
            error_message=error_msg,
            response_size=len(result.encode("utf-8")),
        )

    return result


def _format_package_search_results(packages: list[PackageInfo], query: str, registry: str) -> str:
    """Format package search results into readable text."""

    if not packages:
        return f"No packages found for '{query}' on {registry}.\n\nTry different keywords or check another registry."

    lines = [
        f"Search Results for '{query}' on {registry}:",
        "─" * 50,
    ]

    for i, pkg in enumerate(packages, 1):
        lines.append(f"{i}. {pkg.name}")
        if pkg.version != "unknown":
            lines.append(f"   Version: {pkg.version}")
        if pkg.downloads:
            lines.append(f"   Downloads: {pkg.downloads}")
        if pkg.description:
            # Truncate long descriptions
            desc = pkg.description[:100] + "..." if len(pkg.description) > 100 else pkg.description
            lines.append(f"   Description: {desc}")
        lines.append("")  # blank line between results

    return "\n".join(lines)


@mcp.tool()
async def package_search(
    query: Annotated[
        str,
        "Search keywords (e.g., 'web framework', 'json parser', 'machine learning')",
    ],
    reasoning: Annotated[str, "Why you're searching for packages (required for analytics)"],
    registry: Annotated[
        Literal["npm", "pypi", "crates", "go"],
        "Package registry to search (npm, pypi, crates, go)",
    ] = "npm",
    max_results: Annotated[int, "Maximum number of results to return (1-10)"] = 5,
) -> str:
    """
    Search for packages by keywords or description across registries.

    Use this to find packages that solve a specific problem or provide certain functionality.
    Perfect for discovering libraries when you know what you need but not the package name.

    Examples:
    - package_search("web framework", reasoning="Need backend framework", registry="npm")
    - package_search("json parsing", reasoning="Data processing", registry="pypi")
    """
    start_time = time.time()
    success = False
    error_msg = None
    result = ""

    try:
        max_results = max(1, min(max_results, 10))  # Clamp to 1-10

        packages = await registry_client.search_packages(query, registry, max_results)
        result = _format_package_search_results(packages, query, registry)
        result = clamp_text(result, MAX_RESPONSE_CHARS)
        success = True
    except Exception as exc:  # noqa: BLE001
        error_msg = str(exc)
        result = f"Search failed for '{query}' on {registry}: {exc}"
    finally:
        # Track usage
        response_time = (time.time() - start_time) * 1000
        tracker.track_usage(
            tool_name="package_search",
            reasoning=reasoning,
            parameters={
                "query": query,
                "registry": registry,
                "max_results": max_results,
            },
            response_time_ms=response_time,
            success=success,
            error_message=error_msg,
            response_size=len(result.encode("utf-8")),
        )

    return result


def _format_repo_info(info: RepoInfo, commits=None) -> str:
    """Format RepoInfo into readable text response."""

    lines = [
        f"Repository: {info.full_name}",
        "─" * 50,
        f"⭐ {info.stars:,} | 🍴 {info.forks:,} | 👁️ {info.watchers:,}",
    ]

    if info.language:
        lines.append(f"Language: {info.language}")

    if info.license:
        lines.append(f"License: {info.license}")

    lines.append(f"Last Updated: {info.last_updated}")

    # Issues and PRs
    issue_line = f"Open Issues: {info.open_issues}"
    if info.open_prs is not None:
        issue_line += f" | Open PRs: {info.open_prs}"
    lines.append(issue_line)

    if info.archived:
        lines.append("⚠️ This repository is archived (read-only)")

    if info.topics:
        lines.append(f"Topics: {', '.join(info.topics[:5])}")  # Show first 5 topics

    lines.append("")  # blank line

    if info.homepage:
        lines.append(f"Homepage: {info.homepage}")

    if commits:
        lines.append("Recent Commits:")
        for commit in commits[:3]:  # Show top 3
            lines.append(f"- [{commit.date}] {commit.message} ({commit.author})")

    lines.append(f"\nDescription: {info.description}")

    return "\n".join(lines)


@mcp.tool()
async def github_repo(
    repo: Annotated[str, "GitHub repository (owner/repo format or full URL)"],
    reasoning: Annotated[str, "Why you're checking this repository (required for analytics)"],
    include_commits: Annotated[bool, "Include recent commit history"] = True,
) -> str:
    """
    Fetch GitHub repository information and health metrics.

    Returns stars, forks, issues, recent activity, language, license, and description.
    Use this to evaluate open source projects before using them.

    Examples:
    - github_repo("microsoft/vscode", reasoning="Evaluate editor project")
    - github_repo("https://github.com/facebook/react", reasoning="Research UI framework")
    """
    start_time = time.time()
    success = False
    error_msg = None
    result = ""

    try:
        owner, repo_name = github_client.parse_repo_url(repo)

        # Get repo info
        repo_info = await github_client.get_repo_info(owner, repo_name)

        # Optionally get recent commits
        commits = None
        if include_commits:
            try:
                commits = await github_client.get_recent_commits(owner, repo_name, count=3)
            except Exception:  # noqa: BLE001, S110
                # Don't fail the whole request if commits fail
                pass

        result = clamp_text(_format_repo_info(repo_info, commits), MAX_RESPONSE_CHARS)
        success = True

    except httpx.HTTPStatusError as exc:
        error_msg = f"HTTP {exc.response.status_code}"
        if exc.response.status_code == 404:
            # Try to provide helpful suggestions
            suggestions = []
            if "/" in repo:
                parts = repo.replace("https://github.com/", "").split("/")
                if len(parts) >= 2:
                    owner_guess = parts[0]
                    suggestions.append(
                        f"- Check if '{owner_guess}' is the correct organization/user"
                    )
                    suggestions.append("- The repository may have been renamed or deleted")
                    suggestions.append(f"- Try searching: https://github.com/search?q={parts[1]}")

            result = (
                f"Repository '{repo}' not found (HTTP 404).\n\n"
                f"Possible reasons:\n"
                f"- The repository doesn't exist or was deleted\n"
                f"- The repository is private\n"
                f"- There's a typo in the owner or repository name\n"
            )
            if suggestions:
                result += "\nSuggestions:\n" + "\n".join(suggestions)
        elif exc.response.status_code == 403:
            result = (
                f"Access denied to repository '{repo}' (HTTP 403).\n\n"
                f"Possible reasons:\n"
                f"- The repository is private\n"
                f"- GitHub API rate limit exceeded\n"
                f"- Set GITHUB_TOKEN environment variable for higher rate limits"
            )
        elif exc.response.status_code == 301:
            # This shouldn't happen anymore with our redirect handling, but just in case
            result = (
                f"Repository '{repo}' has moved (HTTP 301).\n\n"
                f"The repository may have been renamed or transferred.\n"
                f"Try searching for the new location on GitHub."
            )
        else:
            result = f"Failed to fetch repository '{repo}': HTTP {exc.response.status_code}"
    except ValueError as exc:
        error_msg = str(exc)
        result = str(exc)  # Invalid repo format - already has good error message
    except Exception as exc:  # noqa: BLE001
        error_msg = str(exc)
        result = f"Failed to fetch repository '{repo}': {exc}"
    finally:
        # Track usage
        response_time = (time.time() - start_time) * 1000
        tracker.track_usage(
            tool_name="github_repo",
            reasoning=reasoning,
            parameters={"repo": repo, "include_commits": include_commits},
            response_time_ms=response_time,
            success=success,
            error_message=error_msg,
            response_size=len(result.encode("utf-8")),
        )

    return result


@mcp.tool()
async def translate_error(
    error_message: Annotated[str, "The error message or stack trace to investigate"],
    reasoning: Annotated[str, "Why you're investigating this error (required for analytics)"],
    language: Annotated[str | None, "Programming language (auto-detected if not provided)"] = None,
    framework: Annotated[
        str | None, "Framework context (e.g., 'React', 'FastAPI', 'Django')"
    ] = None,
    max_results: Annotated[int, "Number of solutions to return (1-10)"] = 5,
) -> str:
    """
    Find solutions for error messages and stack traces from Stack Overflow and GitHub.

    Takes an error message or stack trace and finds relevant solutions with code examples.
    Automatically detects language and framework, extracts key error information, and
    searches for the best solutions ranked by votes and relevance.

    Perfect for:
    - Debugging production errors
    - Understanding cryptic error messages
    - Finding working code fixes
    - Learning from similar issues

    Examples:
    - translate_error("TypeError: Cannot read property 'map' of undefined", reasoning="Debugging React app crash")
    - translate_error("CORS policy: No 'Access-Control-Allow-Origin' header", reasoning="Fixing API integration", framework="FastAPI")
    - translate_error("error[E0382]: borrow of moved value", reasoning="Learning Rust ownership", language="rust")
    """
    start_time = time.time()
    success = False
    error_msg = None
    result = ""
    parsed = None

    try:
        max_results = max(1, min(max_results, 10))

        # Parse the error message
        parsed = error_parser.parse(error_message, language=language, framework=framework)

        # Build search query
        search_query = error_parser.build_search_query(parsed)

        # Search for solutions (request more to allow for filtering)
        hits = await unified_search(
            search_query,
            category="it",
            max_results=max_results * 2,  # Get extra results for filtering
        )

        # Filter and prioritize results
        if hits:
            # Filter out irrelevant sources
            irrelevant_domains = {
                "hub.docker.com",
                "crates.io",
                "npmjs.com",
                "pypi.org",
                "pkg.go.dev",
            }

            filtered_hits = [
                hit
                for hit in hits
                if not any(domain in hit.url.lower() for domain in irrelevant_domains)
            ]

            # Prioritize Stack Overflow results
            so_hits = [hit for hit in filtered_hits if "stackoverflow.com" in hit.url]
            other_hits = [hit for hit in filtered_hits if "stackoverflow.com" not in hit.url]

            # Combine: Stack Overflow first, then others
            hits = (so_hits + other_hits)[:max_results]

        if not hits:
            result = (
                f"No solutions found for this error.\n\n"
                f"Parsed Error Info:\n"
                f"- Type: {parsed.error_type}\n"
                f"- Language: {parsed.language or 'Unknown'}\n"
                f"- Framework: {parsed.framework or 'None detected'}\n\n"
                f"Try:\n"
                f"- Providing more context with language/framework parameters\n"
                f"- Searching for just the error type: {parsed.error_type}\n"
                f"- Using web_search with broader terms"
            )
        else:
            # Format results
            lines = [
                "Error Translation Results",
                "═" * 70,
                "",
                "📋 Parsed Error Information:",
                f"   Error Type: {parsed.error_type}",
            ]

            if parsed.language:
                lines.append(f"   Language: {parsed.language.title()}")
            if parsed.framework:
                lines.append(f"   Framework: {parsed.framework.title()}")
            if parsed.file_path:
                location = f"{parsed.file_path}"
                if parsed.line_number:
                    location += f":{parsed.line_number}"
                lines.append(f"   Location: {location}")

            lines.extend(
                [
                    "",
                    f"🔍 Search Query: {search_query}",
                    "",
                    "💡 Top Solutions (Stack Overflow prioritized):",
                    "─" * 70,
                    "",
                ]
            )

            for idx, hit in enumerate(hits, 1):
                # Try to extract vote count from snippet (if available)
                votes = "N/A"
                if hit.snippet:
                    vote_match = re.search(r"(\d+)\s*votes?", hit.snippet, re.IGNORECASE)
                    if vote_match:
                        votes = vote_match.group(1)

                # Check if it's a Stack Overflow link
                is_so = "stackoverflow.com" in hit.url
                source_icon = "[SO]" if is_so else "[Web]"

                lines.append(f"{idx}. {source_icon} {hit.title}")
                if votes != "N/A":
                    lines.append(f"   Votes: {votes}")
                lines.append(f"   {hit.url}")

                if hit.snippet:
                    # Clean and truncate snippet
                    snippet = hit.snippet.replace("\n", " ").strip()
                    if len(snippet) > 200:
                        snippet = snippet[:200] + "..."
                    lines.append(f"   {snippet}")

                lines.append("")

            lines.extend(
                [
                    "─" * 70,
                    "",
                    "💡 Tips:",
                    "- Check accepted answers (marked with ✓) first",
                    "- Look for solutions with high vote counts",
                    "- Verify the solution matches your exact error",
                    "- Use crawl_url to get full answer details",
                ]
            )

            result = clamp_text("\n".join(lines), MAX_RESPONSE_CHARS)

        success = True

    except Exception as exc:  # noqa: BLE001
        error_msg = str(exc)
        result = f"Error translation failed: {exc}\n\nTry simplifying the error message or provide language/framework context."
    finally:
        # Track usage
        response_time = (time.time() - start_time) * 1000
        tracker.track_usage(
            tool_name="translate_error",
            reasoning=reasoning,
            parameters={
                "error_type": parsed.error_type if parsed else "unknown",
                "language": language or (parsed.language if parsed else None),
                "framework": framework or (parsed.framework if parsed else None),
                "max_results": max_results,
            },
            response_time_ms=response_time,
            success=success,
            error_message=error_msg,
            response_size=len(result.encode("utf-8")),
        )

    return result


@mcp.tool()
async def api_docs(
    api_name: Annotated[str, "API name (e.g., 'stripe', 'github') or base docs URL"],
    reasoning: Annotated[str, "Why you're looking up this API (required for analytics)"],
    topic: Annotated[
        str,
        "What to search for (e.g., 'create customer', 'webhooks', 'authentication')",
    ],
    max_results: Annotated[int, "Number of doc pages to fetch (1-3)"] = 2,
) -> str:
    """
    Search and fetch official API documentation with examples and explanations.

    Documentation-first approach: fetches human-written docs with context, examples,
    and best practices. Much more useful than OpenAPI specs alone.

    Discovery strategy:
    1. Try common URL patterns (docs.{api}.com, {api}.com/docs, etc.)
    2. If patterns fail, search for "{api} API official documentation"
    3. Crawl discovered docs and extract relevant content

    No hardcoded URLs - works for ANY API by discovering docs dynamically.

    Examples:
    - api_docs("stripe", "create customer", reasoning="Setting up payments")
    - api_docs("github", "create repository", reasoning="Automating repo creation")
    - api_docs("spartan", "button component", reasoning="Learning UI library")
    """
    start_time = time.time()
    success = False
    error_msg = None
    result = ""
    docs_url = None

    # Check cache first
    cache_key = f"api_docs:{api_name.lower()}:{topic.lower()}"
    cached_result = await api_docs_cache.get(cache_key)
    if cached_result:
        # Track cache hit
        tracker.track_usage(
            tool_name="api_docs",
            reasoning=reasoning,
            parameters={
                "api_name": api_name,
                "topic": topic,
                "docs_url": "cached",
                "max_results": max_results,
            },
            response_time_ms=(time.time() - start_time) * 1000,
            success=True,
            error_message=None,
            response_size=len(cached_result.encode("utf-8")),
        )
        return cached_result

    try:
        max_results = max(1, min(max_results, 3))  # Clamp to 1-3

        # Get alternative search terms for the API
        search_terms = api_docs_detector.get_search_terms(api_name)

        # Find documentation URL
        docs_url = await api_docs_detector.find_docs_url(api_name)

        if not docs_url:
            # Fallback: Search for official docs using multiple search terms
            for search_term in search_terms:
                search_results = await unified_search(
                    f"{search_term} official documentation",
                    category="general",
                    max_results=5,
                )

                # Filter for docs-like URLs
                for hit in search_results:
                    if any(
                        indicator in hit.url.lower()
                        for indicator in ["docs", "developer", "api", "reference"]
                    ):
                        docs_url = hit.url
                        # Extract base URL (remove path beyond /docs or /api)
                        if "/docs" in docs_url:
                            docs_url = docs_url.split("/docs")[0] + "/docs"
                        elif "/api" in docs_url:
                            docs_url = docs_url.split("/api")[0] + "/api"
                        break

                if docs_url:
                    break

        if not docs_url:
            result = (
                f"Could not find official documentation for '{api_name}'.\n\n"
                f"Try:\n"
                f"- Checking the API name spelling\n"
                f"- Providing the docs URL directly (e.g., 'https://docs.example.com')\n"
                f"- Using web_search to find the documentation manually"
            )
            error_msg = "Documentation URL not found"
            success = False
        else:
            # Get the domain for site-specific search
            docs_domain = api_docs_detector.get_docs_domain(docs_url)

            # IMPROVED SEARCH STRATEGY:
            # Primary: Search with API name + topic (works better than site: operator in SearXNG)
            search_query = f"{api_name} {topic} documentation"
            doc_results = await unified_search(
                search_query, category="it", max_results=max_results * 3
            )

            # Filter & sort: prefer results from the official docs domain
            if doc_results:
                doc_results = sorted(
                    doc_results,
                    key=lambda r: 0 if docs_domain in r.url else 1,
                )

            # Fallback 1: Try API reference style search
            if not doc_results:
                doc_results = await unified_search(
                    f"{api_name} API reference {topic}",
                    category="it",
                    max_results=max_results * 2,
                )

            # Fallback 2: Try with each search term variation
            if not doc_results:
                for search_term in search_terms[:2]:
                    doc_results = await unified_search(
                        f"{search_term} {topic}",
                        category="it",
                        max_results=max_results * 2,
                    )
                    if doc_results:
                        break

            # Fallback 3: Simplify the topic (extract key terms) and try again
            if not doc_results and len(topic.split()) > 3:
                # Remove version numbers, common filler words
                simplified = re.sub(r"\bv\d+\b", "", topic, flags=re.IGNORECASE)
                simplified = re.sub(
                    r"\b(api|the|a|an|and|or|for|to|with|using)\b",
                    "",
                    simplified,
                    flags=re.IGNORECASE,
                )
                key_terms = [w for w in simplified.split() if len(w) > 2][:3]
                if key_terms:
                    simplified_topic = " ".join(key_terms)
                    doc_results = await unified_search(
                        f"{api_name} {simplified_topic}",
                        category="it",
                        max_results=max_results * 2,
                    )

            # Fallback 4: Try common documentation URL paths directly
            if not doc_results and docs_url:
                common_paths = [
                    "/api/{topic}",
                    "/reference/{topic}",
                    "/docs/{topic}",
                    "/guide/{topic}",
                    "/docs/api/{topic}",
                    "/{topic}",
                ]
                topic_slug = topic.lower().replace(" ", "-").replace("_", "-")
                for path_pattern in common_paths:
                    try_url = docs_url.rstrip("/") + path_pattern.format(topic=topic_slug)
                    try:
                        content = await crawler_client.fetch(try_url, max_chars=15000)
                        if content and len(content) > 500:
                            doc_results = [SearchHit(title=topic, url=try_url, snippet="")]
                            break
                    except Exception:  # noqa: BLE001
                        continue

            # Fallback 5: Crawl the base docs URL directly
            if not doc_results and docs_url:
                try:
                    base_content = await crawler_client.fetch(docs_url, max_chars=15000)
                    if base_content and len(base_content) > 200:
                        doc = APIDocumentation(
                            api_name=api_name,
                            topic=topic,
                            docs_url=docs_url,
                            overview=api_docs_extractor.extract_overview(base_content),
                            parameters=[],
                            examples=api_docs_extractor.extract_examples(base_content),
                            related_links=api_docs_extractor.extract_links(base_content, docs_url),
                            notes=[
                                f"Note: Could not find specific docs for '{topic}'. Showing general documentation."
                            ],
                            source_urls=[docs_url],
                        )
                        result = api_docs_extractor.format_documentation(doc)
                        result = clamp_text(result, MAX_RESPONSE_CHARS)
                        success = True
                except Exception:  # noqa: BLE001
                    pass

            if not doc_results and not success:
                result = (
                    f"Found documentation site: {docs_url}\n"
                    f"But no results for topic: '{topic}'\n\n"
                    f"Try:\n"
                    f"- Broader search terms\n"
                    f"- Different wording (e.g., 'customers' instead of 'create customer')\n"
                    f"- Browse the docs directly: {docs_url}"
                )
                error_msg = "No results for topic"
                success = False
            elif doc_results:
                # Crawl the top results
                source_urls = []
                all_content = []

                for doc_result in doc_results[:max_results]:
                    try:
                        content = await crawler_client.fetch(doc_result.url, max_chars=12000)
                        all_content.append(content)
                        source_urls.append(doc_result.url)
                    except Exception:  # noqa: BLE001
                        pass

                if not all_content:
                    result = (
                        f"Failed to fetch documentation pages. Try browsing directly: {docs_url}"
                    )
                    error_msg = "Failed to crawl docs"
                    success = False
                else:
                    combined_content = "\n\n".join(all_content)

                    overview = api_docs_extractor.extract_overview(combined_content)
                    parameters = api_docs_extractor.extract_parameters(combined_content)
                    examples = api_docs_extractor.extract_examples(combined_content)
                    notes = api_docs_extractor.extract_notes(combined_content)
                    related_links = api_docs_extractor.extract_links(combined_content, docs_url)

                    doc = APIDocumentation(
                        api_name=api_name,
                        topic=topic,
                        docs_url=docs_url,
                        overview=overview,
                        parameters=parameters,
                        examples=examples,
                        related_links=related_links,
                        notes=notes,
                        source_urls=source_urls,
                    )

                    result = api_docs_extractor.format_documentation(doc)
                    result = clamp_text(result, MAX_RESPONSE_CHARS)
                    success = True

        # Cache successful results
        if success and result:
            await api_docs_cache.set(cache_key, result)

    except Exception as exc:  # noqa: BLE001
        error_msg = str(exc)
        result = f"Failed to fetch API documentation: {exc}\n\nTry using web_search or crawl_url directly."
    finally:
        response_time = (time.time() - start_time) * 1000
        tracker.track_usage(
            tool_name="api_docs",
            reasoning=reasoning,
            parameters={
                "api_name": api_name,
                "topic": topic,
                "docs_url": docs_url or "not_found",
                "max_results": max_results,
            },
            response_time_ms=response_time,
            success=success,
            error_message=error_msg,
            response_size=len(result.encode("utf-8")),
        )

    return result


@mcp.tool()
async def extract_data(
    url: Annotated[str, "HTTP(S) URL to extract structured data from"],
    reasoning: Annotated[str, "Why you're extracting data from this URL (required for analytics)"],
    extract_type: Annotated[
        Literal["table", "list", "fields", "json-ld", "auto"],
        'Extraction type: "table", "list", "fields", "json-ld", or "auto"',
    ] = "auto",
    selectors: Annotated[
        dict[str, str] | None,
        "CSS selectors for field extraction (only used with extract_type='fields')",
    ] = None,
    max_items: Annotated[int, "Maximum number of items to extract"] = 100,
) -> str:
    """
    Extract structured data from web pages.

    Extracts tables, lists, or specific fields from HTML pages and returns
    structured data. Much more efficient than parsing full page text.

    Extract Types:
    - "table": Extract HTML tables as list of dicts
    - "list": Extract lists (ul/ol/dl) as structured list
    - "fields": Extract specific elements using CSS selectors
    - "json-ld": Extract JSON-LD structured data
    - "auto": Automatically detect and extract structured content

    Examples:
    - extract_data("https://pypi.org/project/fastapi/", reasoning="Get package info")
    - extract_data("https://github.com/user/repo/releases", reasoning="Get releases", extract_type="list")
    - extract_data(
        "https://example.com/product",
        reasoning="Extract product details",
        extract_type="fields",
        selectors={"price": ".price", "title": "h1.product-name"}
      )
    """
    import json

    start_time = time.time()
    success = False
    error_msg = None
    result = ""

    try:
        # Fetch raw HTML — use generous limit since extraction needs the full page;
        # the final JSON output is clamped by MAX_RESPONSE_CHARS anyway.
        html = await crawler_client.fetch_raw(url, max_chars=2_000_000)

        # Extract based on type
        if extract_type == "table":
            tables = data_extractor.extract_tables(html, max_tables=max_items)
            extracted_data = {
                "type": "table",
                "tables": [
                    {
                        "caption": t.caption,
                        "headers": t.headers,
                        "rows": t.rows[:max_items],
                    }
                    for t in tables
                ],
                "source": url,
            }
        elif extract_type == "list":
            lists = data_extractor.extract_lists(html, max_lists=max_items)
            extracted_data = {
                "type": "list",
                "lists": [{"title": li.title, "items": li.items[:max_items]} for li in lists],
                "source": url,
            }
        elif extract_type == "fields":
            if not selectors:
                raise ValueError("selectors parameter is required for extract_type='fields'")
            fields = data_extractor.extract_fields(html, selectors)
            extracted_data = {"type": "fields", "data": fields, "source": url}
        elif extract_type == "json-ld":
            json_ld = data_extractor.extract_json_ld(html)
            extracted_data = {"type": "json-ld", "data": json_ld, "source": url}
        else:  # auto
            auto_data = data_extractor.auto_extract(html)
            extracted_data = {"type": "auto", "data": auto_data, "source": url}

        # Format result
        result = json.dumps(extracted_data, indent=2, ensure_ascii=False)
        result = clamp_text(result, MAX_RESPONSE_CHARS)
        success = True

    except Exception as exc:  # noqa: BLE001
        error_msg = str(exc)
        result = f"Data extraction failed for {url}: {exc}"

    finally:
        # Track usage
        response_time = (time.time() - start_time) * 1000
        import urllib.parse as _urlparse

        tracker.track_usage(
            tool_name="extract_data",
            reasoning=reasoning,
            parameters={
                "url": url,
                "extract_type": extract_type,
                "has_selectors": selectors is not None,
                "max_items": max_items,
                "domain": _urlparse.urlparse(url).netloc,
            },
            response_time_ms=response_time,
            success=success,
            error_message=error_msg,
            response_size=len(result.encode("utf-8")),
        )

    return result


@mcp.tool()
async def compare_tech(
    technologies: Annotated[list[str], "List of 2-5 technologies to compare"],
    reasoning: Annotated[str, "Why you're comparing these technologies (required for analytics)"],
    category: Annotated[
        Literal["framework", "library", "database", "language", "tool", "auto"],
        'Technology category (auto-detects if "auto")',
    ] = "auto",
    aspects: Annotated[
        list[str] | None,
        "Specific aspects to compare (auto-selected if not provided)",
    ] = None,
    max_results_per_tech: Annotated[int, "Maximum search results per technology"] = 3,
) -> str:
    """
    Compare multiple technologies, frameworks, or libraries side-by-side.

    Automatically gathers information about each technology and presents
    a structured comparison to help make informed decisions.

    Categories:
    - "framework": Web frameworks (React, Vue, Angular, etc.)
    - "library": JavaScript/Python/etc. libraries
    - "database": Databases (PostgreSQL, MongoDB, etc.)
    - "language": Programming languages (Python, Go, Rust, etc.)
    - "tool": Build tools, CLIs, etc. (Webpack, Vite, etc.)
    - "auto": Auto-detect category

    Examples:
    - compare_tech(["React", "Vue", "Svelte"], reasoning="Choose framework for new project")
    - compare_tech(["PostgreSQL", "MongoDB"], category="database", reasoning="Database for user data")
    - compare_tech(["FastAPI", "Flask"], aspects=["performance", "learning_curve"], reasoning="Python web framework")
    """
    import json

    start_time = time.time()
    success = False
    error_msg = None
    result = ""
    detected_category = category
    selected_aspects = aspects

    try:
        # Validate input
        if len(technologies) < 2:
            raise ValueError("Please provide at least 2 technologies to compare")
        if len(technologies) > 5:
            raise ValueError("Please provide at most 5 technologies to compare")

        # Detect category if auto
        if category == "auto":
            detected_category = detect_category(technologies)

        # Select aspects
        if not selected_aspects:
            selected_aspects = CATEGORY_ASPECTS.get(
                detected_category,
                ["performance", "features", "ecosystem", "popularity"],
            )

        # Gather info for each technology
        tech_infos = []
        for tech in technologies:
            info = await tech_comparator.gather_info(tech, detected_category, selected_aspects)
            tech_infos.append(info)

        # Build comparison
        comparison = tech_comparator.compare(tech_infos, selected_aspects)

        # Format result
        result = json.dumps(comparison, indent=2, ensure_ascii=False)
        result = clamp_text(result, MAX_RESPONSE_CHARS)
        success = True

    except Exception as exc:  # noqa: BLE001
        error_msg = str(exc)
        result = f"Technology comparison failed: {exc}"

    finally:
        # Track usage
        response_time = (time.time() - start_time) * 1000
        tracker.track_usage(
            tool_name="compare_tech",
            reasoning=reasoning,
            parameters={
                "technologies": technologies,
                "category": category,
                "detected_category": detected_category if category == "auto" else None,
                "num_aspects": len(selected_aspects) if selected_aspects else 0,
                "max_results_per_tech": max_results_per_tech,
            },
            response_time_ms=response_time,
            success=success,
            error_message=error_msg,
            response_size=len(result.encode("utf-8")),
        )

    return result


@mcp.tool()
async def get_changelog(
    package: Annotated[str, "Package name (e.g., react, fastapi)"],
    reasoning: Annotated[str, "Why you're checking the changelog"],
    registry: Annotated[Literal["npm", "pypi", "auto"], "Package registry"] = "auto",
    max_releases: Annotated[int, "Maximum releases to fetch"] = 5,
) -> str:
    """Get changelog and release notes for a package."""
    import json

    start_time = time.time()
    success = False
    error_msg = None
    result = ""
    detected_registry = registry

    try:
        # Auto-detect registry
        if registry == "auto":
            detected_registry = "npm"  # Default to npm

        # Fetch changelog
        changelog = await changelog_fetcher.get_changelog(package, detected_registry, max_releases)

        result = json.dumps(changelog, indent=2, ensure_ascii=False)
        result = clamp_text(result, MAX_RESPONSE_CHARS)
        success = "error" not in changelog
        if not success:
            error_msg = changelog.get("error")

    except Exception as exc:
        error_msg = str(exc)
        result = f"Changelog fetch failed for {package}: {exc}"

    finally:
        response_time = (time.time() - start_time) * 1000
        tracker.track_usage(
            tool_name="get_changelog",
            reasoning=reasoning,
            parameters={
                "package": package,
                "registry": detected_registry,
                "max_releases": max_releases,
            },
            response_time_ms=response_time,
            success=success,
            error_message=error_msg,
            response_size=len(result.encode("utf-8")),
        )

    return result


@mcp.tool()
async def check_service_status(
    service: Annotated[str, "Service name (e.g., stripe, aws, github, openai)"],
    reasoning: Annotated[str, "Why you're checking service status"],
) -> str:
    """Check if an API service or platform is experiencing issues."""
    import json

    start_time = time.time()
    success = False
    error_msg = None
    result = ""

    try:
        # Check service health
        status = await service_health_checker.check_service(service)

        result = json.dumps(status, indent=2, ensure_ascii=False)
        result = clamp_text(result, MAX_RESPONSE_CHARS)
        success = "error" not in status
        if not success:
            error_msg = status.get("error")

    except Exception as exc:
        error_msg = str(exc)
        result = f"Service health check failed for {service}: {exc}"

    finally:
        response_time = (time.time() - start_time) * 1000
        tracker.track_usage(
            tool_name="check_service_status",
            reasoning=reasoning,
            parameters={"service": service},
            response_time_ms=response_time,
            success=success,
            error_message=error_msg,
            response_size=len(result.encode("utf-8")),
        )

    return result


# =============================================================================
# RESOURCES - Read-only data lookups
# =============================================================================


@mcp.resource("package://{registry}/{name}")
async def get_package_resource(registry: str, name: str) -> str:
    """
    Get package information from a registry.

    URI format: package://{registry}/{name}
    Examples:
    - package://npm/express
    - package://pypi/fastapi
    - package://crates/serde
    - package://go/github.com/gin-gonic/gin
    """
    if registry not in ("npm", "pypi", "crates", "go"):
        return f"Unknown registry: {registry}. Supported: npm, pypi, crates, go"

    try:
        if registry == "npm":
            info = await registry_client.search_npm(name)
        elif registry == "pypi":
            info = await registry_client.search_pypi(name)
        elif registry == "crates":
            info = await registry_client.search_crates(name)
        else:  # go
            info = await registry_client.search_go(name)

        return _format_package_info(info)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return f"Package '{name}' not found on {registry}."
        return f"Failed to fetch {registry} package '{name}': HTTP {exc.response.status_code}"
    except Exception as exc:  # noqa: BLE001
        return f"Failed to fetch {registry} package '{name}': {exc}"


@mcp.resource("github://{owner}/{repo}")
async def get_github_resource(owner: str, repo: str) -> str:
    """
    Get GitHub repository information.

    URI format: github://{owner}/{repo}
    Examples:
    - github://microsoft/vscode
    - github://facebook/react
    - github://anthropics/anthropic-sdk-python
    """
    try:
        repo_info = await github_client.get_repo_info(owner, repo)
        commits = None
        try:
            commits = await github_client.get_recent_commits(owner, repo, count=3)
        except Exception:  # noqa: BLE001, S110
            pass
        return _format_repo_info(repo_info, commits)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return f"Repository '{owner}/{repo}' not found."
        elif exc.response.status_code == 403:
            return f"Access denied to '{owner}/{repo}'. May be private or rate limited."
        return f"Failed to fetch '{owner}/{repo}': HTTP {exc.response.status_code}"
    except Exception as exc:  # noqa: BLE001
        return f"Failed to fetch '{owner}/{repo}': {exc}"


@mcp.resource("status://{service}")
async def get_service_status_resource(service: str) -> str:
    """
    Get service health status.

    URI format: status://{service}
    Examples:
    - status://anthropic
    - status://openai
    - status://github
    - status://stripe
    """
    import json

    try:
        status = await service_health_checker.check_service(service)
        return json.dumps(status, indent=2, ensure_ascii=False)
    except Exception as exc:  # noqa: BLE001
        return f"Failed to check status for '{service}': {exc}"


@mcp.resource("changelog://{registry}/{package}")
async def get_changelog_resource(registry: str, package: str) -> str:
    """
    Get package changelog and release notes.

    URI format: changelog://{registry}/{package}
    Examples:
    - changelog://npm/react
    - changelog://pypi/fastapi
    """
    import json

    if registry not in ("npm", "pypi"):
        return f"Unknown registry: {registry}. Supported: npm, pypi"

    try:
        changelog = await changelog_fetcher.get_changelog(package, registry, max_releases=5)
        return json.dumps(changelog, indent=2, ensure_ascii=False)
    except Exception as exc:  # noqa: BLE001
        return f"Failed to fetch changelog for '{package}': {exc}"


@mcp.resource("domain-health://report")
async def get_domain_health_resource() -> str:
    """Per-domain fetch success/failure rates, block rates, and stealth escalation stats."""
    return domain_tracker.format_report()


# =============================================================================
# PROMPTS - Reusable message templates for common research tasks
# =============================================================================


@mcp.prompt()
def research_package(
    package: str,
    registry: str = "npm",
) -> str:
    """
    Generate a prompt for comprehensive package research.

    Use this when you want to thoroughly evaluate a package before adding it to your project.
    """
    return f"""Please research the "{package}" package from {registry} and provide:

1. **Overview**: What does this package do? What problem does it solve?
2. **Popularity & Trust**: Download stats, GitHub stars, maintenance activity
3. **Security**: Any known vulnerabilities or security concerns?
4. **Dependencies**: How many dependencies does it have? Any concerns?
5. **Alternatives**: What are the main alternatives and how does this compare?
6. **Recommendation**: Should I use this package? Why or why not?

Use the package://{registry}/{package} resource to get the package information, then search for additional context about alternatives and community sentiment."""


@mcp.prompt()
def debug_error(
    error_message: str,
    language: str = "",
    framework: str = "",
) -> str:
    """
    Generate a prompt for debugging an error message.

    Use this when you encounter an error and want help understanding and fixing it.
    """
    context_parts = []
    if language:
        context_parts.append(f"Language: {language}")
    if framework:
        context_parts.append(f"Framework: {framework}")
    context = "\n".join(context_parts) if context_parts else "Not specified"

    return f"""I encountered this error and need help debugging it:

```
{error_message}
```

**Context:**
{context}

Please help me:
1. **Understand**: What does this error mean in plain terms?
2. **Root Cause**: What typically causes this error?
3. **Fix**: How can I resolve this issue? Provide code examples if applicable.
4. **Prevention**: How can I prevent this error in the future?

Use the translate_error tool to find relevant Stack Overflow discussions and solutions."""


@mcp.prompt()
def compare_technologies(
    tech1: str,
    tech2: str,
    use_case: str = "general use",
) -> str:
    """
    Generate a prompt for comparing two technologies.

    Use this when deciding between two frameworks, libraries, or tools.
    """
    return f"""Please compare **{tech1}** vs **{tech2}** for {use_case}.

Analyze the following aspects:

1. **Performance**: Speed, resource usage, scalability
2. **Developer Experience**: Learning curve, documentation, tooling
3. **Ecosystem**: Community size, available plugins/extensions, job market
4. **Maintenance**: Release frequency, backward compatibility, long-term viability
5. **Use Cases**: When to choose one over the other

Use the compare_tech tool to gather data, then provide a clear recommendation with reasoning.

**My use case**: {use_case}

Which one should I choose and why?"""


@mcp.prompt()
def evaluate_repository(
    owner: str,
    repo: str,
) -> str:
    """
    Generate a prompt for evaluating a GitHub repository.

    Use this when deciding whether to use or contribute to an open source project.
    """
    return f"""Please evaluate the GitHub repository **{owner}/{repo}** for potential use in my project.

Analyze:

1. **Health**: Is this project actively maintained? Check recent commits, issue response time, PR activity.
2. **Quality**: Code quality indicators, test coverage, documentation quality.
3. **Community**: Number of contributors, community engagement, responsiveness to issues.
4. **Stability**: Version history, breaking changes, deprecation policy.
5. **Security**: Any known vulnerabilities? Security policy in place?
6. **License**: Is the license compatible with my use case?

Use the github://{owner}/{repo} resource to get repository information.

Provide a clear recommendation: Should I use this project? What are the risks?"""


@mcp.prompt()
def check_service_health(
    services: str,
) -> str:
    """
    Generate a prompt for checking multiple service statuses.

    Use this when you suspect infrastructure issues or before a deployment.
    Provide comma-separated service names.
    """
    service_list = [s.strip() for s in services.split(",")]
    resource_calls = "\n".join([f"- status://{s}" for s in service_list])

    return f"""Please check the health status of the following services:

{resource_calls}

For each service, report:
1. **Status**: Operational, degraded, or experiencing issues?
2. **Active Incidents**: Any ongoing problems?
3. **Recent History**: Any recent outages or maintenance?

If any services are having issues, suggest:
- Workarounds or alternatives
- Expected resolution time (if available)
- Impact on my application"""


def main() -> None:
    """Entrypoint used by the console script."""

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    mcp.run("stdio")


if __name__ == "__main__":
    main()
