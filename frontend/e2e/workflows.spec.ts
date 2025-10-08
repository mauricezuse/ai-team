import { test, expect } from '@playwright/test';

test.describe('Workflows Management', () => {
  test('should display workflows list and add workflow', async ({ page }) => {
    await page.goto('/workflows');
    await expect(page.getByText('Add Workflow')).toBeVisible();

    await page.getByText('Add Workflow').click();
    await page.getByLabel('Name').fill('Test Workflow');
    await page.getByText('Save').click();

    await expect(page.getByText('Test Workflow')).toBeVisible();
  });
});
