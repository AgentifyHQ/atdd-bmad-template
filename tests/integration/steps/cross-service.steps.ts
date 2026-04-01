import { expect } from '@playwright/test';
import { createBdd } from 'playwright-bdd';

const { Given, When, Then } = createBdd();

/**
 * Integration test steps for cross-service scenarios.
 * Uses Playwright request context with different baseUrls per service.
 */

let serviceUrls: Record<string, string> = {};
let userId: string | undefined;
let orderId: string | undefined;
let lastResponse = { status: 0, body: null as any };
let products = new Map<string, { id: string; initialStock: number }>();

// ── Background: Service availability ──

Given('the user service is available at USER_SERVICE_URL', async ({}) => {
  serviceUrls = {};
  userId = undefined;
  orderId = undefined;
  lastResponse = { status: 0, body: null };
  products = new Map();
  serviceUrls.user = process.env.USER_SERVICE_URL || 'http://localhost:3001';
});

Given('the order service is available at ORDER_SERVICE_URL', async ({}) => {
  serviceUrls.order = process.env.ORDER_SERVICE_URL || 'http://localhost:3002';
});

Given('the inventory service is available at INVENTORY_SERVICE_URL', async ({}) => {
  serviceUrls.inventory = process.env.INVENTORY_SERVICE_URL || 'http://localhost:3003';
});

// ── Given: Data setup ──

Given('a user {string} exists in the user service', async ({ request }, name: string) => {
  const response = await request.post(`${serviceUrls.user}/api/users`, {
    data: {
      name,
      email: `${name.toLowerCase().replace(/\s/g, '-')}-${Date.now()}@test.example.com`,
      password: 'TestPass123!',
    },
  });
  const body = await response.json();
  userId = body.id;
});

Given(
  'product {string} has {int} units in inventory',
  async ({ request }, productId: string, units: number) => {
    await request.put(`${serviceUrls.inventory}/api/inventory/${productId}`, {
      data: { quantity: units },
    });
    products.set(productId, { id: productId, initialStock: units });
  },
);

// ── When: Actions ──

When(
  'I create an order for user with {int} units of {string}',
  async ({ request }, quantity: number, productId: string) => {
    const response = await request.post(`${serviceUrls.order}/api/orders`, {
      data: {
        userId,
        items: [{ productId, quantity }],
      },
    });
    lastResponse = {
      status: response.status(),
      body: await response.json().catch(() => null),
    };
    if (lastResponse.body?.id) {
      orderId = lastResponse.body.id;
    }
  },
);

When(
  'I create an order for non-existent user {string} with {int} unit of {string}',
  async ({ request }, fakeUserId: string, quantity: number, productId: string) => {
    const response = await request.post(`${serviceUrls.order}/api/orders`, {
      data: {
        userId: fakeUserId,
        items: [{ productId, quantity }],
      },
    });
    lastResponse = {
      status: response.status(),
      body: await response.json().catch(() => null),
    };
  },
);

When('the order is marked as {string}', async ({ request }, status: string) => {
  await request.patch(`${serviceUrls.order}/api/orders/${orderId}`, {
    data: { status },
  });
});

// ── Then: Assertions ──

Then('the order service should return status {int}', async ({}, expectedStatus: number) => {
  expect(lastResponse.status).toBe(expectedStatus);
});

Then('the order should have status {string}', async ({}, expectedStatus: string) => {
  expect(lastResponse.body?.status).toBe(expectedStatus);
});

Then('the order error code should be {string}', async ({}, expectedCode: string) => {
  expect(lastResponse.body?.code ?? lastResponse.body?.error?.code).toBe(expectedCode);
});

Then(
  'eventually the inventory for {string} should be {int} units',
  async ({ request }, productId: string, expectedQty: number) => {
    const maxAttempts = 15;
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const response = await request.get(
        `${serviceUrls.inventory}/api/inventory/${productId}`,
      );
      const body = await response.json();
      if (body.quantity === expectedQty) return;
      await new Promise((r) => setTimeout(r, 1000));
    }
    const finalResponse = await request.get(
      `${serviceUrls.inventory}/api/inventory/${productId}`,
    );
    const finalBody = await finalResponse.json();
    expect(finalBody.quantity).toBe(expectedQty);
  },
);

Then(
  'eventually the user service should show the order as {string}',
  async ({ request }, expectedStatus: string) => {
    const maxAttempts = 15;
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const response = await request.get(
        `${serviceUrls.user}/api/users/${userId}/orders`,
      );
      const body = await response.json();
      const order = body.orders?.find((o: any) => o.id === orderId);
      if (order?.status === expectedStatus) return;
      await new Promise((r) => setTimeout(r, 1000));
    }
    const finalResponse = await request.get(
      `${serviceUrls.user}/api/users/${userId}/orders`,
    );
    const finalBody = await finalResponse.json();
    const order = finalBody.orders?.find((o: any) => o.id === orderId);
    expect(order?.status).toBe(expectedStatus);
  },
);
