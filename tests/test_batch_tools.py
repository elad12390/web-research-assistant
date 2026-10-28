from __future__ import annotations

import asyncio
import json
import re
import sys
import threading
import time
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from searxng_mcp import server
from searxng_mcp.batch import RecentCalls, page_window, run_bounded, split_budget
from searxng_mcp.config import TRUNCATION_SUFFIX
from searxng_mcp.search import SearxSearcher
from searxng_mcp.tracking import UsageTracker

SECTION = re.compile(r"^=== \[(\d+)/(\d+)\] (\S+) \| (.+?) ===$", re.MULTILINE)
SPAN = re.compile(r"chars ([\d,]+)-([\d,]+)")


def _html(paragraphs: list[str]) -> bytes:
    body = "".join(f"<p>{text}</p>" for text in paragraphs)
    return f"<html><head><title>t</title></head><body>{body}</body></html>".encode()


PAGES = {
    "/short": _html(["Short page about SQLite and BSON storage."]),
    "/long": _html([f"Long page paragraph {n:04d} about embedded databases." for n in range(900)]),
    "/long2": _html([f"Second long page paragraph {n:04d} on licenses." for n in range(900)]),
}


class _Site(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/slow":
            time.sleep(3)
            body = _html(["Slow page."])
        elif path == "/search":
            self._search()
            return
        elif path in PAGES:
            body = PAGES[path]
        else:
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _search(self) -> None:
        query = parse_qs(urlparse(self.path).query)["q"][0]
        if query == "boom":
            self.send_response(500)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        results = (
            []
            if query == "nothing"
            else [
                {
                    "title": f"{query} result {n}",
                    "url": f"https://example.com/{query.replace(' ', '-')}/{n}",
                    "content": f"Snippet {n} for {query}.",
                }
                for n in (1, 2)
            ]
        )
        body = json.dumps({"results": results}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


@pytest.fixture
def site() -> Iterator[str]:
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Site)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_port}"
    finally:
        httpd.shutdown()
        httpd.server_close()


