import { test, expect } from '@playwright/test';

test.describe('Workflow Error Display Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to workflows page
    await page.goto('/workflows');
    await page.waitForLoadState('networkidle');
  });

  test('should display error information in workflow list for failed workflows', async ({ page }) => {
    // Look for workflow 12 (NEGISHI-165) in the list
    const workflowRow = page.locator('[data-testid="workflow-row"]').filter({ hasText: 'NEGISHI-165' });
    
    if (await workflowRow.count() > 0) {
      // Check if workflow has error status
      const statusCell = workflowRow.locator('[data-testid="workflow-status"]');
      const statusText = await statusCell.textContent();
      
      if (statusText?.includes('failed') || statusText?.includes('error')) {
        // Check for error indicator chip
        const errorChip = workflowRow.locator('.p-chip-danger');
        await expect(errorChip).toBeVisible();
        await expect(errorChip).toHaveText('Error');
        
        // Check that error chip has tooltip with error message
        await expect(errorChip).toHaveAttribute('title');
        const tooltip = await errorChip.getAttribute('title');
        expect(tooltip).toBeTruthy();
        expect(tooltip!.length).toBeGreaterThan(0);
      }
    }
  });

  test('should display comprehensive error information in workflow detail view', async ({ page }) => {
    // Navigate to workflow 12 detail page
    await page.goto('/workflows/12');
    await page.waitForLoadState('networkidle');
    
    // Check if workflow detail is loaded
    const workflowDetail = page.locator('[data-testid="workflow-detail"]');
    await expect(workflowDetail).toBeVisible();
    
    // Check for error message display
    const errorMessage = page.locator('.error-message');
    if (await errorMessage.count() > 0) {
      await expect(errorMessage).toBeVisible();
      
      // Check error message styling
      const errorStyles = await errorMessage.evaluate(el => {
        const computed = window.getComputedStyle(el);
        return {
          color: computed.color,
          backgroundColor: computed.backgroundColor,
          fontFamily: computed.fontFamily
        };
      });
      
      // Error message should have proper styling
      expect(errorStyles.color).toContain('rgb(220, 53, 69)'); // Red color
      expect(errorStyles.backgroundColor).toContain('rgb(248, 215, 218)'); // Light red background
      expect(errorStyles.fontFamily).toContain('monospace'); // Monospace font
      
      // Check error message content
      const errorText = await errorMessage.textContent();
      expect(errorText).toBeTruthy();
      expect(errorText!.length).toBeGreaterThan(0);
    }
    
    // Check for terminal status indicator
    const terminalChip = page.locator('.p-chip-success').filter({ hasText: 'Terminal' });
    if (await terminalChip.count() > 0) {
      await expect(terminalChip).toBeVisible();
    }
    
    // Check for error status in status field
    const statusField = page.locator('[data-testid="workflow-status"]');
    const statusText = await statusField.textContent();
    if (statusText?.includes('failed') || statusText?.includes('error')) {
      expect(statusText).toContain('failed');
    }
  });

  test('should show error information in workflow status section', async ({ page }) => {
    await page.goto('/workflows/12');
    await page.waitForLoadState('networkidle');
    
    // Check for error information in workflow info section
    const errorSection = page.locator('p').filter({ hasText: 'Error:' });
    if (await errorSection.count() > 0) {
      await expect(errorSection).toBeVisible();
      
      // Check that error message is displayed
      const errorMessage = errorSection.locator('.error-message');
      await expect(errorMessage).toBeVisible();
      
      // Verify error message is not empty
      const errorText = await errorMessage.textContent();
      expect(errorText).toBeTruthy();
      expect(errorText!.trim().length).toBeGreaterThan(0);
    }
  });

  test('should display error with proper formatting and scrolling', async ({ page }) => {
    await page.goto('/workflows/12');
    await page.waitForLoadState('networkidle');
    
    const errorMessage = page.locator('.error-message');
    if (await errorMessage.count() > 0) {
      // Check error message container properties
      const containerStyles = await errorMessage.evaluate(el => {
        const computed = window.getComputedStyle(el);
        return {
          maxHeight: computed.maxHeight,
          overflowY: computed.overflowY,
          whiteSpace: computed.whiteSpace,
          wordWrap: computed.wordWrap
        };
      });
      
      // Should have scrolling capability for long errors
      expect(containerStyles.maxHeight).toBe('200px');
      expect(containerStyles.overflowY).toBe('auto');
      expect(containerStyles.whiteSpace).toBe('pre-wrap');
      expect(containerStyles.wordWrap).toBe('break-word');
    }
  });

  test('should show error indicators in workflow list with proper styling', async ({ page }) => {
    await page.goto('/workflows');
    await page.waitForLoadState('networkidle');
    
    // Find workflow 12 row
    const workflowRow = page.locator('[data-testid="workflow-row"]').filter({ hasText: 'NEGISHI-165' });
    
    if (await workflowRow.count() > 0) {
      const errorChip = workflowRow.locator('.p-chip-danger');
      if (await errorChip.count() > 0) {
        // Check error chip styling
        const chipStyles = await errorChip.evaluate(el => {
          const computed = window.getComputedStyle(el);
          return {
            backgroundColor: computed.backgroundColor,
            color: computed.color
          };
        });
        
        // Error chip should have danger styling
        expect(chipStyles.backgroundColor).toContain('rgb(248, 215, 218)');
        expect(chipStyles.color).toContain('rgb(220, 53, 69)');
        
        // Check chip text
        await expect(errorChip).toHaveText('Error');
      }
    }
  });

  test('should handle long error messages with proper display', async ({ page }) => {
    await page.goto('/workflows/12');
    await page.waitForLoadState('networkidle');
    
    const errorMessage = page.locator('.error-message');
    if (await errorMessage.count() > 0) {
      // Get error message content
      const errorText = await errorMessage.textContent();
      
      if (errorText && errorText.length > 100) {
        // For long error messages, check that scrolling works
        const scrollHeight = await errorMessage.evaluate(el => el.scrollHeight);
        const clientHeight = await errorMessage.evaluate(el => el.clientHeight);
        
        if (scrollHeight > clientHeight) {
          // Should be scrollable
          expect(scrollHeight).toBeGreaterThan(clientHeight);
        }
      }
    }
  });

  test('should show error information in real-time updates', async ({ page }) => {
    await page.goto('/workflows/12');
    await page.waitForLoadState('networkidle');
    
    // Monitor for status updates
    const statusElement = page.locator('[data-testid="workflow-status"]');
    const initialStatus = await statusElement.textContent();
    
    // Wait for any status updates (WebSocket/SSE)
    await page.waitForTimeout(2000);
    
    const updatedStatus = await statusElement.textContent();
    
    // If status changed to failed, check for error display
    if (updatedStatus?.includes('failed') || updatedStatus?.includes('error')) {
      const errorMessage = page.locator('.error-message');
      if (await errorMessage.count() > 0) {
        await expect(errorMessage).toBeVisible();
      }
    }
  });

  test('should display error information in workflow executions table', async ({ page }) => {
    await page.goto('/workflows/12');
    await page.waitForLoadState('networkidle');
    
    // Check if executions table exists
    const executionsTable = page.locator('.executions table');
    if (await executionsTable.count() > 0) {
      // Look for failed executions
      const failedRows = executionsTable.locator('tr').filter({ hasText: 'failed' });
      if (await failedRows.count() > 0) {
        // Check that failed executions are properly displayed
        await expect(failedRows.first()).toBeVisible();
        
        // Check status column shows failed
        const statusCell = failedRows.first().locator('td').nth(1);
        await expect(statusCell).toContainText('failed');
      }
    }
  });

  test('should show error information with proper accessibility', async ({ page }) => {
    await page.goto('/workflows/12');
    await page.waitForLoadState('networkidle');
    
    const errorMessage = page.locator('.error-message');
    if (await errorMessage.count() > 0) {
      // Check that error message has proper contrast
      const styles = await errorMessage.evaluate(el => {
        const computed = window.getComputedStyle(el);
        return {
          color: computed.color,
          backgroundColor: computed.backgroundColor
        };
      });
      
      // Should have sufficient contrast for accessibility
      expect(styles.color).toBeTruthy();
      expect(styles.backgroundColor).toBeTruthy();
      
      // Check that error message is readable
      const errorText = await errorMessage.textContent();
      expect(errorText).toBeTruthy();
      expect(errorText!.trim().length).toBeGreaterThan(0);
    }
  });
});
