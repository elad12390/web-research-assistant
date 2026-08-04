from __future__ import annotations

import subprocess
import sys


def test_server_starts_with_declared_mcp_runtime() -> None:
    # Given the installed dependencies and the module entry point
    command = [sys.executable, "-m", "searxng_mcp.server"]

    # When the stdio client closes immediately after startup
    result = subprocess.run(command, input="", capture_output=True, text=True, check=False)

    # Then the server should shut down cleanly instead of failing during import
    assert result.returncode == 0, result.stderr