@pytest.fixture(autouse=True)
def isolated_state(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MCP_USAGE_LOG", str(tmp_path / "usage.json"))
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    monkeypatch.setattr(server, "tracker", UsageTracker())
    monkeypatch.setattr(server, "recent_calls", RecentCalls())


def _sections(result: str) -> list[tuple[str, str, str]]:
    """(url, status, page text) per section, using the header's char span to cut the text."""
    matches = list(SECTION.finditer(result))
    sections = []
    for match in matches:
        status = match.group(4)
        body = result[match.end() + 1 :]
        span = SPAN.search(status)
        if span:
            start, end = (int(value.replace(",", "")) for value in span.groups())
            body = body[: end - start]
        sections.append((match.group(3), status, body))
    return sections


def _continuation(result: str) -> dict:
    line = result.rsplit("batch_crawl_urls ", 1)[1]
    return json.loads(line)


async def _full_page(url: str) -> str:
    fetched = await server.crawler_client.resilient_fetch(url, max_chars=200_001)
    return fetched.content


def test_split_budget_meets_small_wants_and_splits_the_rest_evenly() -> None:
    assert split_budget([100, 5000, 9000], 6000) == [100, 2950, 2950]
    assert split_budget([100, 200], 6000) == [100, 200]
    assert sum(split_budget([7000] * 7, 45000)) <= 45000
    assert split_budget([0, 0], 10) == [0, 0]


def test_page_window_continues_exactly_and_never_leaks_the_crawler_note() -> None:
    cut_page = "abcdefghij  " + TRUNCATION_SUFFIX

    assert page_window(cut_page, 0, 4) == ("abcd", 4)
    assert page_window(cut_page, 8, 10) == ("ij  ", 18)
    assert page_window("abcdefghij", 8, 4) == ("ij", None)
    assert page_window("abcdefghij", 20, 4) == ("", None)


def test_run_bounded_keeps_order_and_isolates_errors_and_late_jobs() -> None:
    async def value(item: int, delay: float) -> int:
        await asyncio.sleep(delay)
        if item == 2:
            raise RuntimeError("item 2 broke")
        return item * 10

    outcomes = asyncio.run(
        run_bounded(
            [lambda: value(1, 0.05), lambda: value(2, 0), lambda: value(3, 5), lambda: value(4, 0)],
            concurrency=2,
            timeout=0.5,
        )
    )

    assert outcomes[0] == 10
    assert isinstance(outcomes[1], RuntimeError)
    assert outcomes[2] is None
    assert outcomes[3] == 40


def test_batch_crawl_reads_every_page_in_order_and_isolates_failures(site: str) -> None:
    urls = [f"{site}/long", f"{site}/missing", f"{site}/short", f"{site}/long"]

    result = asyncio.run(server.batch_crawl_urls(urls=urls, max_chars=5000))

    assert result.startswith("Batch crawl: 3 URLs | 2 read, 1 failed")
    assert "1 duplicate or blank URL(s) skipped" in result
    sections = _sections(result)
    assert [url for url, _, _ in sections] == [f"{site}/long", f"{site}/missing", f"{site}/short"]
    assert sections[0][1] == "chars 0-5,000, continues at start_char=5000"
    assert sections[1][1] == "FAILED"
    assert "HTTP 404" in result
    assert sections[2][1].endswith("end of page")
    assert "Short page about SQLite and BSON storage." in sections[2][2]


def test_cut_pages_continue_in_one_call_exactly_where_they_stopped(site, monkeypatch) -> None:
    monkeypatch.setattr(server, "MAX_BATCH_RESPONSE_CHARS", 20000)
    urls = [f"{site}/long", f"{site}/short", f"{site}/long2"]

    # One event loop for the whole exchange, like the running server.
    async def read_in_two_calls():
        first = await server.batch_crawl_urls(urls=urls, max_chars=15000)
        second = await server.batch_crawl_urls(**_continuation(first))
        full = {url: await _full_page(url) for url in (f"{site}/long", f"{site}/long2")}
        return first, second, full

    first, second, full = asyncio.run(read_in_two_calls())

    assert len(first) <= 20000
    continuation = _continuation(first)
    assert continuation["urls"] == [f"{site}/long", f"{site}/long2"]
    assert second.startswith("Batch crawl: 2 URLs | 2 read, 0 failed")
    for url in continuation["urls"]:
        before = next(text for seen, _, text in _sections(first) if seen == url)
        after = next(text for seen, _, text in _sections(second) if seen == url)
        assert full[url].startswith(before + after)
        assert len(before) == continuation["start_chars"][url]


def test_slow_page_times_out_without_sinking_the_batch(site, monkeypatch) -> None:
    monkeypatch.setattr(server, "BATCH_TIMEOUT_SECONDS", 1.0)

    started = time.monotonic()
    result = asyncio.run(server.batch_crawl_urls(urls=[f"{site}/slow", f"{site}/short"]))

    assert time.monotonic() - started < 2.5
    sections = _sections(result)
    assert sections[0][1] == "TIMED OUT"
    assert sections[1][1].endswith("end of page")


def test_batch_web_search_answers_every_query_in_order(site, monkeypatch) -> None:
    monkeypatch.setattr(server, "SEARCH_PROVIDER", "searxng")
    monkeypatch.setattr(server, "searxng_searcher", SearxSearcher(base_url=f"{site}/search"))

    result = asyncio.run(
        server.batch_web_search(queries=["sqlite bson", "boom", "nothing", "sqlite bson"])
    )

    assert result.startswith("Batch web search: 3 queries | 2 answered, 1 failed")
    headers = re.findall(r"^=== \[\d+/3\] (.+) ===$", result, re.MULTILINE)
    assert headers == ["sqlite bson", "boom", "nothing"]
    assert "1. sqlite bson result 1 \u2014 https://example.com/sqlite-bson/1" in result
    assert "Search failed:" in result
    assert "No results in category 'general'." in result
    assert 'batch_crawl_urls {"urls": ["https://example.com/sqlite-bson/1"]}' in result


def test_looping_single_page_crawls_are_told_to_batch(site: str) -> None:
    async def crawl_one_by_one():
        return [
            await server.crawl_url(url=f"{site}/short?page={n}", max_chars=200) for n in range(3)
        ]

    results = asyncio.run(crawl_one_by_one())

    assert not results[0].startswith("[BATCH THIS")
    assert not results[1].startswith("[BATCH THIS")
    assert results[2].startswith("[BATCH THIS: 2 other crawl_url calls")
    assert "Short page about SQLite" in results[2]


def test_agents_learn_to_batch_from_the_mcp_session(site, tmp_path) -> None:
    async def agent_session():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "searxng_mcp.server"],
            env={"MCP_USAGE_LOG": str(tmp_path / "usage.json"), "NO_PROXY": "127.0.0.1"},
        )
        async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
            initialized = await session.initialize()
            tools = await session.list_tools()
            called = await session.call_tool(
                "batch_crawl_urls", {"urls": [f"{site}/short", f"{site}/missing"]}
            )
            return initialized, tools, called

    initialized, tools, called = asyncio.run(agent_session())

    assert "Batch, don't loop" in initialized.instructions
    assert "batch_crawl_urls ONCE" in initialized.instructions
    assert "batch_web_search ONCE" in initialized.instructions
    by_name = {tool.name: tool for tool in tools.tools}
    assert by_name["batch_crawl_urls"].inputSchema["properties"]["urls"]["maxItems"] == 20
    assert by_name["batch_web_search"].inputSchema["properties"]["queries"]["maxItems"] == 20
    assert "batch_crawl_urls" in by_name["crawl_url"].description
    assert "batch_web_search" in by_name["web_search"].description
    undescribed = [
        f"{tool.name}.{name}"
        for tool in tools.tools
        for name, schema in tool.inputSchema["properties"].items()
        if not schema.get("description")
    ]
    assert undescribed == []
    text = called.content[0].text
    assert text.startswith("Batch crawl: 2 URLs | 1 read, 1 failed")
    assert [url for url, _, _ in _sections(text)] == [f"{site}/short", f"{site}/missing"]
