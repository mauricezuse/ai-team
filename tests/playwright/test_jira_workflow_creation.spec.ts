import { test, expect } from '@playwright/test';

test.describe('Jira Workflow Creation', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API responses for workflows
    await page.route('**/api/workflows', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              id: 1,
              name: 'NEGISHI-178: Federation-aware agents',
              jira_story_id: 'NEGISHI-178',
              status: 'completed',
              created_at: '2025-10-02T21:21:21.064373',
              updated_at: '2025-10-02T21:21:21.064377',
              repository_url: 'https://github.com/mauricezuse/negishi-freelancing',
              target_branch: 'main',
              agents: []
            },
            {
              id: 2,
              name: 'NEGISHI-175: Intelligent code modifications',
              jira_story_id: 'NEGISHI-175',
              status: 'completed',
              created_at: '2025-10-02T21:21:21.064378',
              updated_at: '2025-10-02T21:21:21.064379',
              repository_url: 'https://github.com/mauricezuse/negishi-freelancing',
              target_branch: 'main',
              agents: []
            }
          ])
        });
      }
    });

    // Mock successful Jira workflow creation
    await page.route('**/api/workflows/from-jira/NEGISHI-165', async (route) => {
      if (route.request().method() === 'POST') {
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

    // Mock successful Jira workflow creation for NEGISHI-166
    await page.route('**/api/workflows/from-jira/NEGISHI-166', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            message: 'Workflow created successfully for NEGISHI-166',
            workflow_id: 4,
            story_id: 'NEGISHI-166',
            title: 'Add real-time notifications feature'
          })
        });
      }
    });

    // Mock error response for non-existent story
    await page.route('**/api/workflows/from-jira/NEGISHI-999', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: 'Could not retrieve story NEGISHI-999 from Jira'
          })
        });
      }
    });

    // Mock error response for server error
    await page.route('**/api/workflows/from-jira/NEGISHI-ERROR', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: 'Internal server error'
          })
        });
      }
    });

    // Navigate to workflows page
    await page.goto('/workflows');
    await page.waitForLoadState('networkidle');
  });

  test('should create workflow from Jira story successfully', async ({ page }) => {
    // Click the "Create from Jira" button
    await page.getByTestId('create-from-jira-button').click();
    
    // Fill in the Jira story ID
    await page.fill('input[placeholder*="Jira Story ID"]', 'NEGISHI-165');
    await page.keyboard.press('Enter');
    
    // Wait for success message
    await expect(page.getByText('Workflow created successfully for NEGISHI-165')).toBeVisible();
    
    // Verify the workflow appears in the list
    await expect(page.getByText('NEGISHI-165: Implement advanced user authentication system')).toBeVisible();
  });

  test('should handle Jira story not found error', async ({ page }) => {
    // Click the "Create from Jira" button
    await page.getByTestId('create-from-jira-button').click();
    
    // Fill in a non-existent Jira story ID
    await page.fill('input[placeholder*="Jira Story ID"]', 'NEGISHI-999');
    await page.keyboard.press('Enter');
    
    // Wait for error message
    await expect(page.getByText('Could not retrieve story NEGISHI-999 from Jira')).toBeVisible();
  });

  test('should handle server error gracefully', async ({ page }) => {
    // Click the "Create from Jira" button
    await page.getByTestId('create-from-jira-button').click();
    
    // Fill in a story ID that causes server error
    await page.fill('input[placeholder*="Jira Story ID"]', 'NEGISHI-ERROR');
    await page.keyboard.press('Enter');
    
    // Wait for error message
    await expect(page.getByText('Internal server error')).toBeVisible();
  });

  test('should cancel Jira workflow creation', async ({ page }) => {
    // Click the "Create from Jira" button
    await page.getByTestId('create-from-jira-button').click();
    
    // Cancel the prompt (press Escape or click Cancel)
    await page.keyboard.press('Escape');
    
    // Verify no new workflow was created
    await expect(page.getByText('NEGISHI-165: Implement advanced user authentication system')).not.toBeVisible();
  });

  test('should validate Jira story ID format', async ({ page }) => {
    // Click the "Create from Jira" button
    await page.getByTestId('create-from-jira-button').click();
    
    // Try to create with invalid story ID format
    await page.fill('input[placeholder*="Jira Story ID"]', 'invalid-id');
    await page.keyboard.press('Enter');
    
    // Should show error for invalid format
    await expect(page.getByText('Invalid Jira story ID format')).toBeVisible();
  });

  test('should handle empty Jira story ID', async ({ page }) => {
    // Click the "Create from Jira" button
    await page.getByTestId('create-from-jira-button').click();
    
    // Try to create with empty story ID
    await page.fill('input[placeholder*="Jira Story ID"]', '');
    await page.keyboard.press('Enter');
    
    // Should not make API call
    await expect(page.getByText('Workflow created successfully')).not.toBeVisible();
  });

  test('should show loading state during Jira workflow creation', async ({ page }) => {
    // Mock a slow API response
    await page.route('**/api/workflows/from-jira/NEGISHI-165', async (route) => {
      if (route.request().method() === 'POST') {
        // Add delay to test loading state
        await new Promise(resolve => setTimeout(resolve, 1000));
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
    
    // Verify loading state is shown
    await expect(page.getByTestId('loading-spinner')).toBeVisible();
    
    // Wait for success message
    await expect(page.getByText('Workflow created successfully for NEGISHI-165')).toBeVisible();
  });

  test('should refresh workflow list after successful creation', async ({ page }) => {
    // Mock the updated workflow list after creation
    await page.route('**/api/workflows', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              id: 1,
              name: 'NEGISHI-178: Federation-aware agents',
              jira_story_id: 'NEGISHI-178',
              status: 'completed',
              created_at: '2025-10-02T21:21:21.064373',
              updated_at: '2025-10-02T21:21:21.064377',
              repository_url: 'https://github.com/mauricezuse/negishi-freelancing',
              target_branch: 'main',
              agents: []
            },
            {
              id: 2,
              name: 'NEGISHI-175: Intelligent code modifications',
              jira_story_id: 'NEGISHI-175',
              status: 'completed',
              created_at: '2025-10-02T21:21:21.064378',
              updated_at: '2025-10-02T21:21:21.064379',
              repository_url: 'https://github.com/mauricezuse/negishi-freelancing',
              target_branch: 'main',
              agents: []
            },
            {
              id: 3,
              name: 'NEGISHI-165: Implement advanced user authentication system',
              jira_story_id: 'NEGISHI-165',
              status: 'pending',
              created_at: '2025-10-04T13:00:00.000000',
              updated_at: '2025-10-04T13:00:00.000000',
              repository_url: 'https://github.com/mauricezuse/negishi-freelancing',
              target_branch: 'main',
              agents: []
            }
          ])
        });
      }
    });

    // Click the "Create from Jira" button
    await page.getByTestId('create-from-jira-button').click();
    
    // Fill in the Jira story ID
    await page.fill('input[placeholder*="Jira Story ID"]', 'NEGISHI-165');
    await page.keyboard.press('Enter');
    
    // Wait for success message
    await expect(page.getByText('Workflow created successfully for NEGISHI-165')).toBeVisible();
    
    // Verify the new workflow appears in the list
    await expect(page.getByText('NEGISHI-165: Implement advanced user authentication system')).toBeVisible();
    
    // Verify the workflow has the correct status
    await expect(page.getByText('pending')).toBeVisible();
  });

  test('should handle network timeout during Jira workflow creation', async ({ page }) => {
    // Mock a timeout response
    await page.route('**/api/workflows/from-jira/NEGISHI-165', async (route) => {
      if (route.request().method() === 'POST') {
        // Simulate timeout by not fulfilling the request
        await new Promise(resolve => setTimeout(resolve, 10000));
      }
    });

    // Click the "Create from Jira" button
    await page.getByTestId('create-from-jira-button').click();
    
    // Fill in the Jira story ID
    await page.fill('input[placeholder*="Jira Story ID"]', 'NEGISHI-165');
    await page.keyboard.press('Enter');
    
    // Wait for timeout error
    await expect(page.getByText('Request timeout')).toBeVisible();
  });

  test('should handle malformed JSON response', async ({ page }) => {
    // Mock malformed JSON response
    await page.route('**/api/workflows/from-jira/NEGISHI-165', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: 'invalid json response'
        });
      }
    });

    // Click the "Create from Jira" button
    await page.getByTestId('create-from-jira-button').click();
    
    // Fill in the Jira story ID
    await page.fill('input[placeholder*="Jira Story ID"]', 'NEGISHI-165');
    await page.keyboard.press('Enter');
    
    // Wait for error message
    await expect(page.getByText('Failed to parse response')).toBeVisible();
  });
});
