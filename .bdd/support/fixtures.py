"""async_step decorator for pytest-bdd — bridges async functions to sync step execution.

pytest-bdd does not support async step definitions natively (issue #223, open since 2017).
This decorator wraps async steps so they run via asyncio.run().
"""

from __future__ import annotations

import asyncio
import functools


def async_step(step_func):
    """Wrap an async step function so pytest-bdd can execute it synchronously.

    Usage::

        @when('I fetch the page', target_fixture="page_content")
        @async_step
        async def fetch_page(crawler, url):
            return await crawler.fetch(url)
    """

    @functools.wraps(step_func)
    def wrapper(*args, **kwargs):
        return asyncio.run(step_func(*args, **kwargs))

    return wrapper
