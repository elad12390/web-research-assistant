Feature: Inspect package metadata

  Background:
    Given a developer has access to the web research assistant

  @integration @packages
  Scenario Outline: Retrieve metadata from different registries
    When a developer requests package info for "<name>" from registry "<registry>"
    Then the system returns the latest version, license, and dependency summary

    Examples:
      | name                    | registry |
      | express                 | npm      |
      | fastapi                 | pypi     |
      | serde                   | crates   |
      | github.com/gin-gonic/gin | go      |

  @integration @packages
  Scenario: Include security and download signals when available
    When a developer requests package info for "requests" from registry "pypi"
    Then the system includes security status and download indicators when provided by the registry

  @integration @packages
  Scenario: Report a missing package clearly
    When a developer requests package info for "zzz-nonexistent-pkg-bdd-12345" from registry "npm"
    Then the system reports that the package cannot be found
