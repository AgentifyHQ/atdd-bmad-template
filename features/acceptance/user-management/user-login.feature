@example @acceptance @P0
Feature: User Login Journey
  As a registered user
  I want to log in to the application
  So that I can access my dashboard and protected resources

  Background:
    Given a registered user exists with email "testuser@example.com"

  @smoke
  Scenario: Successful login with valid credentials
    Given I am on the login page
    When I enter email "testuser@example.com"
    And I enter password "ValidPassword123!"
    And I click the login button
    Then I should be redirected to the dashboard
    And I should see a welcome message containing my name

  Scenario: Login fails with invalid password
    Given I am on the login page
    When I enter email "testuser@example.com"
    And I enter password "WrongPassword"
    And I click the login button
    Then I should see an error message "Invalid email or password"
    And I should remain on the login page

  Scenario: Login fails with non-existent email
    Given I am on the login page
    When I enter email "nobody@example.com"
    And I enter password "AnyPassword123"
    And I click the login button
    Then I should see an error message "Invalid email or password"

  Scenario Outline: Login validation for empty fields
    Given I am on the login page
    When I enter email "<email>"
    And I enter password "<password>"
    And I click the login button
    Then I should see a validation error for "<field>"

    Examples:
      | email               | password         | field    |
      |                     | ValidPassword123 | email    |
      | testuser@example.com |                  | password |
      |                     |                  | email    |
