@api @P0 @github:AgentifyHQ/atdd-bmad-template/issues/1
Feature: Interrupt Content Validation and Sanitization
  As a gateway operator
  I want agent-submitted content to be validated and sanitized before storage
  So that malicious or malformed content never reaches human responders

  @smoke
  Scenario: Submit interrupt with valid text content
    When I send a POST request to "/api/v1/interrupts" with body:
      """json
      {
        "content_type": "text",
        "content": {
          "body": "Please review this deployment request"
        },
        "interrupt_type": "approval_required",
        "correlation_id": "corr-001"
      }
      """
    Then the response status should be 201
    And the response body should contain "id"
    And the response body "content_type" should equal "text"

  Scenario: Submit interrupt with markdown content is sanitized
    When I send a POST request to "/api/v1/interrupts" with body:
      """json
      {
        "content_type": "markdown",
        "content": {
          "body": "## Review <script>alert('xss')</script> this change"
        },
        "interrupt_type": "approval_required",
        "correlation_id": "corr-002"
      }
      """
    Then the response status should be 201
    And the response body should contain "id"
    And the response body "content.body" should not contain "<script>"

  Scenario: Submit interrupt with valid approval content
    When I send a POST request to "/api/v1/interrupts" with body:
      """json
      {
        "content_type": "approval",
        "content": {
          "options": [
            { "label": "Approve", "value": "approved" },
            { "label": "Reject", "value": "rejected" }
          ]
        },
        "interrupt_type": "approval_required",
        "correlation_id": "corr-003"
      }
      """
    Then the response status should be 201
    And the response body should contain "id"

  @negative
  Scenario: Reject invalid approval options
    When I send a POST request to "/api/v1/interrupts" with body:
      """json
      {
        "content_type": "approval",
        "content": {
          "options": []
        },
        "interrupt_type": "approval_required",
        "correlation_id": "corr-004"
      }
      """
    Then the response status should be 400
    And the response error code should be "GW-5001"

  @negative
  Scenario: Reject unknown content type
    When I send a POST request to "/api/v1/interrupts" with body:
      """json
      {
        "content_type": "video",
        "content": {
          "url": "https://example.com/video.mp4"
        },
        "interrupt_type": "approval_required",
        "correlation_id": "corr-005"
      }
      """
    Then the response status should be 400
    And the response error code should be "GW-5002"

  @negative
  Scenario: Reject oversized text content
    When I send a POST request to "/api/v1/interrupts" with body:
      """json
      {
        "content_type": "text",
        "content": {
          "body": "<<OVERSIZED_CONTENT_PLACEHOLDER>>"
        },
        "interrupt_type": "approval_required",
        "correlation_id": "corr-006"
      }
      """
    Then the response status should be 400
    And the response error code should be "GW-5001"

  @negative
  Scenario: Reject invalid json_form schema
    When I send a POST request to "/api/v1/interrupts" with body:
      """json
      {
        "content_type": "json_form",
        "content": {},
        "interrupt_type": "approval_required",
        "correlation_id": "corr-007"
      }
      """
    Then the response status should be 400
    And the response error code should be "GW-5001"
