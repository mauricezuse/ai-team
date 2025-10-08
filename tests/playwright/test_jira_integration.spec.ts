import { test, expect } from '@playwright/test';

test.describe('Jira Integration Features', () => {
  test.beforeEach(async ({ page }) => {
    // Mock workflows list
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
              jira_story_title: 'Implement federation-aware agents that can collaborate across different environments',
              jira_story_description: 'Create a system where AI agents can work together across different environments and share information securely.',
              status: 'completed',
              created_at: '2025-10-02T21:21:21.064373',
              updated_at: '2025-10-02T21:21:21.064377',
              repository_url: 'https://github.com/mauricezuse/negishi-freelancing',
              target_branch: 'main',
              conversations: [],
              code_files: []
            }
          ])
        });
      }
    });

    // Mock agents endpoint
    await page.route('**/api/agents', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 'pm', name: 'Product Manager', role: 'Requirements analysis and user story creation' },
          { id: 'architect', name: 'System Architect', role: 'System design and architecture' },
          { id: 'developer', name: 'Backend Developer', role: 'Backend implementation and APIs' },
          { id: 'frontend', name: 'Frontend Developer', role: 'Frontend implementation and UI' },
          { id: 'tester', name: 'QA Tester', role: 'Testing and quality assurance' },
          { id: 'reviewer', name: 'Code Reviewer', role: 'Code review and quality standards' }
        ])
      });
    });

    // Navigate to workflows page
    await page.goto('http://localhost:4001/workflows');
    await page.waitForLoadState('networkidle');
  });

  test('should create workflow from existing Jira story', async ({ page }) => {
    // Mock successful Jira story retrieval
    await page.route('**/api/workflows/from-jira/NEGISHI-180', async (route) => {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Workflow created successfully for NEGISHI-180',
          workflow_id: 2,
          story_id: 'NEGISHI-180',
          title: 'Implement user authentication system'
        })
      });
    });

    // Mock the prompt dialog
    await page.evaluate(() => {
      window.prompt = () => 'NEGISHI-180';
    });
    
    // Click create from Jira button
    await page.getByTestId('create-from-jira-button').click();
    
    // Should show success message
    await expect(page.locator('text=Workflow created successfully for NEGISHI-180')).toBeVisible();
    
    // Should refresh the workflows list
    await expect(page.getByTestId('workflows-table')).toBeVisible();
  });

  test('should handle Jira story not found error', async ({ page }) => {
    // Mock Jira story not found
    await page.route('**/api/workflows/from-jira/NEGISHI-999', async (route) => {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Could not retrieve story NEGISHI-999 from Jira'
        })
      });
    });

    // Mock the prompt dialog
    await page.evaluate(() => {
      window.prompt = () => 'NEGISHI-999';
    });
    
    // Click create from Jira button
    await page.getByTestId('create-from-jira-button').click();
    
    // Should show error message
    await expect(page.locator('text=Could not retrieve story NEGISHI-999 from Jira')).toBeVisible();
  });

  test('should handle Jira authentication error', async ({ page }) => {
    // Mock Jira authentication error
    await page.route('**/api/workflows/from-jira/NEGISHI-180', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Jira authentication failed. Please check your credentials.'
        })
      });
    });

    // Mock the prompt dialog
    await page.evaluate(() => {
      window.prompt = () => 'NEGISHI-180';
    });
    
    // Click create from Jira button
    await page.getByTestId('create-from-jira-button').click();
    
    // Should show authentication error
    await expect(page.locator('text=Jira authentication failed. Please check your credentials.')).toBeVisible();
  });

  test('should handle duplicate workflow creation', async ({ page }) => {
    // Mock duplicate workflow error
    await page.route('**/api/workflows/from-jira/NEGISHI-178', async (route) => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Workflow for this Jira story already exists'
        })
      });
    });

    // Mock the prompt dialog
    await page.evaluate(() => {
      window.prompt = () => 'NEGISHI-178';
    });
    
    // Click create from Jira button
    await page.getByTestId('create-from-jira-button').click();
    
    // Should show duplicate error
    await expect(page.locator('text=Workflow for this Jira story already exists')).toBeVisible();
  });

  test('should handle Jira server error', async ({ page }) => {
    // Mock Jira server error
    await page.route('**/api/workflows/from-jira/NEGISHI-180', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Jira server error. Please try again later.'
        })
      });
    });

    // Mock the prompt dialog
    await page.evaluate(() => {
      window.prompt = () => 'NEGISHI-180';
    });
    
    // Click create from Jira button
    await page.getByTestId('create-from-jira-button').click();
    
    // Should show server error
    await expect(page.locator('text=Jira server error. Please try again later.')).toBeVisible();
  });

  test('should cancel Jira workflow creation', async ({ page }) => {
    // Mock the prompt dialog to return null (cancel)
    await page.evaluate(() => {
      window.prompt = () => null;
    });
    
    // Click create from Jira button
    await page.getByTestId('create-from-jira-button').click();
    
    // Should not show any error or success message
    await expect(page.locator('text=Workflow created successfully')).not.toBeVisible();
    await expect(page.locator('text=Error')).not.toBeVisible();
  });

  test('should handle empty Jira story ID', async ({ page }) => {
    // Mock the prompt dialog to return empty string
    await page.evaluate(() => {
      window.prompt = () => '';
    });
    
    // Click create from Jira button
    await page.getByTestId('create-from-jira-button').click();
    
    // Should not make any API call
    await expect(page.locator('text=Workflow created successfully')).not.toBeVisible();
  });

  test('should handle invalid Jira story ID format', async ({ page }) => {
    // Mock the prompt dialog with invalid format
    await page.evaluate(() => {
      window.prompt = () => 'INVALID-FORMAT';
    });
    
    // Click create from Jira button
    await page.getByTestId('create-from-jira-button').click();
    
    // Should show validation error
    await expect(page.locator('text=Invalid Jira story ID format')).toBeVisible();
  });

  test('should display Jira story details in created workflow', async ({ page }) => {
    // Mock Jira story with detailed information
    await page.route('**/api/workflows/from-jira/NEGISHI-180', async (route) => {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Workflow created successfully for NEGISHI-180',
          workflow_id: 2,
          story_id: 'NEGISHI-180',
          title: 'Implement user authentication system',
          description: 'As a user, I want to be able to log in to the system securely so that I can access my personal data.',
          assignee: 'john.doe@example.com',
          priority: 'High',
          labels: ['authentication', 'security', 'backend']
        })
      });
    });

    // Mock the prompt dialog
    await page.evaluate(() => {
      window.prompt = () => 'NEGISHI-180';
    });
    
    // Click create from Jira button
    await page.getByTestId('create-from-jira-button').click();
    
    // Should show success message with story details
    await expect(page.locator('text=Workflow created successfully for NEGISHI-180')).toBeVisible();
  });

  test('should handle Jira story with complex description', async ({ page }) => {
    // Mock Jira story with ADF (Atlassian Document Format) description
    await page.route('**/api/workflows/from-jira/NEGISHI-180', async (route) => {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Workflow created successfully for NEGISHI-180',
          workflow_id: 2,
          story_id: 'NEGISHI-180',
          title: 'Implement user authentication system',
          description: 'As a user, I want to be able to log in to the system securely so that I can access my personal data. This includes: 1. Username/password authentication 2. Two-factor authentication 3. Password reset functionality 4. Session management',
          assignee: 'john.doe@example.com',
          priority: 'High',
          labels: ['authentication', 'security', 'backend']
        })
      });
    });

    // Mock the prompt dialog
    await page.evaluate(() => {
      window.prompt = () => 'NEGISHI-180';
    });
    
    // Click create from Jira button
    await page.getByTestId('create-from-jira-button').click();
    
    // Should show success message
    await expect(page.locator('text=Workflow created successfully for NEGISHI-180')).toBeVisible();
  });

  test('should handle network timeout during Jira creation', async ({ page }) => {
    // Mock network timeout
    await page.route('**/api/workflows/from-jira/NEGISHI-180', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 10000)); // 10 second delay
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Workflow created successfully for NEGISHI-180',
          workflow_id: 2,
          story_id: 'NEGISHI-180',
          title: 'Implement user authentication system'
        })
      });
    });

    // Mock the prompt dialog
    await page.evaluate(() => {
      window.prompt = () => 'NEGISHI-180';
    });
    
    // Click create from Jira button
    await page.getByTestId('create-from-jira-button').click();
    
    // Should show loading state
    await expect(page.getByTestId('create-from-jira-button')).toBeDisabled();
  });

  test('should validate Jira story ID format in frontend', async ({ page }) => {
    // Test various invalid formats
    const invalidFormats = ['INVALID', '123', 'NEGISHI', 'NEGISHI-', '-123', 'NEGISHI-abc'];
    
    for (const invalidFormat of invalidFormats) {
      // Mock the prompt dialog
      await page.evaluate((format) => {
        window.prompt = () => format;
      }, invalidFormat);
      
      // Click create from Jira button
      await page.getByTestId('create-from-jira-button').click();
      
      // Should show validation error
      await expect(page.locator('text=Invalid Jira story ID format')).toBeVisible();
    }
  });

  test('should handle Jira story with special characters', async ({ page }) => {
    // Mock Jira story with special characters in title/description
    await page.route('**/api/workflows/from-jira/NEGISHI-180', async (route) => {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Workflow created successfully for NEGISHI-180',
          workflow_id: 2,
          story_id: 'NEGISHI-180',
          title: 'Implement user authentication system (v2.0)',
          description: 'As a user, I want to be able to log in to the system securely so that I can access my personal data. This includes: 1. Username/password authentication 2. Two-factor authentication 3. Password reset functionality 4. Session management',
          assignee: 'john.doe@example.com',
          priority: 'High',
          labels: ['authentication', 'security', 'backend']
        })
      });
    });

    // Mock the prompt dialog
    await page.evaluate(() => {
      window.prompt = () => 'NEGISHI-180';
    });
    
    // Click create from Jira button
    await page.getByTestId('create-from-jira-button').click();
    
    // Should show success message
    await expect(page.locator('text=Workflow created successfully for NEGISHI-180')).toBeVisible();
  });
});
