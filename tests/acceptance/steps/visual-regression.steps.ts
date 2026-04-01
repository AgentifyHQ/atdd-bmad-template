import { expect } from '@playwright/test';
import { createBdd } from 'playwright-bdd';

const { Then } = createBdd();

/**
 * Visual regression step definitions.
 *
 * Baselines are stored in __snapshots__/ next to the generated test files.
 * First run: baseline is created, test fails (review and commit the baseline).
 * Subsequent runs: screenshot compared against baseline.
 *
 * Update baselines: npx playwright test --update-snapshots
 *
 * Reports:
 * - Playwright HTML report (reports/playwright/) shows interactive side-by-side
 *   slider with expected/actual/diff images — best for visual review.
 * - Living docs show pass/fail status on the scenario.
 */

Then(
  'the page should match the visual baseline {string}',
  async ({ page }, baselineName: string) => {
    // Wait for visual stability
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveScreenshot(`${baselineName}.png`, {
      maxDiffPixelRatio: 0.01,
      animations: 'disabled',
      fullPage: true,
    });
  },
);

Then(
  'the page should match the visual baseline {string} with masked:',
  async ({ page }, baselineName: string, dataTable: any) => {
    // Wait for visual stability
    await page.waitForLoadState('networkidle');

    // Build mask array from data table
    const rows: string[][] = dataTable.rows();
    const mask = rows.map((row: string[]) => page.locator(row[0]));

    await expect(page).toHaveScreenshot(`${baselineName}.png`, {
      maxDiffPixelRatio: 0.01,
      animations: 'disabled',
      fullPage: true,
      mask,
    });
  },
);

Then(
  'the element {string} should match the visual baseline {string}',
  async ({ page }, selector: string, baselineName: string) => {
    await page.waitForLoadState('networkidle');

    await expect(page.locator(selector)).toHaveScreenshot(`${baselineName}.png`, {
      maxDiffPixelRatio: 0.01,
      animations: 'disabled',
    });
  },
);
