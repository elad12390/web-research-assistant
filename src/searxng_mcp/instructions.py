"""Sent as the MCP `instructions`, which clients such as OpenCode put in every agent's system prompt."""

from .batch import MAX_BATCH_QUERIES, MAX_BATCH_URLS

SERVER_INSTRUCTIONS = f"""Web research: search the web, read pages, and look up packages, repositories, API docs, changelogs, and errors.

Batch, don't loop. Never call web_search or crawl_url once per item (per query, URL, file, or candidate project), whether one by one, in parallel, or inside a code loop:
- Several pages to read (search hits, READMEs, raw.githubusercontent.com files, docs pages): call batch_crawl_urls ONCE with every URL in `urls` (up to {MAX_BATCH_URLS}). Pages are fetched in parallel and come back in request order; a page that fails does not stop the others.
- Several searches (different phrasings, one per candidate library or project): call batch_web_search ONCE with every query in `queries` (up to {MAX_BATCH_QUERIES}).
- In code, build the urls or queries array inside the loop, then make one batch call after it.
- Searching and then reading the hits is two calls: batch_web_search, then batch_crawl_urls with the URLs you picked.
batch_crawl_urls splits one output budget across its pages. When it cuts pages, its result ends with the exact batch_crawl_urls arguments that continue all of them: send those in one call instead of calling crawl_url with start_char per page.

Use web_search or crawl_url only for a single query or page. Use stealth_scrape only for a page a crawl reports as blocked."""
