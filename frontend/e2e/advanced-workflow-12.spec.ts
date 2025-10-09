import { test, expect } from '@playwright/test';

test.describe('Advanced Workflow 12 UI', () => {
  test('should load workflow 12 detail page', async ({ page }) => {
    await page.goto('/workflows/12');
    await expect(page.getByTestId('workflow-title')).toBeVisible();
    await expect(page.getByTestId('conversations')).toBeVisible({ timeout: 5000 });
  });

  test('should open advanced timeline for workflow 12', async ({ page }) => {
    await page.goto('/workflows/12/advanced');
    await expect(page.getByTestId('advanced-workflow-timeline')).toBeVisible();
  });

  test('should open llm calls table route (if conversation param provided)', async ({ page }) => {
    await page.goto('/workflows/12/advanced');
    const link = page.getByTestId('open-llm-calls').first();
    await link.click();
    await expect(page.getByTestId('llm-calls-table')).toBeVisible();
    await expect(page.locator('table')).toBeVisible();
    // URL should include conversationId
    await expect(page).toHaveURL(/conversationId=/);
  });
  
  test('should show empty-state when conversationId missing', async ({ page }) => {
    await page.goto('/workflows/12/advanced/llm-calls');
    await expect(page.getByText('No conversation selected')).toBeVisible();
  });

  test('prompt viewer should display latest request/response for conversation', async ({ page }) => {
    await page.goto('/workflows/12/advanced');
    const link = page.getByTestId('open-prompt-viewer').first();
    await link.click();
    await expect(page.getByTestId('prompt-output-viewer')).toBeVisible();
    await expect(page).toHaveURL(/conversationId=/);
  });
});


