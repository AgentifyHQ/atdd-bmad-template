import { expect } from '@playwright/test';
import { createBdd } from 'playwright-bdd';

const { Given, When, Then } = createBdd();

// ── Background ──

Given('a registered user exists with email {string}', async ({ request }, email: string) => {
  await request.post('/api/test/seed-user', {
    data: { email, password: 'ValidPassword123!', name: 'Test User' },
  });
});

// ── Given ──

Given('I am on the login page', async ({ page }) => {
  await page.goto('/login');
  await expect(page).toHaveURL(/\/login/);
});

// ── When ──

When('I enter email {string}', async ({ page }, email: string) => {
  await page.getByLabel('Email').fill(email);
});

When('I enter password {string}', async ({ page }, password: string) => {
  await page.getByLabel('Password').fill(password);
});

When('I click the login button', async ({ page }) => {
  const responsePromise = page.waitForResponse(
    (resp) => resp.url().includes('/api/auth') && resp.request().method() === 'POST',
    { timeout: 5000 },
  ).catch(() => null);

  await page.getByRole('button', { name: /log in|sign in/i }).click();
  await responsePromise;
});

// ── Then ──

Then('I should be redirected to the dashboard', async ({ page }) => {
  await expect(page).toHaveURL(/\/dashboard/);
});

Then('I should see a welcome message containing my name', async ({ page }) => {
  await expect(page.getByText(/welcome/i)).toBeVisible();
});

Then('I should see an error message {string}', async ({ page }, message: string) => {
  await expect(page.getByText(message)).toBeVisible();
});

Then('I should remain on the login page', async ({ page }) => {
  await expect(page).toHaveURL(/\/login/);
});

Then('I should see a validation error for {string}', async ({ page }, field: string) => {
  const fieldLocator = page.getByLabel(new RegExp(field, 'i'));
  await expect(fieldLocator).toHaveAttribute('aria-invalid', 'true');
});
