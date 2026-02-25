Feature: Compare technologies side-by-side

  Background:
    Given a product engineer has access to the web research assistant

  @integration @comparison @slow
  Scenario Outline: Compare common technology choices
    When a product engineer compares the technologies "<technologies>" in category "<category>"
    Then the system returns a structured comparison with popularity signals

    Examples:
      | technologies                 | category  |
      | PostgreSQL, MySQL            | database  |
      | FastAPI, Flask               | framework |

  @integration @comparison
  Scenario: Focus the comparison on specific aspects
    When a product engineer compares the technologies "PostgreSQL, MongoDB" with aspects "performance, learning_curve"
    Then the system emphasizes the requested aspects in the comparison

  @integration @comparison
  Scenario: Handle unknown technologies gracefully
    When a product engineer compares the technologies "MadeUpDB, PostgreSQL"
    Then the system explains any missing data for unknown technologies
