Feature: Discover code examples and tutorials

  Background:
    Given a developer has access to the web research assistant

  @integration @search
  Scenario Outline: Find examples by content type
    When a developer searches for examples of "<query>" with content type "<content_type>"
    Then the system returns matching resources with URLs and short descriptions

    Examples:
      | query                                  | content_type |
      | FastAPI dependency injection examples | code         |
      | React hooks tutorial                   | articles     |
      | Rust lifetime examples                 | both         |

  @integration @search
  Scenario: Prefer recent resources when a time range is provided
    When a developer searches for examples of "Vite migration guide" with time range "year"
    Then the system returns resources from the requested time window when available

  @integration @search
  Scenario: Respect maximum result limits
    When a developer searches for examples of "Docker Compose healthcheck" with max results 3
    Then the system returns no more than 3 resources
