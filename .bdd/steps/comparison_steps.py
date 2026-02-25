from pytest_bdd import parsers, then, when

from support.fixtures import async_step


@when(
    parsers.parse(
        'a product engineer compares the technologies "{technologies}" in category "{category}"'
    ),
    target_fixture="comparison_result",
)
@async_step
async def compare_technologies_with_category(technologies, category):
    from searxng_mcp.server import compare_tech

    tech_list = [tech.strip() for tech in technologies.split(",") if tech.strip()]
    return await compare_tech(technologies=tech_list, reasoning="BDD test", category=category)


@when(
    parsers.parse(
        'a product engineer compares the technologies "{technologies}" with aspects "{aspects}"'
    ),
    target_fixture="comparison_result",
)
@async_step
async def compare_technologies_with_aspects(technologies, aspects):
    from searxng_mcp.server import compare_tech

    tech_list = [tech.strip() for tech in technologies.split(",") if tech.strip()]
    aspect_list = [aspect.strip() for aspect in aspects.split(",") if aspect.strip()]
    return await compare_tech(technologies=tech_list, reasoning="BDD test", aspects=aspect_list)


@when(
    parsers.parse('a product engineer compares the technologies "{technologies}"'),
    target_fixture="comparison_result",
)
@async_step
async def compare_technologies(technologies):
    from searxng_mcp.server import compare_tech

    tech_list = [tech.strip() for tech in technologies.split(",") if tech.strip()]
    return await compare_tech(technologies=tech_list, reasoning="BDD test")


@then("the system returns a structured comparison with popularity signals")
def verify_comparison_popularity(comparison_result):
    assert comparison_result
    assert "{" in comparison_result


@then("the system emphasizes the requested aspects in the comparison")
def verify_comparison_aspects(comparison_result):
    lower = comparison_result.lower()
    assert "performance" in lower or "learning_curve" in lower


@then("the system explains any missing data for unknown technologies")
def verify_comparison_missing_data(comparison_result):
    lower = comparison_result.lower()
    assert "missing" in lower or "unknown" in lower or "not found" in lower
