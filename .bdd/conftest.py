"""BDD conftest — all fixtures use REAL services, zero mocks."""

from __future__ import annotations

import sys
import os

import pytest
from pytest_bdd import given

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from searxng_mcp.search import SearxSearcher
from searxng_mcp.exa import ExaSearcher
from searxng_mcp.crawler import CrawlerClient
from searxng_mcp.registry import PackageRegistryClient
from searxng_mcp.github import GitHubClient
from searxng_mcp.images import PixabayClient
from searxng_mcp.errors import ErrorParser
from searxng_mcp.api_docs import APIDocsDetector, APIDocsExtractor
from searxng_mcp.extractor import DataExtractor
from searxng_mcp.comparison import TechComparator
from searxng_mcp.changelog import ChangelogFetcher
from searxng_mcp.service_health import ServiceHealthChecker
from searxng_mcp.config import SEARCH_PROVIDER, MAX_RESPONSE_CHARS

from support.fixtures import async_step  # noqa: F401 — re-export for step files


@pytest.fixture(scope="session")
def searcher() -> SearxSearcher:
    """Requires a running SearXNG instance on SEARXNG_BASE_URL."""
    return SearxSearcher()


@pytest.fixture(scope="session")
def exa_searcher() -> ExaSearcher:
    """Requires EXA_API_KEY env var."""
    return ExaSearcher()


@pytest.fixture(scope="session")
def crawler() -> CrawlerClient:
    return CrawlerClient()


@pytest.fixture(scope="session")
def extractor() -> DataExtractor:
    return DataExtractor()


@pytest.fixture(scope="session")
def registry_client() -> PackageRegistryClient:
    return PackageRegistryClient()


@pytest.fixture(scope="session")
def github_client() -> GitHubClient:
    return GitHubClient()


@pytest.fixture(scope="session")
def pixabay_client() -> PixabayClient:
    """Requires PIXABAY_API_KEY env var for full functionality."""
    return PixabayClient()


@pytest.fixture(scope="session")
def error_parser() -> ErrorParser:
    return ErrorParser()


@pytest.fixture(scope="session")
def api_docs_detector() -> APIDocsDetector:
    return APIDocsDetector()


@pytest.fixture(scope="session")
def api_docs_extractor() -> APIDocsExtractor:
    return APIDocsExtractor()


@pytest.fixture(scope="session")
def tech_comparator(searcher, github_client, registry_client) -> TechComparator:
    return TechComparator(searcher, github_client, registry_client)


@pytest.fixture(scope="session")
def changelog_fetcher(github_client, registry_client) -> ChangelogFetcher:
    return ChangelogFetcher(github_client, registry_client)


@pytest.fixture(scope="session")
def service_health_checker(crawler) -> ServiceHealthChecker:
    return ServiceHealthChecker(crawler)


@pytest.fixture(scope="session")
def search_provider() -> str:
    return SEARCH_PROVIDER


@pytest.fixture(scope="session")
def max_response_chars() -> int:
    return MAX_RESPONSE_CHARS


@pytest.fixture
def result_holder() -> dict:
    return {}


@given("a researcher has access to the web research assistant")
def researcher_has_access():
    pass


@given("a developer has access to the web research assistant")
def developer_has_access():
    pass


@given("a designer has access to the web research assistant")
def designer_has_access():
    pass


@given("an analyst has access to the web research assistant")
def analyst_has_access():
    pass


@given("a product engineer has access to the web research assistant")
def product_engineer_has_access():
    pass


@given("a reliability engineer has access to the web research assistant")
def reliability_engineer_has_access():
    pass
