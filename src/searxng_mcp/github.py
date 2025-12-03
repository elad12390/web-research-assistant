from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

from .config import HTTP_TIMEOUT, USER_AGENT, _env_str


@dataclass(slots=True)
class RepoInfo:
    """GitHub repository metadata."""

    name: str
    full_name: str
    description: str
    stars: int
    forks: int
    watchers: int
    license: str | None
    language: str | None
    last_updated: str
    open_issues: int
    open_prs: int | None
    homepage: str | None
    topics: list[str]
    archived: bool
    size_kb: int


@dataclass(slots=True)
class Commit:
    """Recent commit info."""

    sha: str
    message: str
    author: str
    date: str
    url: str


class GitHubClient:
    """Client for GitHub REST API with optional authentication."""

    def __init__(self, timeout: float = HTTP_TIMEOUT) -> None:
        self.timeout = timeout
        self.token = _env_str("GITHUB_TOKEN", "")

        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/vnd.github.v3+json",
        }

        if self.token:
            headers["Authorization"] = f"token {self.token}"

        self._headers = headers

    async def _resolve_repo_redirect(self, owner: str, repo: str) -> tuple[str, str]:
        """
        Resolve repository redirects (renamed/transferred repos).

        GitHub API returns 301 for renamed repos with the new location in the response.
        """
        url = f"https://api.github.com/repos/{owner}/{repo}"

        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers=self._headers,
            follow_redirects=True,  # Follow redirects
        ) as client:
            response = await client.get(url)

            # If we followed a redirect, extract new owner/repo from the response
            if response.status_code == 200:
                data = response.json()
                new_full_name = data.get("full_name", f"{owner}/{repo}")
                if "/" in new_full_name:
                    new_owner, new_repo = new_full_name.split("/", 1)
                    return new_owner, new_repo

            response.raise_for_status()

        return owner, repo

    async def get_repo_info(self, owner: str, repo: str) -> RepoInfo:
        """Fetch repository information from GitHub API."""

        # First resolve any redirects (renamed repos)
        resolved_owner, resolved_repo = await self._resolve_repo_redirect(owner, repo)

        url = f"https://api.github.com/repos/{resolved_owner}/{resolved_repo}"

        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers=self._headers,
            follow_redirects=True,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        # Get open PRs count (separate API call)
        open_prs = await self._get_open_prs_count(owner, repo)

        # Format last updated time
        updated_at = data.get("updated_at", "")
        last_updated = self._format_time_ago(updated_at) if updated_at else "unknown"

        return RepoInfo(
            name=data.get("name", ""),
            full_name=data.get("full_name", ""),
            description=data.get("description") or "No description available",
            stars=data.get("stargazers_count", 0),
            forks=data.get("forks_count", 0),
            watchers=data.get("watchers_count", 0),
            license=data.get("license", {}).get("name") if data.get("license") else None,
            language=data.get("language"),
            last_updated=last_updated,
            open_issues=data.get("open_issues_count", 0),
            open_prs=open_prs,
            homepage=data.get("homepage"),
            topics=data.get("topics", []),
            archived=data.get("archived", False),
            size_kb=data.get("size", 0),
        )

    async def get_recent_commits(self, owner: str, repo: str, count: int = 5) -> list[Commit]:
        """Fetch recent commits from repository."""

        url = f"https://api.github.com/repos/{owner}/{repo}/commits"
        params = {"per_page": count}

        async with httpx.AsyncClient(timeout=self.timeout, headers=self._headers) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        commits = []
        for commit_data in data[:count]:
            commit_info = commit_data.get("commit", {})
            author_info = commit_info.get("author", {})

            # Truncate long commit messages
            message = commit_info.get("message", "No message")
            if "\n" in message:
                message = message.split("\n")[0]  # First line only
            if len(message) > 80:
                message = message[:77] + "..."

            commits.append(
                Commit(
                    sha=commit_data.get("sha", "")[:8],  # Short SHA
                    message=message,
                    author=author_info.get("name", "Unknown"),
                    date=self._format_time_ago(author_info.get("date", "")),
                    url=commit_data.get("html_url", ""),
                )
            )

        return commits

    async def _get_open_prs_count(self, owner: str, repo: str) -> int | None:
        """Get count of open pull requests."""

        try:
            url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
            params = {"state": "open", "per_page": 1}

            async with httpx.AsyncClient(timeout=5.0, headers=self._headers) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    # GitHub includes total count in Link header, but easier to count from search
                    search_url = "https://api.github.com/search/issues"
                    search_params = {
                        "q": f"repo:{owner}/{repo} type:pr state:open",
                        "per_page": 1,
                    }
                    search_response = await client.get(search_url, params=search_params)
                    if search_response.status_code == 200:
                        return search_response.json().get("total_count", 0)
        except Exception:  # noqa: BLE001, S110
            pass
        return None

    @staticmethod
    def _format_time_ago(iso_time: str) -> str:
        """Convert ISO timestamp to 'X time ago' format."""

        if not iso_time:
            return "unknown"

        try:
            dt = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            diff = now - dt

            if diff.days < 1:
                hours = diff.seconds // 3600
                if hours < 1:
                    minutes = diff.seconds // 60
                    return f"{minutes}m ago" if minutes > 0 else "just now"
                return f"{hours}h ago"
            if diff.days < 30:
                return f"{diff.days}d ago"
            if diff.days < 365:
                months = diff.days // 30
                return f"{months}mo ago"
            years = diff.days // 365
            return f"{years}y ago"
        except Exception:  # noqa: BLE001, S110
            return iso_time

    @staticmethod
    def parse_repo_url(repo_input: str) -> tuple[str, str]:
        """Parse various GitHub repo input formats to (owner, repo).

        Supported formats:
        - owner/repo
        - https://github.com/owner/repo
        - https://github.com/owner/repo.git
        - https://github.com/owner/repo/tree/main
        - https://github.com/owner/repo/blob/main/file.py

        Invalid inputs that will raise ValueError:
        - Non-GitHub URLs (e.g., https://example.com)
        - GitHub search URLs (e.g., https://github.com/search?q=...)
        - GitHub user/org pages without repo (e.g., https://github.com/microsoft)
        """
        repo_input = repo_input.strip()

        # Handle full URLs
        if repo_input.startswith(("https://", "http://")):
            # Must be a github.com URL
            if "github.com" not in repo_input.lower():
                raise ValueError(
                    f"Not a GitHub URL: {repo_input}. "
                    f"Please provide a GitHub repository URL or use 'owner/repo' format."
                )

            # Reject GitHub search/explore/etc URLs
            invalid_patterns = [
                r"github\.com/search",
                r"github\.com/explore",
                r"github\.com/topics",
                r"github\.com/trending",
                r"github\.com/settings",
                r"github\.com/notifications",
                r"github\.com/new",
                r"github\.com/organizations",
                r"github\.com/marketplace",
            ]
            for pattern in invalid_patterns:
                if re.search(pattern, repo_input, re.IGNORECASE):
                    raise ValueError(
                        f"Invalid GitHub URL: {repo_input}. "
                        f"This appears to be a GitHub search/explore page, not a repository. "
                        f"Please provide a repository URL like 'https://github.com/owner/repo'."
                    )

            # Parse repository URL - must have owner/repo
            match = re.match(
                r"https?://(?:www\.)?github\.com/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)(?:\.git|/.*)?$",
                repo_input,
            )
            if match:
                owner, repo = match.group(1), match.group(2)
                # Validate owner and repo names
                if owner and repo and len(owner) > 0 and len(repo) > 0:
                    return owner, repo

            # Check if it's just a user/org page (no repo)
            user_match = re.match(
                r"https?://(?:www\.)?github\.com/([a-zA-Z0-9_.-]+)/?$",
                repo_input,
            )
            if user_match:
                raise ValueError(
                    f"Invalid GitHub URL: {repo_input}. "
                    f"This appears to be a user/organization page, not a repository. "
                    f"Please provide a repository URL like 'https://github.com/{user_match.group(1)}/repo-name'."
                )

            raise ValueError(
                f"Could not parse GitHub URL: {repo_input}. "
                f"Please use format 'https://github.com/owner/repo'."
            )

        # Handle owner/repo format
        if "/" in repo_input:
            parts = repo_input.split("/")
            if len(parts) >= 2:
                owner, repo = parts[0].strip(), parts[1].strip()
                # Validate: must be non-empty and contain only valid characters
                valid_pattern = r"^[a-zA-Z0-9_.-]+$"
                if (
                    owner
                    and repo
                    and re.match(valid_pattern, owner)
                    and re.match(valid_pattern, repo)
                ):
                    return owner, repo

        raise ValueError(
            f"Invalid repository format: {repo_input}. "
            f"Use 'owner/repo' format (e.g., 'microsoft/vscode') or a full GitHub URL."
        )

    async def get_releases(self, owner: str, repo: str, max_releases: int = 10) -> list[dict]:
        """Fetch releases for a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            max_releases: Maximum number of releases to fetch

        Returns:
            List of release dictionaries with version, date, and notes
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/releases"
        params = {"per_page": min(max_releases, 100)}

        async with httpx.AsyncClient(timeout=self.timeout, headers=self._headers) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
