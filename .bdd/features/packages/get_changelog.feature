Feature: Review package changelogs

  Background:
    Given a developer has access to the web research assistant

  @integration @packages
  Scenario Outline: Retrieve recent release notes
    When a developer requests changelog entries for "<package>"
    Then the system returns recent versions with release notes and dates

    Examples:
      | package    |
      | react      |
      | typescript |
      | serde      |

  @integration @packages
  Scenario: Limit the number of releases returned
    When a developer requests changelog entries for "react" with max releases 2
    Then the system returns no more than 2 releases

  @integration @packages
  Scenario: Highlight breaking changes when present
    When a developer requests changelog entries for "next" from registry "npm"
    Then the system identifies any breaking change notes when they are present
