import { test as base, mergeTests } from '@playwright/test';
import { test as bddBase } from 'playwright-bdd';

/**
 * Base fixtures shared across all test layers.
 * Extend this with layer-specific fixtures using mergeTests.
 */
export const test = base.extend<{
  /**
   * Unique test run ID for data isolation.
   * Use this to namespace test data and prevent cross-test pollution.
   */
  testRunId: string;
}>({
  testRunId: async ({}, use) => {
    const id = `test-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    await use(id);
  },
});

export { expect } from '@playwright/test';
export { mergeTests };
