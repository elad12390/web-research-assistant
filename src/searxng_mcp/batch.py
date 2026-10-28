"""Helpers for the batch tools: bounded parallel runs, a shared output budget, page windows,
and loop detection that points single-item callers at the batch tools."""

from __future__ import annotations

import asyncio
import time
from collections import deque
from collections.abc import Awaitable, Callable
from typing import TypeVar

from .config import TRUNCATION_SUFFIX

MAX_BATCH_URLS = 20
MAX_BATCH_QUERIES = 20
CRAWL_CONCURRENCY = 6
SEARCH_CONCURRENCY = 4

T = TypeVar("T")


def unique(items: list[str]) -> list[str]:
    """Strip each item and drop blanks and repeats, keeping first-seen order."""
    return list(dict.fromkeys(item.strip() for item in items if item.strip()))


async def run_bounded(
    jobs: list[Callable[[], Awaitable[T]]], *, concurrency: int, timeout: float
) -> list[T | BaseException | None]:
    """Run *jobs* at most *concurrency* at a time and return their outcomes in input order.

    Each outcome is the job's result, the exception it raised, or None when the job had not
    finished after *timeout* seconds (it is cancelled), so one slow item cannot sink the batch.
    """
    semaphore = asyncio.Semaphore(concurrency)

    async def run(job: Callable[[], Awaitable[T]]) -> T:
        async with semaphore:
            return await job()

    tasks = [asyncio.ensure_future(run(job)) for job in jobs]
    if not tasks:
        return []
    late: set[asyncio.Future[T]] = set()
    try:
        _, late = await asyncio.wait(tasks, timeout=timeout)
    finally:
        for task in tasks:
            task.cancel()
    if late:
        await asyncio.wait(late, timeout=5)

    outcomes: list[T | BaseException | None] = []
    for task in tasks:
        if task in late:
            outcomes.append(None)
        elif task.exception() is not None:
            outcomes.append(task.exception())
        else:
            outcomes.append(task.result())
    return outcomes


def split_budget(wants: list[int], budget: int) -> list[int]:
    """Share *budget* across items: wants below an even share are met in full, and what they
    leave over is split evenly among the larger ones."""
    shares = [0] * len(wants)
    remaining = max(0, budget)
    pending = sorted(range(len(wants)), key=lambda index: wants[index])
    while pending:
        even_share = remaining // len(pending)
        if wants[pending[0]] > even_share:
            for index in pending:
                shares[index] = even_share
            break
        index = pending.pop(0)
        shares[index] = wants[index]
        remaining -= wants[index]
    return shares


def page_body(content: str) -> tuple[str, bool]:
    """Return fetched page text without the crawler's truncation note, and whether it was cut."""
    if content.endswith(TRUNCATION_SUFFIX):
        return content[: -len(TRUNCATION_SUFFIX)], True
    return content, False


def page_window(content: str, start: int, size: int) -> tuple[str, int | None]:
    """Return *size* characters of the page from *start*, and the offset where it continues
    (None at the end of the page)."""
    body, cut = page_body(content)
    end = start + size
    return body[start:end], end if cut or len(body) > end else None


class RecentCalls:
    """Remembers recent single-item calls so an agent looping over items can be told to batch."""

    def __init__(self, window_seconds: float = 120.0) -> None:
        self._window = window_seconds
        self._calls: deque[tuple[float, str, str]] = deque(maxlen=500)

    def note(self, tool: str, target: str) -> int:
        """Record a call; return how many other targets *tool* was called with in the window."""
        now = time.monotonic()
        while self._calls and now - self._calls[0][0] > self._window:
            self._calls.popleft()
        others = {seen for _, name, seen in self._calls if name == tool and seen != target}
        self._calls.append((now, tool, target))
        return len(others)
