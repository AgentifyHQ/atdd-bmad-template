@integration @P1
Feature: Cross-Service Order Flow
  As a system
  I want orders to propagate correctly across user, order, and inventory services
  So that data remains consistent across all microservices

  Background:
    Given the user service is available at USER_SERVICE_URL
    And the order service is available at ORDER_SERVICE_URL
    And the inventory service is available at INVENTORY_SERVICE_URL

  @smoke
  Scenario: Successful order decreases inventory
    Given a user "Order Buyer" exists in the user service
    And product "WIDGET-001" has 50 units in inventory
    When I create an order for user with 3 units of "WIDGET-001"
    Then the order service should return status 201
    And the order should have status "pending"
    And eventually the inventory for "WIDGET-001" should be 47 units

  Scenario: Order rejected for non-existent user
    When I create an order for non-existent user "ghost-user-id" with 1 unit of "WIDGET-001"
    Then the order service should return status 400
    And the order error code should be "INVALID_USER"

  Scenario: Order rejected when insufficient inventory
    Given a user "Low Stock Buyer" exists in the user service
    And product "RARE-001" has 2 units in inventory
    When I create an order for user with 5 units of "RARE-001"
    Then the order service should return status 409
    And the order error code should be "INSUFFICIENT_INVENTORY"

  @eventual-consistency
  Scenario: Order status updates propagate to user service
    Given a user "Status Watcher" exists in the user service
    And product "WIDGET-002" has 100 units in inventory
    When I create an order for user with 1 units of "WIDGET-002"
    And the order is marked as "shipped"
    Then eventually the user service should show the order as "shipped"
