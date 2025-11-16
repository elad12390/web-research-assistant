"""API documentation search and extraction."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import httpx


@dataclass(slots=True)
class APIDocumentation:
    """Represents extracted API documentation."""

    api_name: str
    topic: str
    docs_url: str
    overview: str
    parameters: list[dict]
    examples: list[dict]
    related_links: list[dict]
    notes: list[str]
    source_urls: list[str]


class APIDocsDetector:
    """Intelligently find API documentation URLs."""

    # Common documentation URL patterns to try
    # Order matters: try most common patterns first (.com before .io)
    DOC_PATTERNS = [
        # .com patterns (most common)
        "https://docs.{api}.com",
        "https://{api}.com/docs",
        "https://{api}.com/docs/api",  # Stripe-style
        "https://www.{api}.com/docs",
        "https://developers.{api}.com",
        "https://developer.{api}.com",
        "https://{api}.com/documentation",
        "https://api.{api}.com/docs",
        # Framework-specific patterns
        "https://{api}.dev",  # Vite, Nuxt, etc.
        "https://www.{api}.dev",
        "https://{api}.ng",  # Angular-based (Spartan)
        "https://www.{api}.ng",
        # .io patterns (less common, try after .com)
        "https://docs.{api}.io",
        "https://{api}.io/docs",
        "https://www.{api}.io/docs",
        # .org patterns
        "https://{api}.org/docs",
        "https://www.{api}.org/docs",
        "https://docs.{api}.org",
    ]

    def __init__(self):
        self.http_client = httpx.AsyncClient(
            timeout=10.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; API-Docs-Explorer/1.0)"},
        )

    async def find_docs_url(self, api_name: str) -> Optional[str]:
        """
        Dynamically find the official documentation URL for an API.

        Strategy:
        1. Try common URL patterns (docs.X.com, X.com/docs, etc.)
        2. If patterns fail, return None to trigger search fallback
        """
        api_lower = api_name.lower().strip()

        # Try common patterns
        for pattern in self.DOC_PATTERNS:
            url = pattern.format(api=api_lower)
            if await self._is_valid_docs_site(url):
                return url

        # If all patterns fail, return None and let caller search
        return None

    async def _is_valid_docs_site(self, url: str) -> bool:
        """Check if a URL is a valid documentation site."""
        try:
            response = await self.http_client.head(url, timeout=5.0)
            # Check for successful response and likely docs content
            if response.status_code == 200:
                # Optionally verify it looks like a docs site
                # by checking content-type or doing a quick GET
                return True
            return False
        except Exception:
            return False

    def get_docs_domain(self, docs_url: str) -> str:
        """Extract the domain from a documentation URL for site-specific search."""
        parsed = urlparse(docs_url)
        return parsed.netloc

    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()


class APIDocsExtractor:
    """Extract and format API documentation content."""

    def extract_overview(self, content: str) -> str:
        """Extract the overview/description from documentation."""
        # Look for common overview sections
        patterns = [
            r"(?:^|\n)#{1,3}\s*(?:Overview|Description|About|Introduction)\s*\n(.*?)(?:\n#{1,3}|\Z)",
            r"(?:^|\n)(?:Overview|Description):\s*(.*?)(?:\n\n|\Z)",
            # First substantial paragraph
            r"(?:^|\n)([A-Z][^.\n]{50,}\.(?:\s+[A-Z][^.\n]+\.){0,3})",
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
            if match:
                overview = match.group(1).strip()
                # Clean up and limit length
                overview = re.sub(r"\s+", " ", overview)
                if len(overview) > 500:
                    overview = overview[:500] + "..."
                return overview

        # Fallback: first paragraph
        lines = content.strip().split("\n")
        for line in lines:
            line = line.strip()
            if len(line) > 50 and not line.startswith("#"):
                return line[:500]

        return "No overview available."

    def extract_parameters(self, content: str) -> list[dict]:
        """Extract parameter information from documentation."""
        parameters = []

        # Pattern for parameter documentation
        # Matches: "param_name (type, required/optional) - description"
        param_pattern = r"[\*\-]?\s*`?(\w+)`?\s*\(([^)]+)\)\s*[-–—:]\s*(.+?)(?=\n[\*\-]?\s*`?\w+`?\s*\(|\n\n|\Z)"

        matches = re.finditer(param_pattern, content, re.DOTALL)
        for match in matches:
            name = match.group(1)
            type_info = match.group(2).strip()
            description = match.group(3).strip()

            # Clean up description
            description = re.sub(r"\s+", " ", description)

            # Extract if required/optional
            required = "required" in type_info.lower()

            parameters.append(
                {
                    "name": name,
                    "type": type_info,
                    "required": required,
                    "description": description[:300],  # Limit length
                }
            )

        return parameters

    def extract_examples(self, content: str) -> list[dict]:
        """Extract code examples from documentation."""
        examples = []

        # Match code blocks with language specifier
        code_block_pattern = r"```(\w+)\n(.*?)```"
        matches = re.finditer(code_block_pattern, content, re.DOTALL)

        for match in matches:
            language = match.group(1)
            code = match.group(2).strip()

            # Skip very short snippets (likely not examples)
            if len(code) > 20:
                examples.append({"language": language, "code": code})

        return examples[:10]  # Limit to 10 examples

    def extract_notes(self, content: str) -> list[str]:
        """Extract important notes, warnings, and tips."""
        notes = []

        # Look for note/warning/tip sections
        patterns = [
            r"(?:⚠️|⚡|💡|📝|Note|Warning|Important|Tip):\s*(.+?)(?:\n\n|\Z)",
            r"> (.+?)(?:\n\n|\Z)",  # Blockquotes
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content, re.DOTALL)
            for match in matches:
                note = match.group(1).strip()
                note = re.sub(r"\s+", " ", note)
                if len(note) > 30 and len(note) < 500:
                    notes.append(note)

        return notes[:5]  # Limit to 5 notes

    def extract_links(self, content: str, base_url: str) -> list[dict]:
        """Extract related documentation links."""
        links = []

        # Match markdown links
        link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
        matches = re.finditer(link_pattern, content)

        for match in matches:
            title = match.group(1)
            url = match.group(2)

            # Filter for documentation links (not random external links)
            if any(
                keyword in title.lower()
                for keyword in ["api", "docs", "guide", "reference", "tutorial", "see"]
            ):
                # Make relative URLs absolute
                if url.startswith("/"):
                    parsed = urlparse(base_url)
                    url = f"{parsed.scheme}://{parsed.netloc}{url}"

                links.append({"title": title, "url": url})

        # Deduplicate
        seen_urls = set()
        unique_links = []
        for link in links:
            if link["url"] not in seen_urls:
                seen_urls.add(link["url"])
                unique_links.append(link)

        return unique_links[:10]  # Limit to 10 links

    def format_documentation(self, doc: APIDocumentation) -> str:
        """Format extracted documentation into readable text."""
        lines = [
            f"API Documentation: {doc.api_name.title()} - {doc.topic}",
            "═" * 70,
            "",
        ]

        # Overview
        if doc.overview:
            lines.extend(
                [
                    "📖 Overview:",
                    f"   {doc.overview}",
                    "",
                ]
            )

        # Main documentation URL
        lines.extend(
            [
                f"📚 Documentation: {doc.docs_url}",
                "",
            ]
        )

        # Parameters
        if doc.parameters:
            lines.extend(
                [
                    "📋 Parameters:",
                    "─" * 70,
                    "",
                ]
            )
            for param in doc.parameters:
                req_marker = "required" if param["required"] else "optional"
                lines.append(f"   {param['name']} ({param['type']}, {req_marker})")
                lines.append(f"      {param['description']}")
                lines.append("")

        # Code Examples
        if doc.examples:
            lines.extend(
                [
                    "💡 Code Examples:",
                    "─" * 70,
                    "",
                ]
            )
            for i, example in enumerate(doc.examples, 1):
                lines.append(f"   Example {i} ({example['language']}):")
                lines.append(f"   ```{example['language']}")
                # Indent code
                for code_line in example["code"].split("\n"):
                    lines.append(f"   {code_line}")
                lines.append("   ```")
                lines.append("")

        # Important Notes
        if doc.notes:
            lines.extend(
                [
                    "⚠️ Important Notes:",
                    "─" * 70,
                    "",
                ]
            )
            for note in doc.notes:
                lines.append(f"   • {note}")
            lines.append("")

        # Related Links
        if doc.related_links:
            lines.extend(
                [
                    "🔗 Related Documentation:",
                    "─" * 70,
                    "",
                ]
            )
            for link in doc.related_links:
                lines.append(f"   • {link['title']}")
                lines.append(f"     {link['url']}")
                lines.append("")

        # Source URLs
        if doc.source_urls:
            lines.extend(
                [
                    "📄 Sources:",
                    "─" * 70,
                    "",
                ]
            )
            for url in doc.source_urls:
                lines.append(f"   • {url}")

        return "\n".join(lines)
