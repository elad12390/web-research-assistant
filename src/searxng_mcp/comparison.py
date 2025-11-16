"""Technology comparison and analysis."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from typing import Any

from .config import clamp_text


@dataclass
class TechInfo:
    """Information about a technology."""

    name: str
    category: str
    performance: str | None = None
    learning_curve: str | None = None
    ecosystem: str | None = None
    popularity: str | None = None
    features: list[str] = field(default_factory=list)
    use_cases: str | None = None
    maintenance: str | None = None
    sources: list[str] = field(default_factory=list)


# Default aspects by category
CATEGORY_ASPECTS = {
    "framework": [
        "performance",
        "learning_curve",
        "ecosystem",
        "popularity",
        "features",
    ],
    "library": ["performance", "features", "ecosystem", "popularity"],
    "database": ["performance", "data_model", "scaling", "use_cases", "ecosystem"],
    "language": ["performance", "learning_curve", "ecosystem", "use_cases"],
    "tool": ["performance", "features", "ecosystem"],
}

DEFAULT_ASPECTS = ["performance", "features", "ecosystem", "popularity"]


class TechComparator:
    """Compare technologies based on gathered data."""

    def __init__(self, searcher, github_client, registry_client):
        """Initialize with existing clients.

        Args:
            searcher: SearxSearcher instance
            github_client: GitHubClient instance
            registry_client: PackageRegistryClient instance
        """
        self.searcher = searcher
        self.github_client = github_client
        self.registry_client = registry_client

    async def gather_info(self, technology: str, category: str, aspects: list[str]) -> TechInfo:
        """Gather information about a single technology.

        Uses multiple sources:
        - Web search for general info and comparisons
        - GitHub for popularity metrics (if applicable)
        - Package registries for ecosystem data (if applicable)

        Args:
            technology: Name of the technology (e.g., "React")
            category: Category (framework, database, etc.)
            aspects: List of aspects to gather (performance, ecosystem, etc.)

        Returns:
            TechInfo object with gathered data
        """
        info = TechInfo(name=technology, category=category)

        # Gather all data in parallel for speed
        tasks = []

        # Task 1: Overview search
        tasks.append(self._search_overview(info, technology, category))

        # Task 2: Search for all aspects in parallel
        for aspect in aspects:
            tasks.append(self._search_aspect(info, aspect, technology, category))

        # Task 3: GitHub metrics
        tasks.append(self._gather_github_metrics(info))

        # Task 4: Package metrics
        tasks.append(self._gather_package_metrics(info))

        # Run all in parallel
        await asyncio.gather(*tasks, return_exceptions=True)

        return info

    async def _search_overview(self, info: TechInfo, technology: str, category: str) -> None:
        """Search for overview information."""
        overview_query = f"{technology} {category} overview features"
        try:
            overview_results = await self.searcher.search(
                overview_query, category="general", max_results=3
            )
            if overview_results:
                for result in overview_results:
                    if result.snippet:
                        if result.url not in info.sources:
                            info.sources.append(result.url)
                        # Extract features
                        features = self._extract_features(result.snippet)
                        info.features.extend(features)
        except Exception:
            pass

    async def _search_aspect(
        self, info: TechInfo, aspect: str, technology: str, category: str
    ) -> None:
        """Search for a specific aspect."""
        search_term = self._aspect_to_search_term(aspect, technology, category)
        try:
            results = await self.searcher.search(search_term, category="general", max_results=2)
            if results:
                aspect_info = self._extract_aspect_info(results, aspect)
                if aspect_info:
                    setattr(info, aspect, aspect_info)
                    for result in results:
                        if result.url not in info.sources:
                            info.sources.append(result.url)
        except Exception:
            pass

    def _aspect_to_search_term(self, aspect: str, technology: str, category: str) -> str:
        """Convert aspect to search term.

        Args:
            aspect: The aspect to search for
            technology: Technology name
            category: Category

        Returns:
            Search query string
        """
        # Improved search queries with "vs" to find comparison articles
        aspect_map = {
            "performance": f"{technology} {category} performance fast slow",
            "learning_curve": f"{technology} easy hard learn beginner",
            "ecosystem": f"{technology} packages libraries plugins ecosystem size",
            "popularity": f"{technology} popular usage market share",
            "features": f"{technology} features advantages benefits",
            "use_cases": f"{technology} best for use cases when to use",
            "maintenance": f"{technology} active maintained updates",
            "data_model": f"{technology} data model relational document",
            "scaling": f"{technology} scale scalability horizontal vertical",
        }

        return aspect_map.get(aspect, f"{technology} {aspect} {category}")

    def _extract_features(self, text: str) -> list[str]:
        """Extract feature mentions from text.

        Args:
            text: Text to extract from

        Returns:
            List of feature strings
        """
        features = []

        # Look for common feature patterns
        # "features include:", "key features:", "supports X, Y, Z"
        patterns = [
            r"features?[:\s]+([^.!?]+)",
            r"supports?[:\s]+([^.!?]+)",
            r"capabilities?[:\s]+([^.!?]+)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Split on common delimiters
                items = re.split(r"[,;]", match)
                for item in items:
                    item = item.strip()
                    if item and len(item) < 100:  # Reasonable feature length
                        features.append(item)

        return features[:5]  # Limit to 5 features

    def _extract_aspect_info(self, results, aspect: str) -> str | None:
        """Extract information about a specific aspect from search results.

        Args:
            results: Search results
            aspect: The aspect to extract

        Returns:
            Extracted information or None
        """
        if not results:
            return None

        # Combine snippets from all results
        snippets = [r.snippet for r in results if r.snippet]
        if not snippets:
            return None

        # Try to extract key sentences related to the aspect
        aspect_keywords = {
            "performance": ["fast", "slow", "speed", "performance", "benchmark"],
            "learning_curve": [
                "easy",
                "hard",
                "learn",
                "beginner",
                "simple",
                "complex",
            ],
            "ecosystem": ["packages", "libraries", "plugins", "ecosystem", "community"],
            "popularity": ["popular", "used", "adoption", "market"],
            "features": ["features", "supports", "includes", "offers"],
            "use_cases": ["best for", "use for", "ideal for", "suited"],
            "maintenance": ["maintained", "updated", "active", "development"],
            "data_model": ["relational", "document", "key-value", "graph"],
            "scaling": ["scale", "scalability", "horizontal", "vertical"],
        }

        keywords = aspect_keywords.get(aspect, [])

        # Find sentences mentioning the aspect
        relevant_sentences = []
        for snippet in snippets:
            sentences = re.split(r"[.!?]+", snippet)
            for sentence in sentences:
                sentence = sentence.strip()
                if any(keyword in sentence.lower() for keyword in keywords):
                    relevant_sentences.append(sentence)

        if relevant_sentences:
            # Join top 2 most relevant sentences
            text = ". ".join(relevant_sentences[:2])
            text = " ".join(text.split())  # Normalize whitespace
            text = clamp_text(text, 250)  # Slightly longer for context
            return text

        # Fallback: use first snippet
        text = snippets[0]
        text = " ".join(text.split())
        text = clamp_text(text, 200)
        return text if text else None

    async def _gather_github_metrics(self, info: TechInfo) -> None:
        """Try to gather GitHub metrics for the technology.

        Args:
            info: TechInfo object to update
        """
        name_lower = info.name.lower()

        # Expanded GitHub repo patterns to try
        repo_patterns = [
            f"{name_lower}/{name_lower}",  # react/react
            f"{name_lower}js/{name_lower}",  # vuejs/vue
            f"{name_lower}js/{name_lower}js",  # vite/vitejs
            f"facebook/{name_lower}",  # facebook/react
            f"{name_lower}org/{name_lower}",  # svelte/svelte (svelteorg?)
            f"{name_lower}-lang/{name_lower}",  # rust-lang/rust
            f"python/{name_lower}",  # python/cpython
            f"golang/{name_lower}",  # golang/go
            f"{name_lower}/{name_lower}-core",
            f"{name_lower}/{name_lower}.js",
        ]

        for pattern in repo_patterns:
            try:
                # Split pattern into owner/repo
                if "/" not in pattern:
                    continue
                owner, repo = pattern.split("/", 1)

                repo_info = await self.github_client.get_repo_info(owner, repo)
                if repo_info and repo_info.stars:  # Must have stars to be valid
                    # Add popularity metrics
                    stars = f"{repo_info.stars:,}"
                    forks = f"{repo_info.forks:,}" if repo_info.forks else "0"

                    # Append to existing popularity or create new
                    github_pop = f"GitHub: {stars} stars, {forks} forks"
                    if info.popularity:
                        info.popularity = f"{info.popularity}; {github_pop}"
                    else:
                        info.popularity = github_pop

                    # Add maintenance info
                    if repo_info.last_commit_date:
                        info.maintenance = f"Last commit: {repo_info.last_commit_date}"

                    # Add source
                    if repo_info.url and repo_info.url not in info.sources:
                        info.sources.append(repo_info.url)

                    break  # Found it!
            except Exception:
                continue

    async def _gather_package_metrics(self, info: TechInfo) -> None:
        """Try to gather package registry metrics.

        Args:
            info: TechInfo object to update
        """
        # Try npm first (most common for web frameworks)
        registries = ["npm", "pypi"]

        for registry in registries:
            try:
                pkg_info = None
                if registry == "npm":
                    pkg_info = await self.registry_client.search_npm(info.name.lower())
                elif registry == "pypi":
                    pkg_info = await self.registry_client.search_pypi(info.name.lower())

                if pkg_info:
                    # Add download metrics to popularity
                    if pkg_info.downloads:
                        downloads = pkg_info.downloads
                        current_pop = info.popularity or ""
                        info.popularity = f"{current_pop}, {registry.upper()}: {downloads}".strip(
                            ", "
                        )

                    # Add ecosystem info
                    if pkg_info.dependencies:
                        dep_count = len(pkg_info.dependencies)
                        current_eco = info.ecosystem or ""
                        info.ecosystem = f"{current_eco}, {dep_count} dependencies".strip(", ")

                    break  # Found it!
            except Exception:
                continue

    def compare(self, tech_infos: list[TechInfo], aspects: list[str]) -> dict[str, Any]:
        """Structure comparison from gathered info.

        Args:
            tech_infos: List of TechInfo objects
            aspects: List of aspects to compare

        Returns:
            Structured comparison dictionary
        """
        comparison: dict[str, Any] = {
            "technologies": [t.name for t in tech_infos],
            "category": tech_infos[0].category if tech_infos else "unknown",
            "aspects": {},
            "summary": {},
            "sources": [],
        }

        # Build aspect comparison
        for aspect in aspects:
            comparison["aspects"][aspect] = {}
            for tech in tech_infos:
                value = getattr(tech, aspect, None)
                if value:
                    if isinstance(value, list):
                        # Join list items
                        comparison["aspects"][aspect][tech.name] = ", ".join(value[:3])  # Max 3
                    else:
                        comparison["aspects"][aspect][tech.name] = value
                else:
                    comparison["aspects"][aspect][tech.name] = "Information not found"

        # Build summaries
        for tech in tech_infos:
            summary = self._generate_summary(tech)
            comparison["summary"][tech.name] = summary

        # Collect unique sources
        all_sources = []
        for tech in tech_infos:
            if tech.sources:
                for source in tech.sources[:2]:  # Max 2 sources per tech
                    if source not in all_sources:
                        all_sources.append(source)

        comparison["sources"] = all_sources[:10]  # Max 10 total sources

        return comparison

    def _generate_summary(self, tech: TechInfo) -> str:
        """Generate a best-for summary for a technology.

        Args:
            tech: TechInfo object

        Returns:
            Summary string
        """
        summary_parts = []

        # Analyze gathered data
        if tech.use_cases:
            summary_parts.append(tech.use_cases[:80])

        # Add features if we have them
        if tech.features:
            feature_str = ", ".join(tech.features[:2])
            summary_parts.append(f"Key features: {feature_str}")

        # Add popularity if significant
        if tech.popularity and "stars" in tech.popularity:
            summary_parts.append("Popular choice")

        if summary_parts:
            return "; ".join(summary_parts)[:150]

        return "General-purpose solution"


def detect_category(technologies: list[str]) -> str:
    """Auto-detect category from technology names.

    Args:
        technologies: List of technology names

    Returns:
        Detected category or "auto"
    """
    # Common frameworks
    frameworks = {
        "react",
        "vue",
        "angular",
        "svelte",
        "nextjs",
        "nuxt",
        "gatsby",
        "remix",
    }
    # Common databases
    databases = {
        "postgresql",
        "postgres",
        "mysql",
        "mongodb",
        "redis",
        "sqlite",
        "cassandra",
    }
    # Common languages
    languages = {"python", "javascript", "typescript", "go", "rust", "java", "c++"}

    tech_lower = [t.lower() for t in technologies]

    # Check for frameworks
    if any(t in frameworks for t in tech_lower):
        return "framework"

    # Check for databases
    if any(t in databases for t in tech_lower):
        return "database"

    # Check for languages
    if any(t in languages for t in tech_lower):
        return "language"

    return "library"  # Default to library
