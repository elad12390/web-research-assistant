from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

from .config import HTTP_TIMEOUT, USER_AGENT


@dataclass(slots=True)
class PackageInfo:
    """Structured package metadata from various registries."""

    name: str
    registry: str
    version: str
    description: str
    license: str | None
    downloads: str | None
    last_updated: str
    repository: str | None
    homepage: str | None
    dependencies_count: int | None
    security_issues: int


class PackageRegistryClient:
    """Client for querying npm, PyPI, crates.io, and Go package registries."""

    def __init__(self, timeout: float = HTTP_TIMEOUT) -> None:
        self.timeout = timeout
        self._headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}

    async def search_packages(
        self, query: str, registry: str, max_results: int = 5
    ) -> list[PackageInfo]:
        """Search for packages by description/keywords."""

        if registry == "npm":
            return await self._search_npm(query, max_results)
        elif registry == "pypi":
            return await self._search_pypi(query, max_results)
        elif registry == "crates":
            return await self._search_crates(query, max_results)
        else:  # go
            return await self._search_go(query, max_results)

    async def _search_npm(self, query: str, max_results: int) -> list[PackageInfo]:
        """Search npm packages."""

        url = "https://registry.npmjs.org/-/v1/search"
        params = {"text": query, "size": max_results}

        async with httpx.AsyncClient(timeout=self.timeout, headers=self._headers) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        packages = []
        for item in data.get("objects", []):
            package = item.get("package", {})
            name = package.get("name", "")

            # Get downloads for this package
            downloads = await self._get_npm_downloads(name)

            packages.append(
                PackageInfo(
                    name=name,
                    registry="npm",
                    version=package.get("version", "unknown"),
                    description=package.get("description", "No description"),
                    license=package.get("license", "Unknown"),
                    downloads=downloads,
                    last_updated=self._format_time_ago(package.get("date", "")),
                    repository=package.get("links", {}).get("repository"),
                    homepage=package.get("links", {}).get("homepage"),
                    dependencies_count=None,  # Not available in search results
                    security_issues=0,
                )
            )

        return packages

    async def _search_pypi(self, query: str, max_results: int) -> list[PackageInfo]:
        """Search PyPI packages using GitHub search as fallback."""

        try:
            # Use GitHub search API for Python packages as a proxy for PyPI
            url = "https://api.github.com/search/repositories"
            params = {
                "q": f"{query} language:python",
                "sort": "stars",
                "order": "desc",
                "per_page": max_results,
            }

            async with httpx.AsyncClient(timeout=self.timeout, headers=self._headers) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

            packages = []
            for repo in data.get("items", []):
                # Use the repo name as potential PyPI package name
                name = repo.get("name", "")

                # Many GitHub repos have the same name as their PyPI package
                packages.append(
                    PackageInfo(
                        name=name,
                        registry="PyPI",
                        version="unknown",
                        description=repo.get("description", "No description available"),
                        license="Unknown",
                        downloads=None,
                        last_updated=self._format_time_ago(repo.get("updated_at", "")),
                        repository=repo.get("html_url", ""),
                        homepage=f"https://pypi.org/project/{name}/",
                        dependencies_count=None,
                        security_issues=0,
                    )
                )

            return packages

        except Exception:  # noqa: BLE001, S110
            return []

    async def _search_crates(self, query: str, max_results: int) -> list[PackageInfo]:
        """Search crates.io packages."""

        url = "https://crates.io/api/v1/crates"
        params = {"q": query, "per_page": max_results}

        async with httpx.AsyncClient(timeout=self.timeout, headers=self._headers) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        packages = []
        for crate in data.get("crates", []):
            downloads = self._format_downloads(crate.get("downloads", 0))

            packages.append(
                PackageInfo(
                    name=crate.get("name", ""),
                    registry="crates.io",
                    version=crate.get("newest_version", "unknown"),
                    description=crate.get("description", "No description"),
                    license=crate.get("license", "Unknown"),
                    downloads=f"{downloads} total",
                    last_updated=self._format_time_ago(crate.get("updated_at", "")),
                    repository=crate.get("repository"),
                    homepage=crate.get("homepage"),
                    dependencies_count=None,
                    security_issues=0,
                )
            )

        return packages

    async def _search_go(self, query: str, max_results: int) -> list[PackageInfo]:
        """Search Go packages using GitHub search for Go repositories."""

        try:
            # Use GitHub search API for Go packages
            url = "https://api.github.com/search/repositories"
            params = {
                "q": f"{query} language:go",
                "sort": "stars",
                "order": "desc",
                "per_page": max_results,
            }

            async with httpx.AsyncClient(timeout=self.timeout, headers=self._headers) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

            packages = []
            for repo in data.get("items", []):
                full_name = repo.get("full_name", "")
                # Create Go module path (github.com/owner/repo format)
                go_module = f"github.com/{full_name}"

                packages.append(
                    PackageInfo(
                        name=go_module,
                        registry="Go",
                        version="unknown",
                        description=repo.get("description", "No description available"),
                        license="Unknown",
                        downloads=None,  # Go doesn't track downloads
                        last_updated=self._format_time_ago(repo.get("updated_at", "")),
                        repository=repo.get("html_url", ""),
                        homepage=f"https://pkg.go.dev/{go_module}",
                        dependencies_count=None,
                        security_issues=0,
                    )
                )

            return packages

        except Exception:  # noqa: BLE001, S110
            return []

    async def search_npm(self, name: str) -> PackageInfo:
        """Fetch package information from npm registry."""

        url = f"https://registry.npmjs.org/{name}"

        async with httpx.AsyncClient(timeout=self.timeout, headers=self._headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        latest_version = data.get("dist-tags", {}).get("latest", "unknown")
        version_data = data.get("versions", {}).get(latest_version, {})

        # Get weekly downloads from npm API
        downloads = await self._get_npm_downloads(name)

        # Parse last update time
        time_data = data.get("time", {})
        last_updated = time_data.get(latest_version) or time_data.get("modified", "unknown")
        if last_updated != "unknown":
            last_updated = self._format_time_ago(last_updated)

        repository = (
            version_data.get("repository", {}).get("url")
            if isinstance(version_data.get("repository"), dict)
            else version_data.get("repository")
        )
        if repository and repository.startswith("git+"):
            repository = repository[4:]

        dependencies = version_data.get("dependencies", {})

        return PackageInfo(
            name=name,
            registry="npm",
            version=latest_version,
            description=version_data.get("description", "No description available"),
            license=version_data.get("license", "Unknown"),
            downloads=downloads,
            last_updated=last_updated,
            repository=repository,
            homepage=version_data.get("homepage"),
            dependencies_count=len(dependencies) if dependencies else 0,
            security_issues=0,  # Would need separate npm audit API call
        )

    async def _get_npm_downloads(self, name: str) -> str | None:
        """Get weekly download count for npm package."""

        try:
            url = f"https://api.npmjs.org/downloads/point/last-week/{name}"
            async with httpx.AsyncClient(timeout=5.0, headers=self._headers) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    count = data.get("downloads", 0)
                    return self._format_downloads(count)
        except Exception:  # noqa: BLE001, S110
            pass
        return None

    async def search_pypi(self, name: str) -> PackageInfo:
        """Fetch package information from PyPI."""

        url = f"https://pypi.org/pypi/{name}/json"

        async with httpx.AsyncClient(timeout=self.timeout, headers=self._headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        info = data.get("info", {})
        latest_version = info.get("version", "unknown")

        # PyPI doesn't provide download stats in API anymore, show placeholder
        downloads = None

        # Get last release date
        releases = data.get("releases") or {}
        last_updated = "unknown"
        if (
            latest_version in releases
            and releases[latest_version]
            and len(releases[latest_version]) > 0
        ):
            first_release = releases[latest_version][0]
            if isinstance(first_release, dict):
                upload_time = first_release.get("upload_time", "")
                if upload_time:
                    last_updated = self._format_time_ago(upload_time)

        # Count dependencies from requires_dist
        requires_dist = info.get("requires_dist") or []
        dependencies_count = len([r for r in requires_dist if "extra ==" not in r])

        # Safely handle project_urls - it can be None
        project_urls = info.get("project_urls") or {}

        # Truncate long licenses for readability
        license_text = info.get("license", "Unknown")
        if isinstance(license_text, str) and len(license_text) > 100:
            license_text = license_text[:97] + "..."

        return PackageInfo(
            name=name,
            registry="PyPI",
            version=latest_version,
            description=info.get("summary", "No description available"),
            license=license_text,
            downloads=downloads,
            last_updated=last_updated,
            repository=project_urls.get("Source") or project_urls.get("Repository"),
            homepage=info.get("home_page") or project_urls.get("Homepage"),
            dependencies_count=dependencies_count,
            security_issues=0,
        )

    async def search_crates(self, name: str) -> PackageInfo:
        """Fetch package information from crates.io."""

        url = f"https://crates.io/api/v1/crates/{name}"

        async with httpx.AsyncClient(timeout=self.timeout, headers=self._headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        crate = data.get("crate", {})
        version = data.get("versions", [{}])[0]

        downloads = self._format_downloads(crate.get("downloads", 0))
        last_updated = version.get("created_at", "unknown")
        if last_updated != "unknown":
            last_updated = self._format_time_ago(last_updated)

        return PackageInfo(
            name=name,
            registry="crates.io",
            version=version.get("num", "unknown"),
            description=crate.get("description", "No description available"),
            license=version.get("license", "Unknown"),
            downloads=f"{downloads} total",
            last_updated=last_updated,
            repository=crate.get("repository"),
            homepage=crate.get("homepage"),
            dependencies_count=None,  # Would need to parse version dependencies
            security_issues=0,
        )

    async def search_go(self, module: str) -> PackageInfo:
        """Fetch package information from Go proxy."""

        # Get latest version
        latest_url = f"https://proxy.golang.org/{module}/@latest"

        async with httpx.AsyncClient(timeout=self.timeout, headers=self._headers) as client:
            response = await client.get(latest_url)
            response.raise_for_status()
            data = response.json()

        version = data.get("Version", "unknown")
        time_str = data.get("Time", "unknown")
        if time_str != "unknown":
            time_str = self._format_time_ago(time_str)

        # Try to get more info from pkg.go.dev API
        pkg_info = await self._get_go_pkg_info(module)

        return PackageInfo(
            name=module,
            registry="Go",
            version=version,
            description=pkg_info.get("synopsis", "No description available"),
            license=pkg_info.get("license", "Unknown"),
            downloads=None,  # Go doesn't track downloads
            last_updated=time_str,
            repository=f"https://{module}",
            homepage=f"https://pkg.go.dev/{module}",
            dependencies_count=None,
            security_issues=0,
        )

    async def _get_go_pkg_info(self, module: str) -> dict[str, Any]:
        """Get additional info from pkg.go.dev (best effort)."""

        try:
            url = f"https://api.pkg.go.dev/v1/module/{module}"
            async with httpx.AsyncClient(timeout=5.0, headers=self._headers) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    return response.json()
        except Exception:  # noqa: BLE001, S110
            pass
        return {}

    @staticmethod
    def _format_downloads(count: int) -> str:
        """Format download count in human-readable form."""

        if count >= 1_000_000:
            return f"{count / 1_000_000:.1f}M"
        if count >= 1_000:
            return f"{count / 1_000:.1f}K"
        return str(count)

    @staticmethod
    def _format_time_ago(iso_time: str) -> str:
        """Convert ISO timestamp to 'X days/months ago' format."""

        try:
            dt = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            diff = now - dt

            if diff.days < 1:
                hours = diff.seconds // 3600
                return f"{hours} hours ago" if hours > 0 else "just now"
            if diff.days < 30:
                return f"{diff.days} days ago"
            if diff.days < 365:
                months = diff.days // 30
                return f"{months} months ago"
            years = diff.days // 365
            return f"{years} years ago"
        except Exception:  # noqa: BLE001, S110
            return iso_time
