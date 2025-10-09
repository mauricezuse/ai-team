import { test, expect } from '@playwright/test';

test.describe('Agents Management', () => {
  test('should display agents list', async ({ page }) => {
    await page.goto('/agents');
    await expect(page.getByText('Agents')).toBeVisible();
  });
});
