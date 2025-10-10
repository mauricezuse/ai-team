import { test, expect } from '@playwright/test';

test.describe('Unified Workflow 12 UI', () => {
  test('should load workflow 12 detail page', async ({ page }) => {
    await page.goto('/workflows/12');
    await expect(page.getByTestId('workflow-title')).toBeVisible();
  });

  test('should open LLM Calls tab from inline link', async ({ page }) => {
    await page.goto('/workflows/12');
    const link = page.getByTestId('open-llm-calls-from-detail').first();
    if (await link.count()) {
      await link.click();
      await expect(page.getByRole('tab', { name: 'LLM Calls' })).toBeVisible();
    }
  });
});


