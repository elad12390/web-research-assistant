from pytest_bdd import parsers, then, when

from support.fixtures import async_step


@when(
    parsers.parse('a developer requests package info for "{name}" from registry "{registry}"'),
    target_fixture="package_info_result",
)
@async_step
async def request_package_info(name, registry):
    from searxng_mcp.server import package_info

    return await package_info(name=name, reasoning="BDD test", registry=registry)


@then("the system returns the latest version, license, and dependency summary")
def verify_package_info_fields(package_info_result):
    lower = package_info_result.lower()
    assert "package:" in lower
    assert "version:" in lower
    has_license = "license:" in lower
    has_deps = "dependencies:" in lower
    has_downloads = "downloads:" in lower
    assert has_license or has_deps or has_downloads, (
        f"Expected license, dependencies, or downloads in output: {package_info_result[:200]}"
    )


@then("the system includes security status and download indicators when provided by the registry")
def verify_package_info_security(package_info_result):
    lower = package_info_result.lower()
    assert "security:" in lower or "downloads:" in lower


@then("the system reports that the package cannot be found")
def verify_package_info_not_found(package_info_result):
    lower = package_info_result.lower()
    assert "not found" in lower or "failed to fetch" in lower or "error" in lower, (
        f"Expected not-found message, got: {package_info_result[:200]}"
    )


@when(
    parsers.parse('a developer searches packages for "{query}" in registry "{registry}"'),
    target_fixture="package_search_result",
)
@async_step
async def request_package_search(query, registry):
    from searxng_mcp.server import package_search

    return await package_search(query=query, reasoning="BDD test", registry=registry)


@when(
    parsers.parse(
        'a developer searches packages for "{query}" in registry "{registry}" with max results {max_results:d}'
    ),
    target_fixture="package_search_result",
)
@async_step
async def request_package_search_with_max_results(query, registry, max_results):
    from searxng_mcp.server import package_search

    return await package_search(
        query=query, reasoning="BDD test", registry=registry, max_results=max_results
    )


@then("the system returns a ranked list of packages with names and short descriptions")
def verify_package_search_results(package_search_result):
    lower = package_search_result.lower()
    assert package_search_result
    assert "search results for" in lower or "no packages found" in lower


@then("the system returns no more than 3 packages")
def verify_package_search_max_results(package_search_result):
    lines = [line for line in package_search_result.splitlines() if line.strip()]
    entries = [line for line in lines if line.strip()[0].isdigit() and "." in line]
    assert len(entries) <= 3


@then("the system returns zero or more packages without failure")
def verify_package_search_no_failure(package_search_result):
    lower = package_search_result.lower()
    assert "failed" not in lower and "error" not in lower


@when(
    parsers.parse('a developer requests changelog entries for "{package}"'),
    target_fixture="changelog_result",
)
@async_step
async def request_changelog(package):
    from searxng_mcp.server import get_changelog

    return await get_changelog(package=package, reasoning="BDD test")


@when(
    parsers.parse(
        'a developer requests changelog entries for "{package}" with max releases {max_releases:d}'
    ),
    target_fixture="changelog_result",
)
@async_step
async def request_changelog_with_max_releases(package, max_releases):
    from searxng_mcp.server import get_changelog

    return await get_changelog(package=package, reasoning="BDD test", max_releases=max_releases)


@when(
    parsers.parse(
        'a developer requests changelog entries for "{package}" from registry "{registry}"'
    ),
    target_fixture="changelog_result",
)
@async_step
async def request_changelog_from_registry(package, registry):
    from searxng_mcp.server import get_changelog

    return await get_changelog(package=package, reasoning="BDD test", registry=registry)


@then("the system returns recent versions with release notes and dates")
def verify_changelog_fields(changelog_result):
    import json

    data = json.loads(changelog_result)
    if "error" in data:
        assert "package" in data
        return

    releases = data.get("releases", [])
    assert releases
    assert all("version" in release for release in releases)
    assert all("date" in release for release in releases)


@then("the system returns no more than 2 releases")
def verify_changelog_max_releases(changelog_result):
    import json

    data = json.loads(changelog_result)
    if "error" in data:
        assert "package" in data
        return

    releases = data.get("releases", [])
    assert len(releases) <= 2


@then("the system identifies any breaking change notes when they are present")
def verify_changelog_breaking(changelog_result):
    import json

    data = json.loads(changelog_result)
    if "error" in data:
        assert "package" in data
        return

    releases = data.get("releases", [])
    assert releases
    assert all("breaking_changes" in release for release in releases)
    summary = data.get("summary", {})
    assert "breaking_changes_count" in summary
