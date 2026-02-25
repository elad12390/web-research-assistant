from pytest_bdd import parsers, then, when

from support.fixtures import async_step


@when(
    parsers.parse(
        'a researcher requests web search results for "{query}" in category "{category}"'
    ),
    target_fixture="web_search_result",
)
@async_step
async def request_web_search(query, category):
    from searxng_mcp.server import web_search

    return await web_search(query=query, reasoning="BDD test", category=category)


@then("the system returns a ranked list of snippets with source URLs")
def verify_ranked_snippets(web_search_result):
    assert web_search_result
    lower = web_search_result.lower()
    has_urls = "http" in lower
    is_no_results = "no results" in lower
    assert has_urls or is_no_results, (
        f"Expected URLs or 'no results' message, got: {web_search_result[:200]}"
    )


@then("the system returns results scoped to the requested category")
def verify_category_scoped(web_search_result):
    lower = web_search_result.lower()
    assert "category" in lower or "news" in lower or "general" in lower


@then("the system returns an empty or very small result set without failure")
def verify_small_results(web_search_result):
    lower = web_search_result.lower()
    assert "failed" not in lower and "error" not in lower


@when(
    parsers.parse(
        'a developer searches for examples of "{query}" with content type "{content_type}"'
    ),
    target_fixture="examples_result",
)
@async_step
async def search_examples_by_type(query, content_type):
    from searxng_mcp.server import search_examples

    return await search_examples(query=query, reasoning="BDD test", content_type=content_type)


@when(
    parsers.parse('a developer searches for examples of "{query}" with time range "{time_range}"'),
    target_fixture="examples_result",
)
@async_step
async def search_examples_by_time_range(query, time_range):
    from searxng_mcp.server import search_examples

    return await search_examples(query=query, reasoning="BDD test", time_range=time_range)


@when(
    parsers.parse(
        'a developer searches for examples of "{query}" with max results {max_results:d}'
    ),
    target_fixture="examples_result",
)
@async_step
async def search_examples_with_max_results(query, max_results):
    from searxng_mcp.server import search_examples

    return await search_examples(query=query, reasoning="BDD test", max_results=max_results)


@then("the system returns matching resources with URLs and short descriptions")
def verify_example_resources(examples_result):
    assert examples_result
    assert "http" in examples_result


@then("the system returns resources from the requested time window when available")
def verify_examples_time_window(examples_result):
    lower = examples_result.lower()
    assert "year" in lower or "time_range" in lower


@then("the system returns no more than 3 resources")
def verify_examples_max_results(examples_result):
    assert examples_result.lower().count("http") <= 3


@when(
    parsers.parse(
        'a designer searches for images of "{query}" with type "{image_type}" and orientation "{orientation}"'
    ),
    target_fixture="images_result",
)
@async_step
async def search_images_by_type_orientation(query, image_type, orientation):
    from searxng_mcp.server import search_images

    return await search_images(
        query=query,
        reasoning="BDD test",
        image_type=image_type,
        orientation=orientation,
    )


@when(
    parsers.parse('a designer searches for images of "{query}" with type "{image_type}"'),
    target_fixture="images_result",
)
@async_step
async def search_images_by_type(query, image_type):
    from searxng_mcp.server import search_images

    return await search_images(query=query, reasoning="BDD test", image_type=image_type)


@when(
    parsers.parse('a designer searches for images of "{query}" with max results {max_results:d}'),
    target_fixture="images_result",
)
@async_step
async def search_images_with_max_results(query, max_results):
    from searxng_mcp.server import search_images

    return await search_images(query=query, reasoning="BDD test", max_results=max_results)


@then("the system returns image results with URLs and attribution")
def verify_image_results(images_result):
    assert images_result
    assert "http" in images_result


@then("the system returns zero or more images without error")
def verify_images_no_error(images_result):
    lower = images_result.lower()
    assert "failed" not in lower and "error" not in lower


@then("the system returns no more than 5 images")
def verify_images_max_results(images_result):
    import re

    body = images_result.split("─" * 70)[1] if "─" * 70 in images_result else images_result
    if "─" * 70 in body:
        body = body.split("─" * 70)[0]
    entries = re.findall(r"^\d+\.\s", body, re.MULTILINE)
    assert len(entries) <= 5, f"Expected at most 5 image entries, found {len(entries)}"
