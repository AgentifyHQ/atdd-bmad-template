import 'dotenv/config';
import { defineConfig, devices } from '@playwright/test';
import { defineBddConfig, cucumberReporter } from 'playwright-bdd';

// ──────────────────────────────────────────────
// BDD Config per project — each gets its own
// feature files, steps, and generated output dir
// ──────────────────────────────────────────────

const acceptanceTestDir = defineBddConfig({
  outputDir: 'reports/.features-gen/acceptance',
  features: 'features/acceptance/**/*.feature',
  steps: 'tests/acceptance/steps/**/*.ts',
});

const apiTestDir = defineBddConfig({
  outputDir: 'reports/.features-gen/api',
  features: 'features/api/**/*.feature',
  steps: 'tests/api/steps/**/*.ts',
});

const integrationTestDir = defineBddConfig({
  outputDir: 'reports/.features-gen/integration',
  features: 'features/integration/**/*.feature',
  steps: 'tests/integration/steps/**/*.ts',
});

const promptEvalTestDir = defineBddConfig({
  outputDir: 'reports/.features-gen/prompt-eval',
  features: 'features/prompt-eval/**/*.feature',
  steps: 'tests/prompt-eval/ts-steps/**/*.ts',
});

export default defineConfig({
  // ──────────────────────────────────────────
  // Global defaults
  // ──────────────────────────────────────────
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,

  // ──────────────────────────────────────────
  // Output directories — all under reports/
  // ──────────────────────────────────────────
  outputDir: 'reports/test-results',

  // ──────────────────────────────────────────
  // Reporters — Playwright HTML + Cucumber living docs
  // ──────────────────────────────────────────
  reporter: [
    ['html', { open: 'never', outputFolder: 'reports/playwright' }],
    cucumberReporter('html', {
      outputFile: 'reports/cucumber/index.html',
    }),
    cucumberReporter('json', {
      outputFile: 'reports/cucumber/report.json',
    }),
  ],

  // ──────────────────────────────────────────
  // Projects
  // ──────────────────────────────────────────
  projects: [
    // ── UI Acceptance (browser-based BDD) ──
    {
      name: 'acceptance',
      testDir: acceptanceTestDir,
      use: {
        baseURL: process.env.APP_URL || 'http://localhost:3000',
        ...devices['Desktop Chrome'],
        screenshot: 'only-on-failure',
        trace: 'on-first-retry',
        video: 'on-first-retry',
      },
    },

    // ── API Tests (no browser, BDD) ──
    {
      name: 'api',
      testDir: apiTestDir,
      use: {
        baseURL: process.env.API_URL || 'http://localhost:3000',
        extraHTTPHeaders: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
        },
      },
      timeout: 30_000,
    },

    // ── System Integration (no browser, BDD) ──
    {
      name: 'integration',
      testDir: integrationTestDir,
      use: {
        baseURL: process.env.API_URL || 'http://localhost:3000',
        extraHTTPHeaders: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
        },
      },
      timeout: 45_000,
    },

    // ── Prompt Evaluation (no browser, BDD via promptfoo API) ──
    {
      name: 'prompt-eval',
      testDir: promptEvalTestDir,
      use: {
        baseURL: process.env.LLM_ENDPOINT || 'https://api.anthropic.com',
      },
      timeout: 120_000,
    },
  ],
});
