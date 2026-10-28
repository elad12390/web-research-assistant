from __future__ import annotations

import asyncio
import json
import stat
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace
from unittest.mock import AsyncMock

from searxng_mcp import crawler as crawler_module
from searxng_mcp.changelog import ChangelogFetcher
from searxng_mcp.crawler import CrawlerClient, FetchMethod, FetchResult, FetchStatus
from searxng_mcp.github import GitHubClient
from searxng_mcp.server import _page_content, mcp
from searxng_mcp.tracking import UsageTracker


def test_reasoning_is_optional_for_every_tool() -> None:
    tools = asyncio.run(mcp.list_tools())

    for tool in tools:
        assert "reasoning" not in tool.inputSchema.get("required", []), tool.name


def test_long_crawl_content_can_be_continued_by_offset() -> None:
    content = "abcdefghij"

    assert _page_content(content, 0, 4).endswith("start_char=4.]")
    assert _page_content(content, 4, 4).startswith("efgh")
    assert _page_content(content, 8, 4) == "ij"
    assert _page_content(content, 20, 4) == (
        "No content at start_char=20; the page is shorter than that offset."
    )


def test_invalid_github_token_retries_anonymously(monkeypatch) -> None:
    requests: list[str | None] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            authorization = self.headers.get("Authorization")
            requests.append(authorization)
            if authorization:
                self.send_response(401)
                payload = {"message": "Bad credentials"}
            else:
                self.send_response(200)
                payload = {"full_name": "owner/repo"}
            body = json.dumps(payload).encode()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        monkeypatch.setenv("GITHUB_TOKEN", "invalid-token")
        client = GitHubClient(api_base_url=f"http://127.0.0.1:{server.server_port}")
        assert asyncio.run(client._resolve_repo_redirect("owner", "repo")) == ("owner", "repo")
        assert asyncio.run(client._resolve_repo_redirect("owner", "repo")) == ("owner", "repo")
    finally:
        server.shutdown()
        thread.join()
        server.server_close()

    assert requests == ["token invalid-token", None, None]


def test_changelog_auto_registry_falls_back_from_npm_to_pypi() -> None:
    class Registry:
        async def search_npm(self, package: str):
            raise RuntimeError("not an npm package")

        async def search_pypi(self, package: str):
            return SimpleNamespace(repository="https://github.com/fastapi/fastapi")

    fetcher = ChangelogFetcher(github_client=object(), registry_client=Registry())

    assert asyncio.run(fetcher._find_repository("fastapi", "auto")) == (
        "https://github.com/fastapi/fastapi",
        "pypi",
    )


def test_missing_stealth_browser_preserves_normal_fetch_result(monkeypatch) -> None:
    client = CrawlerClient()
    blocked = FetchResult(
        content="",
        status=FetchStatus.BLOCKED,
        method=FetchMethod.NORMAL,
        domain="example.com",
        http_status=403,
    )
    browser_error = FetchResult(
        content="",
        status=FetchStatus.ERROR,
        method=FetchMethod.STEALTH,
        domain="example.com",
        error_message=(
            "BrowserType.launch: Executable doesn't exist at /cache/chromium. "
            "Please run playwright install."
        ),
    )
    monkeypatch.setattr(crawler_module, "PROXY_URL", "")
    monkeypatch.setattr(client, "_try_normal", AsyncMock(return_value=blocked))
    monkeypatch.setattr(client, "_try_stealth", AsyncMock(return_value=browser_error))

    result = asyncio.run(client.resilient_fetch("https://example.com"))

    assert result.status == FetchStatus.BLOCKED
    assert result.http_status == 403
    assert result.error_message == (
        "Stealth browser is unavailable. Run `uv run scrapling install` in the MCP environment."
    )


def test_usage_log_is_private(monkeypatch, tmp_path) -> None:
    log_file = tmp_path / "usage.json"
    monkeypatch.setenv("MCP_USAGE_LOG", str(log_file))

    UsageTracker()

    assert stat.S_IMODE(log_file.stat().st_mode) == 0o600
