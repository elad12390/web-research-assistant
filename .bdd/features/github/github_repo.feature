Feature: Inspect GitHub repository health

  Background:
    Given a developer has access to the web research assistant

  @integration @github
  Scenario Outline: Retrieve repository health details
    When a developer requests repository information for "<repo>"
    Then the system returns stars, forks, open issues, and license data

    Examples:
      | repo                          |
      | facebook/react                |
      | https://github.com/psf/requests |

  @integration @github
  Scenario: Include recent commit activity when requested
    When a developer requests repository information for "vercel/next.js" with commits included
    Then the system includes recent commit activity in the response

  @integration @github
  Scenario: Report an unknown repository clearly
    When a developer requests repository information for "nonexistent-org/nonexistent-repo"
    Then the system reports that the repository cannot be found
