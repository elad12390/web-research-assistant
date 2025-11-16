from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import _env_str


class UsageTracker:
    """Tracks tool usage for analytics and optimization."""

    def __init__(self) -> None:
        # Get tracking file path from env or use default in user's home directory
        default_path = str(Path.home() / ".config" / "web-research-assistant" / "usage.json")
        self.log_file = Path(_env_str("MCP_USAGE_LOG", default_path))
        self._ensure_log_file()

    def _ensure_log_file(self) -> None:
        """Ensure log file exists with proper structure."""
        if not self.log_file.exists():
            initial_data = {
                "server_name": "web-research-assistant",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "sessions": [],
                "summary": {
                    "total_calls": 0,
                    "tools": {},
                    "most_used_tool": None,
                    "average_response_time": 0.0,
                },
            }
            self._write_log(initial_data)

    def _read_log(self) -> dict[str, Any]:
        """Read current log data."""
        try:
            with open(self.log_file, encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Reset if corrupted
            self._ensure_log_file()
            return self._read_log()

    def _write_log(self, data: dict[str, Any]) -> None:
        """Write log data to file."""
        # Ensure directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.log_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def track_usage(
        self,
        tool_name: str,
        reasoning: str,
        parameters: dict[str, Any],
        response_time_ms: float,
        success: bool,
        error_message: str | None = None,
        response_size: int = 0,
    ) -> None:
        """Track a single tool usage."""

        usage_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool": tool_name,
            "reasoning": reasoning,
            "parameters": parameters,
            "response_time_ms": response_time_ms,
            "success": success,
            "error": error_message,
            "response_size_bytes": response_size,
            "session_id": self._get_session_id(),
        }

        data = self._read_log()

        # Add to sessions
        data["sessions"].append(usage_entry)

        # Update summary
        data["summary"]["total_calls"] += 1

        # Update tool counts
        if tool_name not in data["summary"]["tools"]:
            data["summary"]["tools"][tool_name] = {
                "count": 0,
                "success_count": 0,
                "total_response_time": 0.0,
                "avg_response_time": 0.0,
                "common_reasonings": {},
            }

        tool_stats = data["summary"]["tools"][tool_name]
        tool_stats["count"] += 1
        if success:
            tool_stats["success_count"] += 1
        tool_stats["total_response_time"] += response_time_ms
        tool_stats["avg_response_time"] = tool_stats["total_response_time"] / tool_stats["count"]

        # Track reasoning patterns
        reasoning_key = reasoning[:50]  # Truncate for grouping
        if reasoning_key not in tool_stats["common_reasonings"]:
            tool_stats["common_reasonings"][reasoning_key] = 0
        tool_stats["common_reasonings"][reasoning_key] += 1

        # Update most used tool
        most_used = max(
            data["summary"]["tools"].keys(),
            key=lambda t: data["summary"]["tools"][t]["count"],
        )
        data["summary"]["most_used_tool"] = most_used

        # Update average response time
        total_time = sum(
            stats["total_response_time"] for stats in data["summary"]["tools"].values()
        )
        data["summary"]["average_response_time"] = total_time / data["summary"]["total_calls"]

        self._write_log(data)

    def _get_session_id(self) -> str:
        """Get or create a session ID for grouping related calls."""
        # Simple session ID based on current hour
        return datetime.now(timezone.utc).strftime("%Y%m%d_%H")

    def get_usage_summary(self) -> dict[str, Any]:
        """Get current usage summary."""
        data = self._read_log()
        return data["summary"]

    def get_tool_analytics(self, tool_name: str) -> dict[str, Any] | None:
        """Get detailed analytics for a specific tool."""
        data = self._read_log()
        return data["summary"]["tools"].get(tool_name)

    def get_recent_usage(self, hours: int = 24) -> list[dict[str, Any]]:
        """Get usage from the last N hours."""
        data = self._read_log()

        cutoff = datetime.now(timezone.utc).timestamp() - (hours * 3600)

        recent = []
        for session in data["sessions"]:
            session_time = datetime.fromisoformat(session["timestamp"]).timestamp()
            if session_time >= cutoff:
                recent.append(session)

        return recent

    def export_analytics_report(self) -> str:
        """Generate a human-readable analytics report."""
        data = self._read_log()
        summary = data["summary"]

        lines = [
            "# Web Research Assistant - Usage Analytics Report",
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "## Overall Statistics",
            f"- Total tool calls: {summary['total_calls']}",
            f"- Most used tool: {summary.get('most_used_tool', 'N/A')}",
            f"- Average response time: {summary['average_response_time']:.1f}ms",
            "",
            "## Tool Usage Breakdown",
        ]

        # Sort tools by usage count
        sorted_tools = sorted(summary["tools"].items(), key=lambda x: x[1]["count"], reverse=True)

        for tool_name, stats in sorted_tools:
            success_rate = (
                (stats["success_count"] / stats["count"]) * 100 if stats["count"] > 0 else 0
            )
            lines.extend(
                [
                    f"### {tool_name}",
                    f"- Calls: {stats['count']} ({success_rate:.1f}% success rate)",
                    f"- Avg response time: {stats['avg_response_time']:.1f}ms",
                    "- Common reasons:",
                ]
            )

            # Show top 3 reasonings
            top_reasonings = sorted(
                stats["common_reasonings"].items(), key=lambda x: x[1], reverse=True
            )[:3]

            for reasoning, count in top_reasonings:
                lines.append(f'  - "{reasoning}" ({count}x)')

            lines.append("")

        return "\n".join(lines)


# Global tracker instance
_tracker = None


def get_tracker() -> UsageTracker:
    """Get the global usage tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = UsageTracker()
    return _tracker
