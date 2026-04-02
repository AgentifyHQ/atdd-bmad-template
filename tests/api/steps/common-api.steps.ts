import { expect } from '@playwright/test';
import { createBdd } from 'playwright-bdd';

const { Given, When, Then } = createBdd();

/**
 * Shared API step definitions — reusable across all API feature files.
 *
 * State is stored in module-level variables. Steps run sequentially
 * within a test, and Background resets state per scenario.
 */

let lastResponse = { status: 0, body: null as any, headers: {} as Record<string, string> };
let createdEntities = new Map<string, any>();

function resolvePath(path: string): string {
  return path.replace(/\{(\w+)\}/g, (_, key) => {
    const value = createdEntities.get(key);
    if (!value) return key;
    return String(value);
  });
}

function resolveField(obj: any, path: string): any {
  return path.split('.').reduce((acc, key) => acc?.[key], obj);
}

// ── Given ──

Given(
  'a user exists with name {string} and email {string}',
  async ({ request }, name: string, email: string) => {
    createdEntities = new Map();
    lastResponse = { status: 0, body: null, headers: {} };
    const response = await request.post('/api/users', {
      data: { name, email, role: 'user', password: 'TestPass123!' },
    });
    const body = await response.json();
    createdEntities.set('userId', body.id);
  },
);

// ── When: HTTP methods ──

When(
  'I send a POST request to {string} with body:',
  async ({ request }, path: string, docString: string) => {
    const resolvedPath = resolvePath(path);
    const response = await request.post(resolvedPath, {
      data: JSON.parse(docString),
    });
    lastResponse = {
      status: response.status(),
      body: await response.json().catch(() => null),
      headers: response.headers(),
    };
    if (lastResponse.body?.id) {
      createdEntities.set('userId', lastResponse.body.id);
    }
  },
);

When('I send a GET request to {string}', async ({ request }, path: string) => {
  const resolvedPath = resolvePath(path);
  const response = await request.get(resolvedPath);
  lastResponse = {
    status: response.status(),
    body: await response.json().catch(() => null),
    headers: response.headers(),
  };
});

When(
  'I send a PUT request to {string} with body:',
  async ({ request }, path: string, docString: string) => {
    const resolvedPath = resolvePath(path);
    const response = await request.put(resolvedPath, {
      data: JSON.parse(docString),
    });
    lastResponse = {
      status: response.status(),
      body: await response.json().catch(() => null),
      headers: response.headers(),
    };
  },
);

When('I send a DELETE request to {string}', async ({ request }, path: string) => {
  const resolvedPath = resolvePath(path);
  const response = await request.delete(resolvedPath);
  lastResponse = {
    status: response.status(),
    body: await response.json().catch(() => null),
    headers: response.headers(),
  };
});

// ── Then: Assertions ──

Then('the response status should be {int}', async ({}, expectedStatus: number) => {
  expect(lastResponse.status).toBe(expectedStatus);
});

Then('the response body should contain {string}', async ({}, field: string) => {
  expect(lastResponse.body).toHaveProperty(field);
});

Then('the response body {string} should equal {string}', async ({}, field: string, expected: string) => {
  expect(String(resolveField(lastResponse.body, field))).toBe(expected);
});

Then('the response body {string} should not contain {string}', async ({}, field: string, substring: string) => {
  const value = String(resolveField(lastResponse.body, field));
  expect(value).not.toContain(substring);
});

Then('the response error code should be {string}', async ({}, expectedCode: string) => {
  expect(lastResponse.body?.code ?? lastResponse.body?.error?.code).toBe(expectedCode);
});
