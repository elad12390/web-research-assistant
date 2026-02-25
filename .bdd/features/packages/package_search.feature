Feature: Discover packages by keyword

  Background:
    Given a developer has access to the web research assistant

  @integration @packages
  Scenario Outline: Find packages relevant to a query
    When a developer searches packages for "<query>" in registry "<registry>"
    Then the system returns a ranked list of packages with names and short descriptions

    Examples:
      | query         | registry |
      | web framework | npm      |
      | http client   | pypi     |
      | async runtime | crates   |

  @integration @packages
  Scenario: Respect maximum result limits
    When a developer searches packages for "logging" in registry "npm" with max results 3
    Then the system returns no more than 3 packages

  @integration @packages
  Scenario: Handle queries with limited matches
    When a developer searches packages for "zigbee mqtt gateway" in registry "npm"
    Then the system returns zero or more packages without failure
