Feature: Extract structured data from web pages

  Background:
    Given an analyst has access to the web research assistant

  @integration @crawling
  Scenario Outline: Extract common structures from known pages
    When an analyst extracts "<extract_type>" data from "<url>"
    Then the system returns structured data for the requested type

    Examples:
      | extract_type | url                                                             |
      | table        | https://en.wikipedia.org/wiki/List_of_countries_by_population_(United_Nations) |
      | list         | https://www.iana.org/domains/reserved                           |
      | json-ld      | https://www.imdb.com/title/tt0111161/                           |

  @integration @crawling
  Scenario: Extract specific fields with selectors
    When an analyst extracts fields from "https://www.iana.org/domains/reserved" using selectors:
      | title | h1 |
      | intro | p  |
    Then the system returns a structured object with the selected fields

  @integration @crawling
  Scenario: Limit the number of extracted items
    When an analyst extracts "list" data from "https://www.iana.org/domains/reserved" with max items 3
    Then the system returns no more than 3 list items
