@api @P0
Feature: User CRUD API
  As a service consumer
  I want to manage users via the REST API
  So that user data is consistently created, read, updated, and deleted

  @smoke
  Scenario: Create a new user
    When I send a POST request to "/api/users" with body:
      """json
      {
        "name": "James Kim",
        "email": "james@example.com",
        "role": "admin"
      }
      """
    Then the response status should be 201
    And the response body should contain "id"
    And the response body "name" should equal "James Kim"
    And the response body "role" should equal "admin"

  Scenario: Retrieve an existing user by ID
    Given a user exists with name "Lookup User" and email "lookup@example.com"
    When I send a GET request to "/api/users/{userId}"
    Then the response status should be 200
    And the response body "name" should equal "Lookup User"
    And the response body "email" should equal "lookup@example.com"

  Scenario: Update an existing user
    Given a user exists with name "Old Name" and email "update@example.com"
    When I send a PUT request to "/api/users/{userId}" with body:
      """json
      {
        "name": "New Name"
      }
      """
    Then the response status should be 200
    And the response body "name" should equal "New Name"

  Scenario: Delete an existing user
    Given a user exists with name "Delete Me" and email "delete@example.com"
    When I send a DELETE request to "/api/users/{userId}"
    Then the response status should be 204

  @negative
  Scenario: Create user with duplicate email returns 409
    Given a user exists with name "Existing" and email "duplicate@example.com"
    When I send a POST request to "/api/users" with body:
      """json
      {
        "name": "Another",
        "email": "duplicate@example.com",
        "role": "user"
      }
      """
    Then the response status should be 409
    And the response error code should be "EMAIL_ALREADY_EXISTS"

  @negative
  Scenario: Create user with missing required fields returns 400
    When I send a POST request to "/api/users" with body:
      """json
      {
        "name": "No Email User"
      }
      """
    Then the response status should be 400
    And the response error code should be "VALIDATION_ERROR"

  Scenario: Retrieve non-existent user returns 404
    When I send a GET request to "/api/users/non-existent-id"
    Then the response status should be 404
    And the response error code should be "USER_NOT_FOUND"
