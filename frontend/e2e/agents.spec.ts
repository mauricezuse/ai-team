import { test, expect } from '@playwright/test';

test.describe('Agents Management', () => {
  test('should display agents list and add agent', async ({ page }) => {
    await page.goto('/agents');
    await expect(page.getByText('Add Agent')).toBeVisible();

    await page.getByText('Add Agent').click();
    await page.getByLabel('Name').fill('Test Agent');
    await page.getByLabel('Role').fill('Architect');
    await page.getByLabel('Goal').fill('Design systems');
    await page.getByText('Save').click();

    await expect(page.getByText('Test Agent')).toBeVisible();
  });
});
