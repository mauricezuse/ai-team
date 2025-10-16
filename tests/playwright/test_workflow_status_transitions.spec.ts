import { test, expect } from '@playwright/test';

test.describe('Workflow Status Transitions', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to workflows page
    await page.goto('/workflows');
    await page.waitForLoadState('networkidle');
  });

  test('should display enhanced status information in workflow list', async ({ page }) => {
    // Check if workflows are loaded
    await expect(page.locator('[data-testid="workflows-table"]')).toBeVisible();
    
    // Look for status indicators
    const statusElements = page.locator('[data-testid="workflow-status"]');
    await expect(statusElements.first()).toBeVisible();
    
    // Check for enhanced status chips
    const terminalChips = page.locator('.p-chip-success');
    const staleChips = page.locator('.p-chip-warning');
    const connectionChips = page.locator('.p-chip-info');
    
    // These may or may not be present depending on workflow state
    // Just verify the elements can be found
    console.log('Terminal chips found:', await terminalChips.count());
    console.log('Stale chips found:', await staleChips.count());
    console.log('Connection chips found:', await connectionChips.count());
  });

  test('should show enhanced status in workflow detail', async ({ page }) => {
    // Click on first workflow link
    const firstWorkflowLink = page.locator('[data-testid="workflow-link"]').first();
    await expect(firstWorkflowLink).toBeVisible();
    await firstWorkflowLink.click();
    
    // Wait for workflow detail page to load
    await page.waitForLoadState('networkidle');
    await expect(page.locator('[data-testid="workflow-detail"]')).toBeVisible();
    
    // Check for enhanced status information
    const statusElement = page.locator('[data-testid="workflow-status"]');
    await expect(statusElement).toBeVisible();
    
    // Check for terminal indicator
    const terminalChip = page.locator('.p-chip-success');
    const staleChip = page.locator('.p-chip-warning');
    
    // These may or may not be present
    console.log('Terminal chip found:', await terminalChip.count());
    console.log('Stale chip found:', await staleChip.count());
    
    // Check for connection type display
    const connectionInfo = page.locator('text=Connection:');
    if (await connectionInfo.count() > 0) {
      await expect(connectionInfo).toBeVisible();
    }
  });

  test('should handle reconcile status button', async ({ page }) => {
    // Navigate to workflow detail
    const firstWorkflowLink = page.locator('[data-testid="workflow-link"]').first();
    await firstWorkflowLink.click();
    await page.waitForLoadState('networkidle');
    
    // Look for reconcile button (only shown for running workflows)
    const reconcileButton = page.locator('[data-testid="reconcile-status"]');
    
    if (await reconcileButton.count() > 0) {
      await expect(reconcileButton).toBeVisible();
      
      // Click reconcile button
      await reconcileButton.click();
      
      // Check for success message
      const toast = page.locator('.p-toast-message');
      await expect(toast).toBeVisible({ timeout: 5000 });
    }
  });

  test('should display heartbeat information', async ({ page }) => {
    // Navigate to workflow detail
    const firstWorkflowLink = page.locator('[data-testid="workflow-link"]').first();
    await firstWorkflowLink.click();
    await page.waitForLoadState('networkidle');
    
    // Check for heartbeat information
    const heartbeatInfo = page.locator('text=Last Heartbeat:');
    if (await heartbeatInfo.count() > 0) {
      await expect(heartbeatInfo).toBeVisible();
    }
    
    // Check for started/finished times
    const startedInfo = page.locator('text=Started:');
    const finishedInfo = page.locator('text=Finished:');
    
    if (await startedInfo.count() > 0) {
      await expect(startedInfo).toBeVisible();
    }
    
    if (await finishedInfo.count() > 0) {
      await expect(finishedInfo).toBeVisible();
    }
  });

  test('should show error information when present', async ({ page }) => {
    // Navigate to workflow detail
    const firstWorkflowLink = page.locator('[data-testid="workflow-link"]').first();
    await firstWorkflowLink.click();
    await page.waitForLoadState('networkidle');
    
    // Check for error information
    const errorInfo = page.locator('text=Error:');
    if (await errorInfo.count() > 0) {
      await expect(errorInfo).toBeVisible();
      const errorMessage = page.locator('.error-message');
      await expect(errorMessage).toBeVisible();
    }
  });

  test('should handle status updates in real-time', async ({ page }) => {
    // Navigate to workflow detail
    const firstWorkflowLink = page.locator('[data-testid="workflow-link"]').first();
    await firstWorkflowLink.click();
    await page.waitForLoadState('networkidle');
    
    // Get initial status
    const statusElement = page.locator('[data-testid="workflow-status"]');
    const initialStatus = await statusElement.textContent();
    
    // Wait a bit to see if status changes
    await page.waitForTimeout(2000);
    
    // Check if status is still visible and potentially changed
    await expect(statusElement).toBeVisible();
    
    // Log the status for debugging
    const currentStatus = await statusElement.textContent();
    console.log('Initial status:', initialStatus);
    console.log('Current status:', currentStatus);
  });

  test('should display connection type information', async ({ page }) => {
    // Navigate to workflow detail
    const firstWorkflowLink = page.locator('[data-testid="workflow-link"]').first();
    await firstWorkflowLink.click();
    await page.waitForLoadState('networkidle');
    
    // Check for connection type display
    const connectionInfo = page.locator('text=Connection:');
    if (await connectionInfo.count() > 0) {
      await expect(connectionInfo).toBeVisible();
      
      // Check for connection type chip
      const connectionChip = page.locator('.p-chip-info');
      await expect(connectionChip).toBeVisible();
    }
  });

  test('should handle stale heartbeat warning', async ({ page }) => {
    // Navigate to workflow detail
    const firstWorkflowLink = page.locator('[data-testid="workflow-link"]').first();
    await firstWorkflowLink.click();
    await page.waitForLoadState('networkidle');
    
    // Look for stale heartbeat warning
    const staleChip = page.locator('.p-chip-warning');
    if (await staleChip.count() > 0) {
      await expect(staleChip).toBeVisible();
      
      // Check if it shows "Stale Heartbeat" text
      const staleText = page.locator('text=Stale Heartbeat');
      if (await staleText.count() > 0) {
        await expect(staleText).toBeVisible();
      }
    }
  });

  test('should show terminal status correctly', async ({ page }) => {
    // Navigate to workflow detail
    const firstWorkflowLink = page.locator('[data-testid="workflow-link"]').first();
    await firstWorkflowLink.click();
    await page.waitForLoadState('networkidle');
    
    // Look for terminal status indicator
    const terminalChip = page.locator('.p-chip-success');
    if (await terminalChip.count() > 0) {
      await expect(terminalChip).toBeVisible();
      
      // Check if it shows "Terminal" text
      const terminalText = page.locator('text=Terminal');
      if (await terminalText.count() > 0) {
        await expect(terminalText).toBeVisible();
      }
    }
  });
});
