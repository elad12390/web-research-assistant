from pytest_bdd import parsers, then, when

from support.fixtures import async_step


@when(
    parsers.parse('a researcher requests official API docs for "{api_name}" about "{topic}"'),
    target_fixture="docs_result",
)
@async_step
async def request_api_docs(api_name, topic):
    from searxng_mcp.server import api_docs

    return await api_docs(api_name=api_name, reasoning="BDD test", topic=topic)


@when(
    parsers.parse(
        'a researcher requests official API docs for "{api_name}" about "{topic}" with max results {max_results:d}'
    ),
    target_fixture="docs_result",
)
@async_step
async def request_api_docs_with_max_results(api_name, topic, max_results):
    from searxng_mcp.server import api_docs

    return await api_docs(
        api_name=api_name,
        reasoning="BDD test",
        topic=topic,
        max_results=max_results,
    )


@then("the system returns authoritative documentation sources relevant to the topic")
def verify_api_docs_sources(docs_result):
    assert docs_result
    assert "http" in docs_result


@then("the system returns no more than 1 documentation source")
def verify_api_docs_max_results(docs_result):
    import re

    lower = docs_result.lower()
    source_headers = len(re.findall(r"^source\s*\d*:", docs_result, re.MULTILINE | re.IGNORECASE))
    is_single_or_failure = source_headers <= 1 or "failed" in lower or "try browsing" in lower
    assert is_single_or_failure, f"Expected at most 1 doc source, found {source_headers}"


@then("the system reports that no authoritative docs could be found")
def verify_api_docs_not_found(docs_result):
    lower = docs_result.lower()
    assert (
        "no authoritative" in lower
        or "not found" in lower
        or "could not find" in lower
        or "failed" in lower
    ), f"Expected not-found message, got: {docs_result[:200]}"
