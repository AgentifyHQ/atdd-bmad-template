@acceptance @visual @P1
Feature: User Login Visual Regression
  As a designer
  I want the login page to maintain its visual appearance
  So that UI changes are caught before they reach production

  @smoke
  Scenario: Login page matches visual baseline
    Given I am on the login page
    Then the page should match the visual baseline "login-page"

  Scenario: Login error state matches visual baseline
    Given I am on the login page
    When I enter email "invalid"
    And I enter password "wrong"
    And I click the login button
    Then the page should match the visual baseline "login-error-state" with masked:
      | selector        |
      | .timestamp      |
      | .dynamic-content|

  Scenario: Dashboard matches visual baseline after login
    Given a registered user exists with email "testuser@example.com"
    And I am on the login page
    When I enter email "testuser@example.com"
    And I enter password "ValidPassword123!"
    And I click the login button
    Then I should be redirected to the dashboard
    And the page should match the visual baseline "dashboard" with masked:
      | selector        |
      | .timestamp      |
      | .user-avatar    |
      | .notification-count |
