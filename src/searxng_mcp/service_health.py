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
        # Payment & Finance
        "stripe": "https://status.stripe.com",
        "paypal": "https://www.paypal-status.com",
        "plaid": "https://status.plaid.com",
        # Code & DevOps
        "github": "https://www.githubstatus.com",
        "gitlab": "https://status.gitlab.com",
        "bitbucket": "https://bitbucket.status.atlassian.com",
        "vercel": "https://www.vercel-status.com",
        "netlify": "https://www.netlifystatus.com",
        "heroku": "https://status.heroku.com",
        "docker": "https://status.docker.com",
        "dockerhub": "https://status.docker.com",
        "npm": "https://status.npmjs.org",
        "pypi": "https://status.python.org",
        "circleci": "https://status.circleci.com",
        # AI & ML Services
        "openai": "https://status.openai.com",
        "anthropic": "https://status.anthropic.com",
        "claude": "https://status.anthropic.com",
        "claudeapi": "https://status.anthropic.com",
        "anthropicclaudeapi": "https://status.anthropic.com",
        "gemini": "https://status.cloud.google.com",
        "googlegemini": "https://status.cloud.google.com",
        "googlegeminiapi": "https://status.cloud.google.com",
        "vertexai": "https://status.cloud.google.com",
        "googlecloudvertexai": "https://status.cloud.google.com",
        "googlecloud": "https://status.cloud.google.com",
        "replicate": "https://replicate.statuspage.io",
        "huggingface": "https://status.huggingface.co",
        "hf": "https://status.huggingface.co",
        "cohere": "https://status.cohere.com",
        "mistral": "https://status.mistral.ai",
        "mistralai": "https://status.mistral.ai",
        "together": "https://status.together.ai",
        "togetherai": "https://status.together.ai",
        "groq": "https://status.groq.com",
        "perplexity": "https://status.perplexity.ai",
        "perplexityai": "https://status.perplexity.ai",
        # Image/Video AI
        "fal": "https://fal.statuspage.io",
        "falai": "https://fal.statuspage.io",
        "midjourney": "https://status.midjourney.com",
        "stability": "https://status.stability.ai",
        "stabilityai": "https://status.stability.ai",
        "runway": "https://status.runwayml.com",
        "runwayml": "https://status.runwayml.com",
        "leonardo": "https://status.leonardo.ai",
        "leonardoai": "https://status.leonardo.ai",
        "ideogram": "https://status.ideogram.ai",
        "flux": "https://status.bfl.ml",
        "bfl": "https://status.bfl.ml",
        "blackforestlabs": "https://status.bfl.ml",
        "blackforestlabsbflfluxapi": "https://status.bfl.ml",
        "bflblackforestlabsfluxapi": "https://status.bfl.ml",
        # Voice/Audio AI
        "elevenlabs": "https://status.elevenlabs.io",
        "11labs": "https://status.elevenlabs.io",
        "resemble": "https://status.resemble.ai",
        "assemblyai": "https://status.assemblyai.com",
        "deepgram": "https://status.deepgram.com",
        # Video AI
        "heygen": "https://status.heygen.com",
        "descript": "https://status.descript.com",
        "luma": "https://status.lumalabs.ai",
        "lumalabs": "https://status.lumalabs.ai",
        "pika": "https://status.pika.art",
        "sync": "https://status.sync.so",
        "syncso": "https://status.sync.so",
        "synclabs": "https://status.sync.so",
        # Cloud Providers
        "aws": "https://health.aws.amazon.com/health/status",
        "amazon": "https://health.aws.amazon.com/health/status",
        "gcp": "https://status.cloud.google.com",
        "googlecloudplatform": "https://status.cloud.google.com",
        "azure": "https://status.azure.com",
        "microsoft": "https://status.azure.com",
        "digitalocean": "https://status.digitalocean.com",
        "linode": "https://status.linode.com",
        "vultr": "https://status.vultr.com",
        "render": "https://status.render.com",
        "railway": "https://railway.instatus.com",
        "fly": "https://status.fly.io",
        "flyio": "https://status.fly.io",
        # Databases
        "mongodb": "https://status.mongodb.com",
        "supabase": "https://status.supabase.com",
        "planetscale": "https://www.planetscalestatus.com",
        "neon": "https://neonstatus.com",
        "fauna": "https://status.fauna.com",
        "redis": "https://status.redis.com",
        "upstash": "https://status.upstash.com",
        "cockroachdb": "https://status.cockroachlabs.cloud",
        # Communication
        "twilio": "https://status.twilio.com",
        "sendgrid": "https://status.sendgrid.com",
        "mailgun": "https://status.mailgun.com",
        "postmark": "https://status.postmarkapp.com",
        "slack": "https://status.slack.com",
        "discord": "https://discordstatus.com",
        "zoom": "https://status.zoom.us",
        "intercom": "https://www.intercomstatus.com",
        # CDN & DNS
        "cloudflare": "https://www.cloudflarestatus.com",
        "fastly": "https://status.fastly.com",
        "akamai": "https://cloudharmony.com/status-for-akamai",
        # Auth & Identity
        "auth0": "https://status.auth0.com",
        "okta": "https://status.okta.com",
        "clerk": "https://status.clerk.com",
        # Analytics & Monitoring
        "datadog": "https://status.datadoghq.com",
        "newrelic": "https://status.newrelic.com",
        "sentry": "https://status.sentry.io",
        "mixpanel": "https://status.mixpanel.com",
        "amplitude": "https://status.amplitude.com",
        "segment": "https://status.segment.com",
        "posthog": "https://status.posthog.com",
        # Other
        "notion": "https://status.notion.so",
        "airtable": "https://status.airtable.com",
        "figma": "https://status.figma.com",
        "linear": "https://linearstatus.com",
        "jira": "https://jira-software.status.atlassian.com",
        "confluence": "https://confluence.status.atlassian.com",
        "atlassian": "https://status.atlassian.com",
        "shopify": "https://www.shopifystatus.com",
        "algolia": "https://status.algolia.com",
        "pinecone": "https://status.pinecone.io",
        "weaviate": "https://status.weaviate.io",
        "qdrant": "https://status.qdrant.io",
        "milvus": "https://status.milvus.io",
    }

    # Service name aliases - map variations to canonical names
    SERVICE_ALIASES = {
        # Anthropic/Claude variations
        "anthropic claude": "anthropic",
        "anthropic claude api": "anthropic",
        "claude api": "anthropic",
        "claude": "anthropic",
        # Google variations
        "google cloud": "gcp",
        "google cloud platform": "gcp",
        "google cloud vertex ai": "vertexai",
        "vertex ai": "vertexai",
        "google gemini": "gemini",
        "google gemini api": "gemini",
        "gemini api": "gemini",
        # Fal variations
        "fal.ai": "fal",
        "fal ai": "fal",
        "fal.ai api": "fal",
        # BFL/Flux variations
        "black forest labs": "bfl",
        "black forest labs flux": "bfl",
        "bfl flux": "bfl",
        "flux api": "bfl",
        "black forest labs bfl flux api": "bfl",
        "bfl black forest labs flux api": "bfl",
        # Sync variations
        "sync.so": "sync",
        "sync labs": "sync",
        # Other common variations
        "eleven labs": "elevenlabs",
        "stability ai": "stability",
        "runway ml": "runway",
        "leonardo ai": "leonardo",
        "hugging face": "huggingface",
        "together ai": "together",
        "mistral ai": "mistral",
        "perplexity ai": "perplexity",
        "luma labs": "luma",
        "fly.io": "fly",
    }

    # Common patterns to try
    STATUS_PAGE_PATTERNS = [
        "https://status.{service}.com",
        "https://status.{service}.io",
        "https://status.{service}.ai",
        "https://{service}.statuspage.io",
        "https://{service}.instatus.com",
        "https://{service}status.com",
        "https://www.{service}status.com",
        "https://{service}.com/status",
    ]

    def normalize_service_name(self, service: str) -> str:
        """Normalize service name using aliases."""
        # Clean up the input
        service_lower = service.lower().strip()

        # Check aliases first
        if service_lower in self.SERVICE_ALIASES:
            return self.SERVICE_ALIASES[service_lower]

        # Try partial matching for aliases
        for alias, canonical in self.SERVICE_ALIASES.items():
            if alias in service_lower or service_lower in alias:
                return canonical

        # Remove common suffixes and clean up
        cleaned = service_lower
        for suffix in [" api", " status", " service"]:
            if cleaned.endswith(suffix):
                cleaned = cleaned[: -len(suffix)].strip()

        # Remove spaces, dots, dashes for lookup
        cleaned = cleaned.replace(" ", "").replace(".", "").replace("-", "")

        return cleaned

    def find_status_page(self, service: str) -> str | None:
        """Find status page URL for a service."""
        # Normalize the service name
        normalized = self.normalize_service_name(service)

        # Check known mappings first
        if normalized in self.KNOWN_STATUS_PAGES:
            return self.KNOWN_STATUS_PAGES[normalized]

        # Also try the raw cleaned name (no alias resolution)
        raw_cleaned = service.lower().replace(" ", "").replace(".", "").replace("-", "")
        if raw_cleaned in self.KNOWN_STATUS_PAGES:
            return self.KNOWN_STATUS_PAGES[raw_cleaned]

        # Try common patterns with normalized name
        for pattern in self.STATUS_PAGE_PATTERNS:
            url = pattern.format(service=normalized)
            return url  # Return first pattern to try

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
                text = indicator.get_text() if hasattr(indicator, "get_text") else str(indicator)
                status.status = self._normalize_status(text)
                if status.status != "unknown":
                    break

        # If still unknown, check for keywords in page
        html_lower = html.lower()
        if status.status == "unknown":
            if "all systems operational" in html_lower or "all systems normal" in html_lower:
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
        incident_elements = soup.find_all(["div", "section"], class_=re.compile(r"incident", re.I))
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
            word in status_lower for word in ["operational", "normal", "ok", "all systems", "up"]
        ):
            return "operational"
        elif any(word in status_lower for word in ["degraded", "slow", "performance"]):
            return "degraded_performance"
        elif any(word in status_lower for word in ["partial", "some", "limited"]):
            return "partial_outage"
        elif any(word in status_lower for word in ["major", "down", "outage", "offline"]):
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

    async def _check_url_accessible(self, url: str) -> tuple[bool, int | None]:
        """Check if URL is accessible via HTTP HEAD request."""
        import httpx

        try:
            async with httpx.AsyncClient(
                timeout=10.0,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (compatible; StatusChecker/1.0)"},
            ) as client:
                response = await client.head(url)
                return response.status_code < 400, response.status_code
        except Exception:
            return False, None

    async def _fetch_statuspage_api(self, status_url: str) -> dict | None:
        """Try to fetch status from Statuspage.io API (many services use this)."""
        import httpx

        # Statuspage.io has a standard API endpoint
        # e.g., https://status.example.com/api/v2/status.json
        api_patterns = [
            f"{status_url.rstrip('/')}/api/v2/status.json",
            f"{status_url.rstrip('/')}/api/v2/summary.json",
        ]

        async with httpx.AsyncClient(
            timeout=10.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; StatusChecker/1.0)"},
        ) as client:
            for api_url in api_patterns:
                try:
                    response = await client.get(api_url)
                    if response.status_code == 200:
                        return response.json()
                except Exception:
                    continue

        return None

    def _parse_statuspage_api_response(self, data: dict, service: str) -> ServiceStatus:
        """Parse Statuspage.io API response."""
        status = ServiceStatus(service=service, status="unknown")

        # Parse status indicator
        if "status" in data:
            indicator = data["status"].get("indicator", "none")
            description = data["status"].get("description", "")

            indicator_map = {
                "none": "operational",
                "minor": "degraded_performance",
                "major": "partial_outage",
                "critical": "major_outage",
                "maintenance": "under_maintenance",
            }
            status.status = indicator_map.get(indicator, "unknown")

            if description:
                status.current_incidents.append(description)

        # Parse components
        if "components" in data:
            for comp in data.get("components", [])[:10]:
                comp_status_map = {
                    "operational": "operational",
                    "degraded_performance": "degraded_performance",
                    "partial_outage": "partial_outage",
                    "major_outage": "major_outage",
                    "under_maintenance": "under_maintenance",
                }
                component = ServiceComponent(
                    name=comp.get("name", "Unknown"),
                    status=comp_status_map.get(comp.get("status", ""), "unknown"),
                )
                status.components.append(component)

        # Parse incidents
        if "incidents" in data:
            for incident in data.get("incidents", [])[:3]:
                name = incident.get("name", "")
                if name:
                    status.current_incidents.append(name)

        return status

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

        # Strategy 1: Try Statuspage.io API (many services use this - it's more reliable)
        api_data = await self._fetch_statuspage_api(status_url)
        if api_data:
            status = self._parse_statuspage_api_response(api_data, service)
            status.status_page_url = status_url
            status.checked_at = datetime.utcnow().isoformat() + "Z"
            return self._format_status_response(status)

        # Strategy 2: Try crawling the page
        try:
            html = await self.crawler.fetch_raw(status_url, max_chars=200000)

            if html and len(html.strip()) > 100:
                # Parse status from HTML
                status = self.parser.parse_status_page(html, service)
                status.status_page_url = status_url
                status.checked_at = datetime.utcnow().isoformat() + "Z"
                return self._format_status_response(status)

        except Exception:
            pass  # Fall through to HTTP check

        # Strategy 3: Fallback - just check if URL is accessible
        accessible, http_code = await self._check_url_accessible(status_url)

        if accessible:
            # Page is up but we couldn't parse it (likely JS-rendered)
            return {
                "service": service,
                "status": "unknown",
                "status_emoji": "❓",
                "status_page_url": status_url,
                "checked_at": datetime.utcnow().isoformat() + "Z",
                "message": "Status page is accessible but requires JavaScript to render. Please check manually.",
                "note": f"Visit {status_url} to see current status",
            }
        else:
            return {
                "service": service,
                "status": "unknown",
                "status_emoji": "❓",
                "status_page_url": status_url,
                "error": f"Status page returned HTTP {http_code}"
                if http_code
                else "Status page unreachable",
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
                {"name": comp.name, "status": comp.status} for comp in status.components[:10]
            ]

        return response
