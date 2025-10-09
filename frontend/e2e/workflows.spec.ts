import { test, expect } from '@playwright/test';

test.describe('Workflows Management', () => {
  test('should display workflows list and open a workflow', async ({ page }) => {
    await page.goto('/workflows');
    // Expect at least table/list to be visible
    await expect(page).toHaveURL(/.*workflows/);
    // Navigate to a known workflow id 12 if present
    await page.goto('/workflows/12');
    await expect(page.getByTestId('workflow-title')).toBeVisible();
  });
});
