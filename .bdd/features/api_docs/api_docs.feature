Feature: Discover official API documentation

  Background:
    Given a researcher has access to the web research assistant

  @integration @api_docs
  Scenario Outline: Locate official docs for a specific topic
    When a researcher requests official API docs for "<api_name>" about "<topic>"
    Then the system returns authoritative documentation sources relevant to the topic

    Examples:
      | api_name | topic                    |
      | stripe   | create customer          |
      | github   | create repository        |
      | twilio   | send sms message         |

  @integration @api_docs
  Scenario: Limit the number of documentation sources
    When a researcher requests official API docs for "stripe" about "webhooks" with max results 1
    Then the system returns no more than 1 documentation source

  @integration @api_docs
  Scenario: Report missing documentation clearly
    When a researcher requests official API docs for "imaginary-api" about "authentication"
    Then the system reports that no authoritative docs could be found
