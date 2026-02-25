from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import NamedTuple

from .crawler import FetchMethod, FetchResult, FetchStatus


class _TimestampedEvent(NamedTuple):
    timestamp: float
    status: FetchStatus
    method: FetchMethod
    http_status: int | None
    response_time_ms: float


@dataclass
class DomainMetrics:
    domain: str
    total_requests: int
    success_count: int
    blocked_count: int
    rate_limited_count: int
    error_count: int
    stealth_escalations: int
    stealth_successes: int
    avg_response_time_ms: float
    last_status: FetchStatus
    last_fetch_time: str

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.success_count / self.total_requests) * 100

    @property
    def block_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.blocked_count / self.total_requests) * 100


class DomainHealthTracker:
    """Thread-safe, in-memory domain health tracker with rolling window."""

    def __init__(self, window_seconds: int = 3600) -> None:
        self._window_seconds = window_seconds
        self._lock = threading.RLock()
        self._events: dict[str, deque[_TimestampedEvent]] = {}
        self._stealth_escalations: dict[str, int] = {}
        self._stealth_successes: dict[str, int] = {}

    def record(self, result: FetchResult) -> None:
        """Record a FetchResult for domain tracking."""
        now = datetime.now(timezone.utc).timestamp()

        with self._lock:
            domain = result.domain
            if domain not in self._events:
                self._events[domain] = deque()
                self._stealth_escalations[domain] = 0
                self._stealth_successes[domain] = 0

            event = _TimestampedEvent(
                timestamp=now,
                status=result.status,
                method=result.method,
                http_status=result.http_status,
                response_time_ms=result.response_time_ms,
            )
            self._events[domain].append(event)

            if result.method == FetchMethod.STEALTH:
                self._stealth_escalations[domain] += 1
                if result.status == FetchStatus.OK:
                    self._stealth_successes[domain] += 1

            self._prune_old_events(domain, now)

    def get_domain_metrics(self, domain: str) -> DomainMetrics | None:
        """Get metrics for a specific domain."""
        with self._lock:
            if domain not in self._events:
                return None

            now = datetime.now(timezone.utc).timestamp()
            self._prune_old_events(domain, now)

            events = self._events[domain]
            if not events:
                return None

            total = len(events)
            success_count = sum(1 for e in events if e.status == FetchStatus.OK)
            blocked_count = sum(1 for e in events if e.status == FetchStatus.BLOCKED)
            rate_limited_count = sum(1 for e in events if e.status == FetchStatus.RATE_LIMITED)
            error_count = sum(1 for e in events if e.status == FetchStatus.ERROR)

            avg_response_time = (
                sum(e.response_time_ms for e in events) / total if total > 0 else 0.0
            )

            last_event = events[-1]
            last_fetch_time = datetime.fromtimestamp(
                last_event.timestamp, tz=timezone.utc
            ).isoformat()

            return DomainMetrics(
                domain=domain,
                total_requests=total,
                success_count=success_count,
                blocked_count=blocked_count,
                rate_limited_count=rate_limited_count,
                error_count=error_count,
                stealth_escalations=self._stealth_escalations[domain],
                stealth_successes=self._stealth_successes[domain],
                avg_response_time_ms=avg_response_time,
                last_status=last_event.status,
                last_fetch_time=last_fetch_time,
            )

    def get_all_metrics(self) -> list[DomainMetrics]:
        """Get metrics for all tracked domains, sorted by block_rate descending."""
        with self._lock:
            now = datetime.now(timezone.utc).timestamp()
            for domain in list(self._events.keys()):
                self._prune_old_events(domain, now)

            metrics = []
            for domain in self._events:
                m = self.get_domain_metrics(domain)
                if m is not None:
                    metrics.append(m)

            return sorted(metrics, key=lambda m: m.block_rate, reverse=True)

    def is_domain_healthy(self, domain: str) -> bool:
        """Returns False if block_rate > 50% in the rolling window."""
        metrics = self.get_domain_metrics(domain)
        if metrics is None:
            return True
        return metrics.block_rate <= 50.0

    def get_recommended_method(self, domain: str) -> FetchMethod:
        """Returns STEALTH if domain has >30% block rate, else NORMAL."""
        metrics = self.get_domain_metrics(domain)
        if metrics is None:
            return FetchMethod.NORMAL
        if metrics.block_rate > 30.0:
            return FetchMethod.STEALTH
        return FetchMethod.NORMAL

    def format_report(self) -> str:
        """Human-readable report of all domain metrics."""
        metrics_list = self.get_all_metrics()
        if not metrics_list:
            return "No domain metrics recorded yet."

        lines = [
            "# Domain Health Report",
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "## Summary",
            f"Total domains tracked: {len(metrics_list)}",
            "",
            "## Domain Metrics (sorted by block rate)",
        ]

        for m in metrics_list:
            lines.extend(
                [
                    f"### {m.domain}",
                    f"- Requests: {m.total_requests}",
                    f"- Success rate: {m.success_rate:.1f}%",
                    f"- Block rate: {m.block_rate:.1f}%",
                    f"- Rate limited: {m.rate_limited_count}",
                    f"- Errors: {m.error_count}",
                    f"- Stealth escalations: {m.stealth_escalations}",
                    f"- Stealth successes: {m.stealth_successes}",
                    f"- Avg response time: {m.avg_response_time_ms:.1f}ms",
                    f"- Last status: {m.last_status.value}",
                    f"- Last fetch: {m.last_fetch_time}",
                    "",
                ]
            )

        return "\n".join(lines)

    def _prune_old_events(self, domain: str, now: float) -> None:
        """Remove events outside the rolling window (not thread-safe, call with lock)."""
        if domain not in self._events:
            return

        cutoff = now - self._window_seconds
        events = self._events[domain]

        while events and events[0].timestamp < cutoff:
            events.popleft()

        if not events:
            del self._events[domain]
            self._stealth_escalations.pop(domain, None)
            self._stealth_successes.pop(domain, None)


_tracker: DomainHealthTracker | None = None


def get_domain_health_tracker() -> DomainHealthTracker:
    """Get the global domain health tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = DomainHealthTracker()
    return _tracker
