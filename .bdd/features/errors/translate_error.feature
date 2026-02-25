Feature: Translate errors into actionable solutions

  Background:
    Given a developer has access to the web research assistant

  @integration @errors
  Scenario Outline: Identify language context and provide solutions
    When a developer submits the error message "<error_message>"
    Then the system returns likely causes and links to relevant solutions

    Examples:
      | error_message                                              |
      | TypeError: Cannot read properties of undefined (reading 'map') |
      | ModuleNotFoundError: No module named 'requests'            |
      | error[E0382]: borrow of moved value                        |

  @integration @errors
  Scenario: Respect an explicit language or framework hint
    When a developer submits the error message "CORS policy: No 'Access-Control-Allow-Origin' header" with framework "FastAPI"
    Then the system prioritizes solutions that match the provided framework

  @integration @errors
  Scenario: Handle ambiguous error strings gracefully
    When a developer submits the error message "unknown error"
    Then the system returns best-effort guidance without failing
