Feature: Check service health status

  Background:
    Given a reliability engineer has access to the web research assistant

  @integration @monitoring
  Scenario Outline: Retrieve current status for major services
    When a reliability engineer checks the status of "<service>"
    Then the system returns the current status and any active incident summaries

    Examples:
      | service |
      | GitHub  |
      | Stripe  |
      | OpenAI  |

  @integration @monitoring
  Scenario: Explain when a service is not supported
    When a reliability engineer checks the status of "Contoso Cloud"
    Then the system reports that the service is not supported and suggests known services

  @integration @monitoring
  Scenario: Provide a stable response when no incidents are active
    When a reliability engineer checks the status of "AWS"
    Then the system reports operational status without incident details
