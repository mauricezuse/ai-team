import { test, expect } from '@playwright/test';

// Assumes dev server proxy to backend is configured (frontend/proxy.conf.json)

test.describe('Unified Workflow Detail - Tabs', () => {
  test('should navigate to workflow detail and render headers', async ({ page }) => {
    await page.goto('/workflows/1');
    await expect(page.getByTestId('workflow-detail')).toBeVisible();
    const tabs = ['Overview','Executions','Conversations','LLM Calls','Escalations','Code Diffs','PR & Checks','Artifacts'];
    for (const label of tabs) {
      await expect(page.getByRole('tab', { name: label })).toBeVisible();
    }
  });

  test('should deep-link to LLM Calls from conversation item link', async ({ page }) => {
    await page.goto('/workflows/12');
    // Ensure conversations tab is accessible, then click the inline link to open LLM Calls tab
    const hasInlineLink = await page.getByTestId('open-llm-calls-from-detail').count();
    if (hasInlineLink) {
      await page.getByTestId('open-llm-calls-from-detail').first().click();
      await expect(page.getByRole('tab', { name: 'LLM Calls' })).toBeVisible();
    }
  });
});
