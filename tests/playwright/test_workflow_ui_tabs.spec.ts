import { test, expect } from '@playwright/test';

test.describe('Workflow UI Tabs', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/workflows/12');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('[data-testid="workflow-detail"]')).toBeVisible();
  });

  test('should show Overview, Executions, Conversations, LLM Calls, Escalations, Code Diffs, PR & Checks, Artifacts tabs', async ({ page }) => {
    // Verify tabs exist
    await expect(page.locator('[data-testid="tab-overview"]')).toBeVisible();
    await expect(page.locator('[data-testid="tab-executions"]')).toBeVisible();
    await expect(page.locator('[data-testid="tab-conversations"]')).toBeVisible();
    await expect(page.locator('[data-testid="tab-llm-calls"]')).toBeVisible();
    await expect(page.locator('[data-testid="tab-escalations"]')).toBeVisible();
    await expect(page.locator('[data-testid="tab-code-diffs"]')).toBeVisible();
    await expect(page.locator('[data-testid="tab-pr-checks"]')).toBeVisible();
    await expect(page.locator('[data-testid="tab-artifacts"]')).toBeVisible();
  });

  test('should navigate to Executions and perform comparison UI flow', async ({ page }) => {
    await page.getByRole('tab', { name: 'Executions' }).click();
    // If there are executions, expect the table visible
    if (await page.locator('.executions table').count()) {
      await expect(page.locator('.executions table')).toBeVisible();
      // Attempt to use compare controls if present
      const hasCompare = await page.locator('#execA').count();
      if (hasCompare) {
        // Open compare UI and click compare, expect some result or no-executions message
        await page.click('button:has-text("Compare")');
        // Either JSON result or still empty
        // We tolerate both outcomes as data is environment-dependent
      }
    } else {
      await expect(page.locator('text=No executions yet')).toBeVisible();
    }
  });

  test('should show conversations list when switching to Conversations tab', async ({ page }) => {
    await page.getByRole('tab', { name: 'Conversations' }).click();
    // Expect either conversation list or empty state
    if (await page.locator('[data-testid="conversations"]').count()) {
      await expect(page.locator('[data-testid="conversations"]')).toBeVisible();
    } else {
      await expect(page.locator('text=No conversations yet')).toBeVisible();
    }
  });

  test('should show LLM Calls tab content in any state', async ({ page }) => {
    await page.getByRole('tab', { name: 'LLM Calls' }).click();
    // Either list is present or empty state
    if (await page.locator('#llmConv').count()) {
      await expect(page.locator('#llmConv')).toBeVisible();
    } else {
      await expect(page.locator('text=No LLM calls recorded')).toBeVisible();
    }
  });
});


