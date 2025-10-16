import { test, expect } from '@playwright/test';

test.describe('Workflow UI Refresh Actions', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/workflows/12');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('[data-testid="workflow-detail"]')).toBeVisible();
  });

  test('should refresh PR & Checks', async ({ page }) => {
    await page.getByRole('tab', { name: 'PR & Checks' }).click();
    const hasButton = await page.locator('button:has-text("Refresh PR & Checks")').count();
    if (hasButton) {
      await page.click('button:has-text("Refresh PR & Checks")');
      await expect(page.locator('.p-toast-message').last()).toContainText(/Refreshed|updated|Refresh/);
    }
  });

  test('should refresh Code Diffs', async ({ page }) => {
    await page.getByRole('tab', { name: 'Code Diffs' }).click();
    const hasButton = await page.locator('button:has-text("Refresh Diffs")').count();
    if (hasButton) {
      await page.click('button:has-text("Refresh Diffs")');
      await expect(page.locator('.p-toast-message').last()).toContainText(/Refreshed|updated|Refresh/);
    }
  });

  test('should refresh Artifacts', async ({ page }) => {
    await page.getByRole('tab', { name: 'Artifacts' }).click();
    const hasButton = await page.locator('button:has-text("Refresh Artifacts")').count();
    if (hasButton) {
      await page.click('button:has-text("Refresh Artifacts")');
      await expect(page.locator('.p-toast-message').last()).toContainText(/Refreshed|updated|Refresh/);
    }
  });
});


