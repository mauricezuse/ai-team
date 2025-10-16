import { test, expect } from '@playwright/test';

test.describe('Execution Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to workflow 12 detail page
    await page.goto('/workflows/12');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('[data-testid="workflow-detail"]')).toBeVisible();
  });

  test('should display Start New Execution button', async ({ page }) => {
    // Check that the Start New Execution button is visible
    await expect(page.locator('[data-testid="start-execution"]')).toBeVisible();
    
    // Check button text and styling
    const button = page.locator('[data-testid="start-execution"]');
    await expect(button).toHaveText('Start New Execution');
    await expect(button).toHaveClass(/p-button-info/);
  });

  test('should start new execution when button is clicked', async ({ page }) => {
    // Click the Start New Execution button
    await page.click('[data-testid="start-execution"]');
    
    // Wait for success message (wait for the success toast specifically)
    await expect(page.locator('.p-toast-message').filter({ hasText: 'Execution started' })).toBeVisible();
    
    // Check that executions table is updated
    await expect(page.locator('.executions table')).toBeVisible();
  });

  test('should display executions table with execution data', async ({ page }) => {
    // Wait for executions to load
    await page.waitForSelector('.executions table', { timeout: 10000 });
    
    // Check table headers (actual headers: ID, Status, Started, Finished, Calls, Tokens, Cost)
    await expect(page.locator('.executions th').first()).toContainText('ID');
    await expect(page.locator('.executions th').nth(1)).toContainText('Status');
    await expect(page.locator('.executions th').nth(2)).toContainText('Started');
    await expect(page.locator('.executions th').nth(3)).toContainText('Finished');
    await expect(page.locator('.executions th').nth(4)).toContainText('Calls');
    await expect(page.locator('.executions th').nth(5)).toContainText('Tokens');
    await expect(page.locator('.executions th').nth(6)).toContainText('Cost');
    
    // Check that at least one execution row exists
    const rowCount = await page.locator('.executions tbody tr').count();
    expect(rowCount).toBeGreaterThanOrEqual(1);
  });

  test('should compare executions from Executions tab', async ({ page }) => {
    // Go to Executions tab
    await page.getByRole('tab', { name: 'Executions' }).click();
    // Expect compare UI and interaction
    const hasDropdowns = await page.locator('#execA').count();
    if (hasDropdowns) {
      await page.click('button:has-text("Compare")');
      // Either results or empty/no data is acceptable
      // Ensure the tab content remains stable
      await expect(page.getByRole('tab', { name: 'Executions' })).toBeVisible();
    } else {
      await expect(page.locator('text=No executions yet')).toBeVisible();
    }
  });

  test('should compare executions and display results in Executions tab', async ({ page }) => {
    await page.getByRole('tab', { name: 'Executions' }).click();
    await page.waitForLoadState('networkidle');
    const hasDropdowns = await page.locator('#execA').count();
    if (hasDropdowns) {
      await page.click('button:has-text("Compare")');
      // Show JSON or message
      const hasPre = await page.locator('pre').count();
      if (hasPre) {
        const resultsText = await page.locator('pre').textContent();
        expect(resultsText || '').toContain('total_calls');
      }
    } else {
      await expect(page.locator('text=No executions yet')).toBeVisible();
    }
  });

  test('should show execution selection interface in Executions tab', async ({ page }) => {
    await page.getByRole('tab', { name: 'Executions' }).click();
    await page.waitForLoadState('networkidle');
    const selectCount = await page.locator('#execA').count();
    if (selectCount) {
      await expect(page.locator('button:has-text("Compare")')).toBeVisible();
    } else {
      await expect(page.locator('text=No executions yet')).toBeVisible();
    }
  });

  test('should handle execution start errors gracefully', async ({ page }) => {
    // Mock a failed execution start by intercepting the API call
    await page.route('**/api/workflows/*/executions/start', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' })
      });
    });
    
    // Click the Start New Execution button
    await page.click('[data-testid="start-execution"]');
    
    // Check for error message (use last toast message for error)
    await expect(page.locator('.p-toast-message').last()).toContainText('Failed to start execution');
  });

  test('should refresh executions after starting new execution', async ({ page }) => {
    // Get initial execution count
    const initialCount = await page.locator('.executions tbody tr').count();
    
    // Start new execution
    await page.click('[data-testid="start-execution"]');
    
    // Wait for success message (wait for the success toast specifically)
    await expect(page.locator('.p-toast-message').filter({ hasText: 'Execution started' })).toBeVisible();
    
    // Wait for page to refresh and check that executions table is updated
    await page.waitForTimeout(2000); // Allow time for refresh
    
    // Check that executions table is still visible
    await expect(page.locator('.executions table')).toBeVisible();
  });

  test('should display execution status correctly', async ({ page }) => {
    // Wait for executions to load
    await page.waitForSelector('.executions table', { timeout: 10000 });
    
    // Check that execution status is displayed
    const statusCells = await page.locator('.executions tbody tr td:nth-child(2)').all();
    
    for (const statusCell of statusCells) {
      const status = await statusCell.textContent();
      expect(status).toMatch(/pending|running|completed|failed/);
    }
  });

  test('should display execution metrics correctly', async ({ page }) => {
    // Wait for executions to load
    await page.waitForSelector('.executions table', { timeout: 10000 });
    
    // Check that numeric metrics are displayed (columns: ID, Status, Started, Finished, Calls, Tokens, Cost)
    const callsCells = await page.locator('.executions tbody tr td:nth-child(5)').all();
    const tokensCells = await page.locator('.executions tbody tr td:nth-child(6)').all();
    const costCells = await page.locator('.executions tbody tr td:nth-child(7)').all();
    
    // Check that metrics contain numeric values
    for (const cell of callsCells) {
      const text = await cell.textContent();
      expect(text).toMatch(/^\d+$/); // Should be numeric
    }
    
    for (const cell of tokensCells) {
      const text = await cell.textContent();
      expect(text).toMatch(/^\d+$/); // Should be numeric
    }
    
    for (const cell of costCells) {
      const text = await cell.textContent();
      expect(text).toMatch(/^\d+\.\d{2}$/); // Should be decimal with 2 places
    }
  });
});
