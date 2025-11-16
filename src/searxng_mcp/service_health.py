"""Service health and status page monitoring."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ServiceComponent:
    """Status of a service component."""

    name: str
    status: str


@dataclass
class ServiceStatus:
    """Overall service health status."""

    service: str
    status: str
    status_page_url: str | None = None
    checked_at: str | None = None
    current_incidents: list[str] = field(default_factory=list)
    components: list[ServiceComponent] = field(default_factory=list)


class StatusPageDetector:
    """Detect and find status pages for services."""

    # Known service → status page mappings
    KNOWN_STATUS_PAGES = {
        "stripe": "https://status.stripe.com",
        "github": "https://www.githubstatus.com",
        "openai": "https://status.openai.com",
        "anthropic": "https://status.anthropic.com",
        "aws": "https://health.aws.amazon.com/health/status",
        "vercel": "https://www.vercel-status.com",
        "netlify": "https://www.netlifystatus.com",
        "cloudflare": "https://www.cloudflarestatus.com",
        "twilio": "https://status.twilio.com",
        "sendgrid": "https://status.sendgrid.com",
        "heroku": "https://status.heroku.com",
        "mongodb": "https://status.mongodb.com",
        "supabase": "https://status.supabase.com",
        "planetscale": "https://www.planetscalestatus.com",
        "gitlab": "https://status.gitlab.com",
        "npm": "https://status.npmjs.org",
        "pypi": "https://status.python.org",
        "docker": "https://status.docker.com",
        "dockerhub": "https://status.docker.com",
        "slack": "https://status.slack.com",
        "discord": "https://discordstatus.com",
        "zoom": "https://status.zoom.us",
        "gcp": "https://status.cloud.google.com",
        "azure": "https://status.azure.com",
        "digitalocean": "https://status.digitalocean.com",
    }

    # Common patterns to try
    STATUS_PAGE_PATTERNS = [
        "https://status.{service}.com",
        "https://{service}.statuspage.io",
        "https://{service}.com/status",
        "https://www.{service}status.com",
    ]

    def find_status_page(self, service: str) -> str | None:
        """Find status page URL for a service."""
        service_lower = service.lower().replace(" ", "").replace("-", "")

        # Check known mappings first
        if service_lower in self.KNOWN_STATUS_PAGES:
            return self.KNOWN_STATUS_PAGES[service_lower]

        # Try common patterns
        for pattern in self.STATUS_PAGE_PATTERNS:
            url = pattern.format(service=service_lower)
            return url  # Return first pattern match

        return None


class StatusPageParser:
    """Parse status pages and extract health information."""

    def parse_status_page(self, html: str, service: str) -> ServiceStatus:
        """Parse status page HTML."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        status = ServiceStatus(service=service, status="unknown")

        # Extract overall status - common patterns
        status_indicators = [
            soup.find("span", class_=re.compile(r"status", re.I)),
            soup.find("div", class_=re.compile(r"status", re.I)),
            soup.find(text=re.compile(r"all systems? (operational|normal)", re.I)),
            soup.find(text=re.compile(r"(no|zero) (active )?incidents?", re.I)),
        ]

        for indicator in status_indicators:
            if indicator:
                text = (
                    indicator.get_text()
                    if hasattr(indicator, "get_text")
                    else str(indicator)
                )
                status.status = self._normalize_status(text)
                if status.status != "unknown":
                    break

        # If still unknown, check for keywords in page
        html_lower = html.lower()
        if status.status == "unknown":
            if (
                "all systems operational" in html_lower
                or "all systems normal" in html_lower
            ):
                status.status = "operational"
            elif "no active incidents" in html_lower or "no incidents" in html_lower:
                status.status = "operational"
            elif "investigating" in html_lower or "identified" in html_lower:
                status.status = "degraded_performance"
            elif "outage" in html_lower or "down" in html_lower:
                status.status = "partial_outage"
            elif "maintenance" in html_lower:
                status.status = "under_maintenance"

        # Extract current incidents
        incident_elements = soup.find_all(
            ["div", "section"], class_=re.compile(r"incident", re.I)
        )
        for incident in incident_elements[:3]:  # Max 3
            title_elem = incident.find(
                ["h3", "h4", "span"], class_=re.compile(r"(title|name)", re.I)
            )
            if title_elem:
                status.current_incidents.append(title_elem.get_text(strip=True))

        # Extract components
        component_elements = soup.find_all("div", class_=re.compile(r"component", re.I))
        for comp in component_elements[:10]:  # Max 10
            name_elem = comp.find(["span", "div"], class_=re.compile(r"name", re.I))
            status_elem = comp.find(["span", "div"], class_=re.compile(r"status", re.I))

            if name_elem and status_elem:
                component = ServiceComponent(
                    name=name_elem.get_text(strip=True),
                    status=self._normalize_status(status_elem.get_text(strip=True)),
                )
                status.components.append(component)

        return status

    def _normalize_status(self, status_text: str) -> str:
        """Normalize status text to standard values."""
        status_lower = status_text.lower()

        if any(
            word in status_lower
            for word in ["operational", "normal", "ok", "all systems", "up"]
        ):
            return "operational"
        elif any(word in status_lower for word in ["degraded", "slow", "performance"]):
            return "degraded_performance"
        elif any(word in status_lower for word in ["partial", "some", "limited"]):
            return "partial_outage"
        elif any(
            word in status_lower for word in ["major", "down", "outage", "offline"]
        ):
            return "major_outage"
        elif "maintenance" in status_lower:
            return "under_maintenance"
        else:
            return "unknown"

    def get_status_emoji(self, status: str) -> str:
        """Get emoji for status."""
        emoji_map = {
            "operational": "✅",
            "degraded_performance": "⚠️",
            "partial_outage": "⚠️",
            "major_outage": "🚨",
            "under_maintenance": "🔧",
            "unknown": "❓",
        }
        return emoji_map.get(status, "❓")


class ServiceHealthChecker:
    """Check health of external services."""

    def __init__(self, crawler_client):
        """Initialize with crawler client."""
        self.crawler = crawler_client
        self.detector = StatusPageDetector()
        self.parser = StatusPageParser()

    async def check_service(self, service: str) -> dict:
        """Check service health status."""
        # Find status page
        status_url = self.detector.find_status_page(service)

        if not status_url:
            return {
                "service": service,
                "status": "unknown",
                "status_emoji": "❓",
                "error": "Could not find status page for this service",
                "suggestion": f"Try checking {service}.com/status or searching for '{service} status page'",
            }

        # Fetch and parse status page
        try:
            html = await self.crawler.fetch_raw(status_url, max_chars=200000)

            # Parse status
            status = self.parser.parse_status_page(html, service)
            status.status_page_url = status_url
            status.checked_at = datetime.utcnow().isoformat() + "Z"

            # Format response
            return self._format_status_response(status)

        except Exception as e:
            return {
                "service": service,
                "status": "unknown",
                "status_emoji": "❓",
                "status_page_url": status_url,
                "error": f"Failed to fetch status page: {str(e)}",
            }

    def _format_status_response(self, status: ServiceStatus) -> dict:
        """Format status object as response dict."""
        response = {
            "service": status.service,
            "status": status.status,
            "status_emoji": self.parser.get_status_emoji(status.status),
            "status_page_url": status.status_page_url,
            "checked_at": status.checked_at,
        }

        if status.current_incidents:
            response["current_incidents"] = status.current_incidents
        else:
            response["current_incidents"] = []
            response["message"] = "No active incidents reported"

        if status.components:
            response["components"] = [
                {"name": comp.name, "status": comp.status}
                for comp in status.components[:10]
            ]

        return response
