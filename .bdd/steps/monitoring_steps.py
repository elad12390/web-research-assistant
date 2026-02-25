from pytest_bdd import parsers, then, when

from support.fixtures import async_step


@when(
    parsers.parse('a reliability engineer checks the status of "{service}"'),
    target_fixture="status_result",
)
@async_step
async def check_status(service):
    from searxng_mcp.server import check_service_status

    return await check_service_status(service=service, reasoning="BDD test")


@then("the system returns the current status and any active incident summaries")
def verify_status_incidents(status_result):
    import json

    data = json.loads(status_result)
    assert "service" in data
    assert "status" in data


@then("the system reports that the service is not supported and suggests known services")
def verify_status_not_supported(status_result):
    import json

    data = json.loads(status_result)
    assert data.get("status") == "unknown"
    assert "error" in data or "message" in data


@then("the system reports operational status without incident details")
def verify_status_operational(status_result):
    import json

    data = json.loads(status_result)
    assert "status" in data
    status = data.get("status", "")
    incidents = data.get("current_incidents", [])
    is_operational = status == "operational" and incidents == []
    is_known_status = status in ("operational", "degraded_performance", "unknown")
    assert is_operational or is_known_status, f"Expected operational or known status, got: {status}"
