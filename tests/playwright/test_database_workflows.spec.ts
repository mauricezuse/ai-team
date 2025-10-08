import { test, expect } from '@playwright/test';

test.describe('Database-Driven Workflows List', () => {
  test.beforeEach(async ({ page }) => {
    // Mock database-driven workflows API
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
            },
            {
              id: 2,
              name: 'NEGISHI-175: Intelligent code modifications',
              jira_story_id: 'NEGISHI-175',
              jira_story_title: 'Implement intelligent code modifications that can automatically improve code quality',
              jira_story_description: 'Develop an AI-powered system that can analyze code and suggest or implement improvements automatically.',
              status: 'running',
              created_at: '2025-10-02T21:21:22.064373',
              updated_at: '2025-10-02T21:21:22.064377',
              repository_url: 'https://github.com/mauricezuse/negishi-freelancing',
              target_branch: 'main',
              conversations: [],
              code_files: []
            },
            {
              id: 3,
              name: 'NEGISHI-179: Test Story',
              jira_story_id: 'NEGISHI-179',
              jira_story_title: 'Test Story',
              jira_story_description: 'This is a test story for workflow creation',
              status: 'pending',
              created_at: '2025-10-02T21:21:23.064373',
              updated_at: '2025-10-02T21:21:23.064377',
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

  test('should display database-driven workflows list', async ({ page }) => {
    // Check workflows table is visible
    await expect(page.getByTestId('workflows-table')).toBeVisible();
    
    // Check workflow names
    await expect(page.locator('text=NEGISHI-178: Federation-aware agents')).toBeVisible();
    await expect(page.locator('text=NEGISHI-175: Intelligent code modifications')).toBeVisible();
    await expect(page.locator('text=NEGISHI-179: Test Story')).toBeVisible();
    
    // Check Jira story IDs
    await expect(page.locator('text=NEGISHI-178')).toBeVisible();
    await expect(page.locator('text=NEGISHI-175')).toBeVisible();
    await expect(page.locator('text=NEGISHI-179')).toBeVisible();
  });

  test('should display workflow status indicators', async ({ page }) => {
    // Check status indicators
    await expect(page.locator('text=completed')).toBeVisible();
    await expect(page.locator('text=running')).toBeVisible();
    await expect(page.locator('text=pending')).toBeVisible();
    
    // Check status styling
    const completedStatus = page.locator('text=completed').first();
    const runningStatus = page.locator('text=running');
    const pendingStatus = page.locator('text=pending');
    
    await expect(completedStatus).toBeVisible();
    await expect(runningStatus).toBeVisible();
    await expect(pendingStatus).toBeVisible();
  });

  test('should display workflow creation dates', async ({ page }) => {
    // Check creation dates are displayed
    await expect(page.locator('text=2025-10-02')).toBeVisible();
    
    // Should show multiple dates (3 workflows)
    const dateElements = page.locator('text=2025-10-02');
    await expect(dateElements).toHaveCount(3);
  });

  test('should navigate to workflow details', async ({ page }) => {
    // Click on first workflow link
    await page.getByTestId('workflow-link').first().click();
    
    // Should navigate to workflow detail page
    await expect(page).toHaveURL(/.*\/workflows\/1/);
    
    // Should display workflow title
    await expect(page.getByTestId('workflow-title')).toHaveText('NEGISHI-178: Federation-aware agents');
  });

  test('should filter workflows by status', async ({ page }) => {
    // Check status filter dropdown
    await expect(page.getByTestId('status-filter')).toBeVisible();
    
    // Select 'completed' status
    await page.getByTestId('status-filter').click();
    await page.locator('text=completed').click();
    
    // Should show only completed workflows
    await expect(page.locator('text=NEGISHI-178: Federation-aware agents')).toBeVisible();
    await expect(page.locator('text=NEGISHI-175: Intelligent code modifications')).not.toBeVisible();
    await expect(page.locator('text=NEGISHI-179: Test Story')).not.toBeVisible();
  });

  test('should search workflows by name', async ({ page }) => {
    // Enter search term
    await page.getByTestId('workflow-search').fill('Federation');
    
    // Should show only matching workflows
    await expect(page.locator('text=NEGISHI-178: Federation-aware agents')).toBeVisible();
    await expect(page.locator('text=NEGISHI-175: Intelligent code modifications')).not.toBeVisible();
    await expect(page.locator('text=NEGISHI-179: Test Story')).not.toBeVisible();
  });

  test('should search workflows by Jira story ID', async ({ page }) => {
    // Enter Jira story ID
    await page.getByTestId('workflow-search').fill('NEGISHI-175');
    
    // Should show only matching workflow
    await expect(page.locator('text=NEGISHI-175: Intelligent code modifications')).toBeVisible();
    await expect(page.locator('text=NEGISHI-178: Federation-aware agents')).not.toBeVisible();
    await expect(page.locator('text=NEGISHI-179: Test Story')).not.toBeVisible();
  });

  test('should handle empty search results', async ({ page }) => {
    // Enter non-matching search term
    await page.getByTestId('workflow-search').fill('NONEXISTENT');
    
    // Should show no workflows found message
    await expect(page.getByTestId('no-workflows')).toBeVisible();
    await expect(page.locator('text=No workflows found')).toBeVisible();
  });

  test('should refresh workflows list', async ({ page }) => {
    // Click refresh button
    await page.getByTestId('refresh-button').click();
    
    // Should reload workflows data
    await expect(page.getByTestId('workflows-table')).toBeVisible();
    await expect(page.locator('text=NEGISHI-178: Federation-aware agents')).toBeVisible();
  });

  test('should display workflow actions', async ({ page }) => {
    // Check action buttons for each workflow
    const actionButtons = page.locator('[data-testid^="view-workflow-button"], [data-testid^="start-workflow-button"], [data-testid^="delete-workflow-button"]');
    await expect(actionButtons).toHaveCount(9); // 3 workflows × 3 actions each
  });

  test('should handle database connection errors', async ({ page }) => {
    // Mock database error
    await page.route('**/api/workflows', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Database connection error'
        })
      });
    });
    
    // Reload page
    await page.reload();
    await page.waitForLoadState('networkidle');
    
    // Should show error state
    await expect(page.getByTestId('error-state')).toBeVisible();
    await expect(page.locator('text=Error loading workflows')).toBeVisible();
  });

  test('should display pagination for large datasets', async ({ page }) => {
    // Mock large dataset
    const largeWorkflowsList = Array.from({ length: 25 }, (_, i) => ({
      id: i + 1,
      name: `NEGISHI-${i + 100}: Test Story ${i + 1}`,
      jira_story_id: `NEGISHI-${i + 100}`,
      jira_story_title: `Test Story ${i + 1}`,
      jira_story_description: `This is test story ${i + 1}`,
      status: i % 3 === 0 ? 'completed' : i % 3 === 1 ? 'running' : 'pending',
      created_at: '2025-10-02T21:21:21.064373',
      updated_at: '2025-10-02T21:21:21.064377',
      repository_url: 'https://github.com/mauricezuse/negishi-freelancing',
      target_branch: 'main',
      conversations: [],
      code_files: []
    }));

    await page.route('**/api/workflows', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(largeWorkflowsList)
      });
    });
    
    // Reload page
    await page.reload();
    await page.waitForLoadState('networkidle');
    
    // Should show pagination controls
    await expect(page.locator('text=Showing 1 to 10 of 25 entries')).toBeVisible();
    
    // Should show page size options
    await expect(page.locator('text=10')).toBeVisible();
    await expect(page.locator('text=25')).toBeVisible();
    await expect(page.locator('text=50')).toBeVisible();
  });

  test('should sort workflows by creation date', async ({ page }) => {
    // Check that workflows are sorted by creation date (newest first)
    const workflowRows = page.locator('[data-testid="workflow-row"]');
    
    // First workflow should be NEGISHI-179 (newest)
    await expect(workflowRows.first().locator('text=NEGISHI-179: Test Story')).toBeVisible();
    
    // Last workflow should be NEGISHI-178 (oldest)
    await expect(workflowRows.last().locator('text=NEGISHI-178: Federation-aware agents')).toBeVisible();
  });

  test('should display repository information', async ({ page }) => {
    // Check repository URL is displayed
    await expect(page.locator('text=https://github.com/mauricezuse/negishi-freelancing')).toBeVisible();
    
    // Check target branch
    await expect(page.locator('text=main')).toBeVisible();
  });

  test('should handle workflow deletion', async ({ page }) => {
    // Mock delete endpoint
    await page.route('**/api/workflows/1', async (route) => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Workflow deleted successfully' })
        });
      }
    });
    
    // Click delete button for first workflow
    await page.getByTestId('delete-workflow-button').first().click();
    
    // Should show confirmation dialog
    await expect(page.locator('text=Are you sure you want to delete this workflow?')).toBeVisible();
    
    // Confirm deletion
    await page.locator('text=Yes, Delete').click();
    
    // Should show success message
    await expect(page.locator('text=Workflow deleted successfully')).toBeVisible();
  });
});
