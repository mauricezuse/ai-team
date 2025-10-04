import { test, expect } from '@playwright/test';

test.describe('Workflow Creation Error Scenarios', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to workflows page
    await page.goto('/workflows');
    await page.waitForLoadState('networkidle');
  });

  test('should handle backend server unavailable', async ({ page }) => {
    // Mock server unavailable response
    await page.route('**/api/workflows/from-jira/NEGISHI-165', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 503,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: 'Service unavailable'
          })
        });
      }
    });

    // Click the "Create from Jira" button
    await page.getByTestId('create-from-jira-button').click();
    
    // Fill in the Jira story ID
    await page.fill('input[placeholder*="Jira Story ID"]', 'NEGISHI-165');
    await page.keyboard.press('Enter');
    
    // Wait for error message
    await expect(page.getByText('Service unavailable')).toBeVisible();
  });

  test('should handle database connection error', async ({ page }) => {
    // Mock database connection error
    await page.route('**/api/workflows/from-jira/NEGISHI-165', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: 'Database connection failed'
          })
        });
      }
    });

    // Click the "Create from Jira" button
    await page.getByTestId('create-from-jira-button').click();
    
    // Fill in the Jira story ID
    await page.fill('input[placeholder*="Jira Story ID"]', 'NEGISHI-165');
    await page.keyboard.press('Enter');
    
    // Wait for error message
    await expect(page.getByText('Database connection failed')).toBeVisible();
  });

  test('should handle Jira API rate limiting', async ({ page }) => {
    // Mock rate limiting response
    await page.route('**/api/workflows/from-jira/NEGISHI-165', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 429,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: 'Rate limit exceeded. Please try again later.'
          })
        });
      }
    });

    // Click the "Create from Jira" button
    await page.getByTestId('create-from-jira-button').click();
    
    // Fill in the Jira story ID
    await page.fill('input[placeholder*="Jira Story ID"]', 'NEGISHI-165');
    await page.keyboard.press('Enter');
    
    // Wait for error message
    await expect(page.getByText('Rate limit exceeded. Please try again later.')).toBeVisible();
  });

  test('should handle Jira authentication failure', async ({ page }) => {
    // Mock authentication failure
    await page.route('**/api/workflows/from-jira/NEGISHI-165', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: 'Jira authentication failed'
          })
        });
      }
    });

    // Click the "Create from Jira" button
    await page.getByTestId('create-from-jira-button').click();
    
    // Fill in the Jira story ID
    await page.fill('input[placeholder*="Jira Story ID"]', 'NEGISHI-165');
    await page.keyboard.press('Enter');
    
    // Wait for error message
    await expect(page.getByText('Jira authentication failed')).toBeVisible();
  });

  test('should handle Jira permission denied', async ({ page }) => {
    // Mock permission denied response
    await page.route('**/api/workflows/from-jira/NEGISHI-165', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 403,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: 'Permission denied to access Jira story'
          })
        });
      }
    });

    // Click the "Create from Jira" button
    await page.getByTestId('create-from-jira-button').click();
    
    // Fill in the Jira story ID
    await page.fill('input[placeholder*="Jira Story ID"]', 'NEGISHI-165');
    await page.keyboard.press('Enter');
    
    // Wait for error message
    await expect(page.getByText('Permission denied to access Jira story')).toBeVisible();
  });

  test('should handle invalid Jira story ID format', async ({ page }) => {
    // Click the "Create from Jira" button
    await page.getByTestId('create-from-jira-button').click();
    
    // Try various invalid formats
    const invalidIds = [
      'invalid-id',
      '123',
      'NEGISHI',
      'NEGISHI-',
      '-123',
      'NEGISHI-abc',
      'negishi-123',
      'NEGISHI-123-extra'
    ];

    for (const invalidId of invalidIds) {
      await page.fill('input[placeholder*="Jira Story ID"]', invalidId);
      await page.keyboard.press('Enter');
      
      // Should show validation error
      await expect(page.getByText('Invalid Jira story ID format')).toBeVisible();
      
      // Clear the input for next test
      await page.fill('input[placeholder*="Jira Story ID"]', '');
    }
  });

  test('should handle very long Jira story ID', async ({ page }) => {
    // Click the "Create from Jira" button
    await page.getByTestId('create-from-jira-button').click();
    
    // Try with very long story ID
    const longId = 'NEGISHI-' + '1'.repeat(100);
    await page.fill('input[placeholder*="Jira Story ID"]', longId);
    await page.keyboard.press('Enter');
    
    // Should show validation error
    await expect(page.getByText('Jira story ID is too long')).toBeVisible();
  });

  test('should handle special characters in Jira story ID', async ({ page }) => {
    // Click the "Create from Jira" button
    await page.getByTestId('create-from-jira-button').click();
    
    // Try with special characters
    const specialChars = [
      'NEGISHI-123!',
      'NEGISHI-123@',
      'NEGISHI-123#',
      'NEGISHI-123$',
      'NEGISHI-123%',
      'NEGISHI-123^',
      'NEGISHI-123&',
      'NEGISHI-123*',
      'NEGISHI-123(',
      'NEGISHI-123)',
      'NEGISHI-123[',
      'NEGISHI-123]',
      'NEGISHI-123{',
      'NEGISHI-123}',
      'NEGISHI-123|',
      'NEGISHI-123\\',
      'NEGISHI-123/',
      'NEGISHI-123<',
      'NEGISHI-123>',
      'NEGISHI-123,',
      'NEGISHI-123.',
      'NEGISHI-123?',
      'NEGISHI-123;',
      'NEGISHI-123:',
      'NEGISHI-123"',
      'NEGISHI-123\'',
      'NEGISHI-123`',
      'NEGISHI-123~'
    ];

    for (const specialId of specialChars) {
      await page.fill('input[placeholder*="Jira Story ID"]', specialId);
      await page.keyboard.press('Enter');
      
      // Should show validation error
      await expect(page.getByText('Invalid Jira story ID format')).toBeVisible();
      
      // Clear the input for next test
      await page.fill('input[placeholder*="Jira Story ID"]', '');
    }
  });

  test('should handle empty and whitespace-only Jira story ID', async ({ page }) => {
    // Click the "Create from Jira" button
    await page.getByTestId('create-from-jira-button').click();
    
    // Try with empty string
    await page.fill('input[placeholder*="Jira Story ID"]', '');
    await page.keyboard.press('Enter');
    
    // Should not make API call
    await expect(page.getByText('Workflow created successfully')).not.toBeVisible();
    
    // Try with whitespace only
    await page.fill('input[placeholder*="Jira Story ID"]', '   ');
    await page.keyboard.press('Enter');
    
    // Should not make API call
    await expect(page.getByText('Workflow created successfully')).not.toBeVisible();
    
    // Try with tabs and newlines
    await page.fill('input[placeholder*="Jira Story ID"]', '\t\n\r');
    await page.keyboard.press('Enter');
    
    // Should not make API call
    await expect(page.getByText('Workflow created successfully')).not.toBeVisible();
  });

  test('should handle concurrent Jira workflow creation requests', async ({ page }) => {
    // Mock slow API response
    await page.route('**/api/workflows/from-jira/NEGISHI-165', async (route) => {
      if (route.request().method() === 'POST') {
        // Add delay to simulate slow response
        await new Promise(resolve => setTimeout(resolve, 2000));
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            message: 'Workflow created successfully for NEGISHI-165',
            workflow_id: 3,
            story_id: 'NEGISHI-165',
            title: 'Implement advanced user authentication system'
          })
        });
      }
    });

    // Click the "Create from Jira" button
    await page.getByTestId('create-from-jira-button').click();
    
    // Fill in the Jira story ID
    await page.fill('input[placeholder*="Jira Story ID"]', 'NEGISHI-165');
    await page.keyboard.press('Enter');
    
    // Try to create another workflow while the first one is processing
    await page.getByTestId('create-from-jira-button').click();
    await page.fill('input[placeholder*="Jira Story ID"]', 'NEGISHI-166');
    await page.keyboard.press('Enter');
    
    // Should show error about concurrent requests
    await expect(page.getByText('Please wait for the current request to complete')).toBeVisible();
  });

  test('should handle network interruption during creation', async ({ page }) => {
    // Mock network interruption
    await page.route('**/api/workflows/from-jira/NEGISHI-165', async (route) => {
      if (route.request().method() === 'POST') {
        // Simulate network interruption by not fulfilling the request
        await new Promise(resolve => setTimeout(resolve, 100));
        // Don't fulfill the request to simulate network failure
      }
    });

    // Click the "Create from Jira" button
    await page.getByTestId('create-from-jira-button').click();
    
    // Fill in the Jira story ID
    await page.fill('input[placeholder*="Jira Story ID"]', 'NEGISHI-165');
    await page.keyboard.press('Enter');
    
    // Wait for network error
    await expect(page.getByText('Network error occurred')).toBeVisible();
  });

  test('should handle malformed response from backend', async ({ page }) => {
    // Mock malformed response
    await page.route('**/api/workflows/from-jira/NEGISHI-165', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: 'invalid json{'
        });
      }
    });

    // Click the "Create from Jira" button
    await page.getByTestId('create-from-jira-button').click();
    
    // Fill in the Jira story ID
    await page.fill('input[placeholder*="Jira Story ID"]', 'NEGISHI-165');
    await page.keyboard.press('Enter');
    
    // Wait for parsing error
    await expect(page.getByText('Failed to parse response')).toBeVisible();
  });

  test('should handle missing required fields in response', async ({ page }) => {
    // Mock response with missing fields
    await page.route('**/api/workflows/from-jira/NEGISHI-165', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            // Missing required fields
            workflow_id: 3
          })
        });
      }
    });

    // Click the "Create from Jira" button
    await page.getByTestId('create-from-jira-button').click();
    
    // Fill in the Jira story ID
    await page.fill('input[placeholder*="Jira Story ID"]', 'NEGISHI-165');
    await page.keyboard.press('Enter');
    
    // Wait for validation error
    await expect(page.getByText('Invalid response format')).toBeVisible();
  });

  test('should handle very large response from backend', async ({ page }) => {
    // Mock very large response
    const largeResponse = {
      message: 'Workflow created successfully for NEGISHI-165',
      workflow_id: 3,
      story_id: 'NEGISHI-165',
      title: 'Implement advanced user authentication system',
      description: 'A'.repeat(1000000) // 1MB of data
    };

    await page.route('**/api/workflows/from-jira/NEGISHI-165', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(largeResponse)
        });
      }
    });

    // Click the "Create from Jira" button
    await page.getByTestId('create-from-jira-button').click();
    
    // Fill in the Jira story ID
    await page.fill('input[placeholder*="Jira Story ID"]', 'NEGISHI-165');
    await page.keyboard.press('Enter');
    
    // Should handle large response gracefully
    await expect(page.getByText('Workflow created successfully for NEGISHI-165')).toBeVisible();
  });
});
