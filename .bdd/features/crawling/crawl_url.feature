Feature: Crawl and summarize page content

  Background:
    Given a researcher has access to the web research assistant

  @integration @crawling
  Scenario Outline: Fetch a page as readable markdown
    When a researcher requests the content for "<url>"
    Then the system returns markdown text that reflects the page content

    Examples:
      | url                                      |
      | https://example.com                      |
      | https://www.iana.org/domains/reserved    |

  @integration @crawling
  Scenario: Truncate long content to a maximum size
    When a researcher requests the content for "https://www.wikipedia.org" with max chars 1000
    Then the system returns no more than 1000 characters of markdown text

  @integration @crawling
  Scenario: Report retrieval failures clearly
    When a researcher requests the content for "https://httpbin.org/status/404"
    Then the system reports the failure without returning misleading content
