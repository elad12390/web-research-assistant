Feature: Search stock images

  Background:
    Given a designer has access to the web research assistant

  @integration @search
  Scenario Outline: Find images by type and orientation
    When a designer searches for images of "<query>" with type "<image_type>" and orientation "<orientation>"
    Then the system returns image results with URLs and attribution

    Examples:
      | query                 | image_type  | orientation |
      | modern office workspace | photo     | horizontal  |
      | mountain landscape      | illustration | horizontal |
      | analytics dashboard     | vector    | horizontal  |

  @integration @search
  Scenario: Handle rare image topics gracefully
    When a designer searches for images of "orthorhombic crystal lattice" with type "photo"
    Then the system returns zero or more images without error

  @integration @search
  Scenario: Limit the number of returned images
    When a designer searches for images of "coffee shop interior" with max results 5
    Then the system returns no more than 5 images
