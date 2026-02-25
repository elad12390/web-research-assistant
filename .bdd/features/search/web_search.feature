Feature: Federated web search results

  Background:
    Given a researcher has access to the web research assistant

  @integration @search
  Scenario Outline: Retrieve ranked snippets for a topical query
    When a researcher requests web search results for "<query>" in category "general"
    Then the system returns a ranked list of snippets with source URLs

    Examples:
      | query                           |
      | climate change policy 2024      |
      | quantum computing tutorial      |
      | best python async http client   |

  @integration @search
  Scenario: Constrain results to a specific category
    When a researcher requests web search results for "OpenAI API updates" in category "news"
    Then the system returns results scoped to the requested category

  @integration @search
  Scenario: Handle a query with few or no matches
    When a researcher requests web search results for "asdlkjasdljasdlkjasd" in category "general"
    Then the system returns an empty or very small result set without failure
