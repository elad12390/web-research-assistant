from pytest_bdd import parsers, then, when

from support.fixtures import async_step


@when(
    parsers.parse('a developer requests repository information for "{repo}"'),
    target_fixture="repo_result",
)
@async_step
async def request_repo_info(repo):
    from searxng_mcp.server import github_repo

    return await github_repo(repo=repo, reasoning="BDD test", include_commits=False)


@when(
    parsers.parse('a developer requests repository information for "{repo}" with commits included'),
    target_fixture="repo_result",
)
@async_step
async def request_repo_info_with_commits(repo):
    from searxng_mcp.server import github_repo

    return await github_repo(repo=repo, reasoning="BDD test", include_commits=True)


@then("the system returns stars, forks, open issues, and license data")
def verify_repo_metrics(repo_result):
    assert "⭐" in repo_result
    assert "🍴" in repo_result
    assert "Open Issues:" in repo_result
    assert "License:" in repo_result


@then("the system includes recent commit activity in the response")
def verify_repo_commits(repo_result):
    assert "commit" in repo_result.lower()


@then("the system reports that the repository cannot be found")
def verify_repo_not_found(repo_result):
    lower = repo_result.lower()
    assert "not found" in lower or "failed" in lower
