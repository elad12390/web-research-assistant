from pytest_bdd import parsers, then, when

from support.fixtures import async_step


@when(
    parsers.parse('a developer submits the error message "{error_message}"'),
    target_fixture="error_result",
)
@async_step
async def submit_error_message(error_message):
    from searxng_mcp.server import translate_error

    return await translate_error(error_message=error_message, reasoning="BDD test")


@when(
    parsers.parse(
        'a developer submits the error message "{error_message}" with framework "{framework}"'
    ),
    target_fixture="error_result",
)
@async_step
async def submit_error_message_with_framework(error_message, framework):
    from searxng_mcp.server import translate_error

    return await translate_error(
        error_message=error_message, reasoning="BDD test", framework=framework
    )


@then("the system returns likely causes and links to relevant solutions")
def verify_error_solutions(error_result):
    assert error_result
    lower = error_result.lower()
    has_urls = "http" in lower
    has_parsed_info = "parsed error info" in lower or "no solutions found" in lower
    assert has_urls or has_parsed_info, f"Expected URLs or parsed info, got: {error_result[:200]}"


@then("the system prioritizes solutions that match the provided framework")
def verify_error_framework(error_result):
    assert "fastapi" in error_result.lower()


@then("the system returns best-effort guidance without failing")
def verify_error_best_effort(error_result):
    assert error_result
    lower = error_result.lower()
    is_no_solutions = "no solutions found" in lower
    is_translation_failed_with_guidance = "error translation failed" in lower and "try" in lower
    is_normal = "http" in lower
    assert is_no_solutions or is_translation_failed_with_guidance or is_normal, (
        f"Expected best-effort guidance, got: {error_result[:200]}"
    )
