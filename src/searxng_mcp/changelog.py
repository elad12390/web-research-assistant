"""Package changelog and release notes retrieval."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Release:
    """Information about a package release."""

    version: str
    date: str | None = None
    notes: str | None = None
    breaking_changes: list[str] = field(default_factory=list)


class ChangelogParser:
    """Parse and analyze package changelogs."""

    BREAKING_KEYWORDS = [
        "breaking",
        "removed",
        "deprecated",
        "incompatible",
        "migration",
        "⚠",
        "🚨",
    ]

    def parse_release(self, release_data: dict) -> Release:
        """Parse GitHub release data."""
        body = release_data.get("body", "")
        release = Release(
            version=release_data.get("tag_name", "unknown"),
            date=release_data.get("published_at"),
            notes=body[:500] if body else None,
        )

        # Extract breaking changes
        lines = body.split("\n") if body else []
        for line in lines:
            if any(kw in line.lower() for kw in self.BREAKING_KEYWORDS):
                clean = re.sub(r"^[-*•]\s*", "", line).strip()
                if clean:
                    release.breaking_changes.append(clean[:200])

        return release


class ChangelogFetcher:
    """Fetch changelogs from GitHub."""

    def __init__(self, github_client, registry_client):
        """Initialize with clients."""
        self.github = github_client
        self.registry = registry_client
        self.parser = ChangelogParser()

    async def get_changelog(self, package: str, registry: str, max_releases: int = 5) -> dict:
        """Get changelog for a package."""
        # Find repository
        repo_url = await self._find_repository(package, registry)
        if not repo_url:
            return {"error": "Could not find repository", "package": package}

        # Extract owner/repo
        owner, repo = self._parse_repo_url(repo_url)
        if not owner or not repo:
            return {"error": "Invalid repository URL", "package": package}

        # Fetch releases
        try:
            releases_data = await self.github.get_releases(owner, repo, max_releases)
            releases = [self.parser.parse_release(r) for r in releases_data]

            breaking_count = sum(len(r.breaking_changes) for r in releases)

            return {
                "package": package,
                "registry": registry,
                "repository": repo_url,
                "releases": [
                    {
                        "version": r.version,
                        "date": r.date,
                        "notes": r.notes,
                        "breaking_changes": r.breaking_changes,
                    }
                    for r in releases
                ],
                "summary": {
                    "total_releases": len(releases),
                    "breaking_changes_count": breaking_count,
                    "recommendation": "Safe to upgrade"
                    if breaking_count == 0
                    else f"{breaking_count} breaking change(s) - review carefully",
                },
            }
        except Exception as e:
            return {"error": f"Failed to fetch releases: {e}", "package": package}

    async def _find_repository(self, package: str, registry: str) -> str | None:
        """Find GitHub repository URL."""
        try:
            if registry == "npm":
                info = await self.registry.search_npm(package)
            elif registry == "pypi":
                info = await self.registry.search_pypi(package)
            else:
                return None
            return info.repository if info else None
        except Exception:
            return None

    def _parse_repo_url(self, url: str) -> tuple[str | None, str | None]:
        """Parse owner/repo from GitHub URL."""
        match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
        if match:
            return match.group(1), match.group(2).replace(".git", "")
        return None, None
