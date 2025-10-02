import { test, expect } from '@playwright/test';

test.describe('Workflow Creation Features', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API responses for workflow creation
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
      } else if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 2,
            name: 'NEGISHI-179: Test Story',
            jira_story_id: 'NEGISHI-179',
            jira_story_title: 'Test Story',
            jira_story_description: 'This is a test story for workflow creation',
            status: 'pending',
            created_at: '2025-10-02T21:21:39.398424',
            updated_at: '2025-10-02T21:21:39.398431',
            repository_url: 'https://github.com/mauricezuse/negishi-freelancing',
            target_branch: 'main',
            conversations: [],
            code_files: []
          })
        });
      }
    });

    // Mock Jira workflow creation
    await page.route('**/api/workflows/from-jira/*', async (route) => {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Workflow created successfully for NEGISHI-180',
          workflow_id: 3,
          story_id: 'NEGISHI-180',
          title: 'Jira Story Title'
        })
      });
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
    await page.goto('http://localhost:4200/workflows');
    await page.waitForLoadState('networkidle');
  });

  test('should display workflows list with create buttons', async ({ page }) => {
    // Check that the workflows list is visible
    await expect(page.getByTestId('workflows-table')).toBeVisible();
    
    // Check for create workflow buttons
    await expect(page.getByTestId('add-workflow-button')).toBeVisible();
    await expect(page.getByTestId('create-from-jira-button')).toBeVisible();
    
    // Check button labels
    await expect(page.getByTestId('add-workflow-button')).toHaveText('Create Workflow');
    await expect(page.getByTestId('create-from-jira-button')).toHaveText('Create from Jira');
  });

  test('should navigate to create workflow form', async ({ page }) => {
    // Click create workflow button
    await page.getByTestId('add-workflow-button').click();
    
    // Should navigate to create workflow page
    await expect(page).toHaveURL(/.*\/workflows\/create/);
    
    // Check form elements are present
    await expect(page.locator('input[formControlName="jira_story_id"]')).toBeVisible();
    await expect(page.locator('input[formControlName="jira_story_title"]')).toBeVisible();
    await expect(page.locator('textarea[formControlName="jira_story_description"]')).toBeVisible();
    await expect(page.locator('input[formControlName="repository_url"]')).toBeVisible();
    await expect(page.locator('input[formControlName="target_branch"]')).toBeVisible();
  });

  test('should validate create workflow form', async ({ page }) => {
    // Navigate to create workflow page
    await page.getByTestId('add-workflow-button').click();
    
    // Try to submit empty form
    await page.getByRole('button', { name: 'Create Workflow' }).click();
    
    // Should show validation errors
    await expect(page.locator('.error-message')).toBeVisible();
    
    // Fill in invalid Jira story ID
    await page.locator('input[formControlName="jira_story_id"]').fill('INVALID');
    await page.locator('input[formControlName="jira_story_title"]').fill('Test');
    await page.locator('textarea[formControlName="jira_story_description"]').fill('Test description');
    
    // Should show format error for Jira ID
    await expect(page.locator('text=Format must be PROJECT-123')).toBeVisible();
  });

  test('should create workflow with valid data', async ({ page }) => {
    // Navigate to create workflow page
    await page.getByTestId('add-workflow-button').click();
    
    // Fill in valid form data
    await page.locator('input[formControlName="jira_story_id"]').fill('NEGISHI-179');
    await page.locator('input[formControlName="jira_story_title"]').fill('Test Story');
    await page.locator('textarea[formControlName="jira_story_description"]').fill('This is a test story for workflow creation');
    await page.locator('input[formControlName="repository_url"]').fill('https://github.com/mauricezuse/negishi-freelancing');
    await page.locator('input[formControlName="target_branch"]').fill('main');
    
    // Submit form
    await page.getByRole('button', { name: 'Create Workflow' }).click();
    
    // Should show success message
    await expect(page.locator('text=Workflow NEGISHI-179 created successfully')).toBeVisible();
    
    // Should navigate to workflow detail page
    await expect(page).toHaveURL(/.*\/workflows\/2/);
  });

  test('should create workflow from Jira', async ({ page }) => {
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

  test('should handle Jira creation errors gracefully', async ({ page }) => {
    // Mock Jira creation error
    await page.route('**/api/workflows/from-jira/*', async (route) => {
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

  test('should cancel create workflow form', async ({ page }) => {
    // Navigate to create workflow page
    await page.getByTestId('add-workflow-button').click();
    
    // Fill in some data
    await page.locator('input[formControlName="jira_story_id"]').fill('NEGISHI-179');
    
    // Click cancel button
    await page.getByRole('button', { name: 'Cancel' }).click();
    
    // Should navigate back to workflows list
    await expect(page).toHaveURL(/.*\/workflows$/);
    await expect(page.getByTestId('workflows-table')).toBeVisible();
  });

  test('should show loading state during workflow creation', async ({ page }) => {
    // Mock slow response
    await page.route('**/api/workflows', async (route) => {
      if (route.request().method() === 'POST') {
        await new Promise(resolve => setTimeout(resolve, 1000));
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 2,
            name: 'NEGISHI-179: Test Story',
            jira_story_id: 'NEGISHI-179',
            jira_story_title: 'Test Story',
            jira_story_description: 'This is a test story for workflow creation',
            status: 'pending',
            created_at: '2025-10-02T21:21:39.398424',
            updated_at: '2025-10-02T21:21:39.398431',
            repository_url: 'https://github.com/mauricezuse/negishi-freelancing',
            target_branch: 'main',
            conversations: [],
            code_files: []
          })
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([])
        });
      }
    });
    
    // Navigate to create workflow page
    await page.getByTestId('add-workflow-button').click();
    
    // Fill in valid form data
    await page.locator('input[formControlName="jira_story_id"]').fill('NEGISHI-179');
    await page.locator('input[formControlName="jira_story_title"]').fill('Test Story');
    await page.locator('textarea[formControlName="jira_story_description"]').fill('This is a test story for workflow creation');
    
    // Submit form
    await page.getByRole('button', { name: 'Create Workflow' }).click();
    
    // Should show loading state
    await expect(page.getByRole('button', { name: 'Create Workflow' })).toBeDisabled();
  });
});
