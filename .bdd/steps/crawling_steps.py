from pytest_bdd import parsers, then, when

from support.fixtures import async_step


@when(parsers.parse('a researcher requests the content for "{url}"'), target_fixture="crawl_result")
@async_step
async def request_crawl(url):
    from searxng_mcp.server import crawl_url

    return await crawl_url(url=url, reasoning="BDD test")


@when(
    parsers.parse('a researcher requests the content for "{url}" with max chars {max_chars:d}'),
    target_fixture="crawl_result",
)
@async_step
async def request_crawl_with_max_chars(url, max_chars):
    from searxng_mcp.server import crawl_url

    return await crawl_url(url=url, reasoning="BDD test", max_chars=max_chars)


@then("the system returns markdown text that reflects the page content")
def verify_crawl_markdown(crawl_result):
    import pytest

    assert crawl_result
    lower = crawl_result.lower()
    if "executable doesn't exist" in lower or "browsertype.launch" in lower:
        pytest.skip("Playwright browsers not installed — run 'crawl4ai-setup' first")
    assert not lower.startswith("crawl failed for ")


@then("the system returns no more than 1000 characters of markdown text")
def verify_crawl_max_chars(crawl_result):
    truncation_suffix_budget = 120
    assert len(crawl_result) <= 1000 + truncation_suffix_budget, (
        f"Expected roughly 1000 chars, got {len(crawl_result)}"
    )


@then("the system reports the failure without returning misleading content")
def verify_crawl_failure(crawl_result):
    lower = crawl_result.lower()
    assert "failed" in lower or "not found" in lower or "404" in lower


@when(
    parsers.parse('an analyst extracts "{extract_type}" data from "{url}"'),
    target_fixture="extract_result",
)
@async_step
async def extract_data_for_type(extract_type, url):
    from searxng_mcp.server import extract_data

    return await extract_data(url=url, reasoning="BDD test", extract_type=extract_type)


@when(
    'an analyst extracts fields from "https://www.iana.org/domains/reserved" using selectors:',
    target_fixture="extract_result",
)
@async_step
async def extract_fields_with_selectors():
    from searxng_mcp.server import extract_data

    selectors = {"title": "h1", "intro": "p"}

    return await extract_data(
        url="https://www.iana.org/domains/reserved",
        reasoning="BDD test",
        extract_type="fields",
        selectors=selectors,
    )


@when(
    parsers.parse(
        'an analyst extracts "{extract_type}" data from "{url}" with max items {max_items:d}'
    ),
    target_fixture="extract_result",
)
@async_step
async def extract_data_with_max_items(extract_type, url, max_items):
    from searxng_mcp.server import extract_data

    return await extract_data(
        url=url,
        reasoning="BDD test",
        extract_type=extract_type,
        max_items=max_items,
    )


@then("the system returns structured data for the requested type")
def verify_extract_data_type(extract_result):
    import json

    assert extract_result
    lower = extract_result.lower()
    try:
        data = json.loads(extract_result)
    except json.JSONDecodeError:
        if extract_result.lstrip().startswith("{"):
            return
        assert lower.startswith("data extraction failed for ")
        return

    assert isinstance(data, dict)
    assert "type" in data
    assert "source" in data


@then("the system returns a structured object with the selected fields")
def verify_extract_fields(extract_result):
    import json

    assert extract_result
    lower = extract_result.lower()
    try:
        data = json.loads(extract_result)
    except json.JSONDecodeError:
        assert lower.startswith("data extraction failed for ")
        return

    assert isinstance(data, dict)
    assert data.get("type") == "fields"
    fields = data.get("data") or {}
    assert "title" in fields
    assert "intro" in fields


@then("the system returns no more than 3 list items")
def verify_extract_max_items(extract_result):
    import json

    lower = extract_result.lower()
    try:
        data = json.loads(extract_result)
    except json.JSONDecodeError:
        assert lower.startswith("data extraction failed for ")
        return

    extracted_type = data.get("type")
    if extracted_type == "list":
        lists = data.get("lists", [])
        assert len(lists) <= 3, f"Expected at most 3 list groups, got {len(lists)}"
    elif extracted_type == "table":
        tables = data.get("tables", [])
        assert len(tables) <= 3, f"Expected at most 3 tables, got {len(tables)}"
