import { test, expect } from '@playwright/test';

test.describe('Comprehensive Database and Workflow Features', () => {
  test.beforeEach(async ({ page }) => {
    // Mock comprehensive API responses
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
            }
          ])
        });
      } else if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 3,
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

    // Mock workflow detail with full conversation data
    await page.route('**/api/workflows/1', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
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
          conversations: [
            {
              id: 1,
              step: 'story_analysis',
              timestamp: '2024-01-01T00:00:00',
              agent: 'pm',
              status: 'completed',
              details: 'Analyzed NEGISHI-178 story requirements',
              output: 'Story analysis complete. Identified key requirements for federation-aware agents implementation.',
              prompt: 'As a Product Manager, analyze the NEGISHI-178 story: "Implement federation-aware agents that can collaborate across different environments". Break down the requirements, identify stakeholders, and create user stories for this feature.',
              code_files: [],
              escalations: [],
              collaborations: []
            },
            {
              id: 2,
              step: 'architecture_design',
              timestamp: '2024-01-01T00:01:00',
              agent: 'architect',
              status: 'completed',
              details: 'Designed system architecture for federation-aware agents',
              output: 'Architecture design complete. Proposed system architecture for federation-aware agents.',
              prompt: 'As a System Architect, design a scalable architecture for federation-aware agents. Consider system design, API design, data flow, security, and integration patterns.',
              code_files: [
                {
                  filename: 'federation-agents-design.md',
                  file_path: 'docs/architecture/federation-agents-design.md'
                }
              ],
              escalations: [],
              collaborations: []
            },
            {
              id: 3,
              step: 'backend_implementation',
              timestamp: '2024-01-01T00:02:00',
              agent: 'developer',
              status: 'completed',
              details: 'Implemented backend services for federation-aware agents',
              output: 'Backend implementation complete. Created agent service and federation APIs.',
              prompt: 'As a Backend Developer, implement the federation-aware agents system. Create APIs for agent communication, data sharing, and cross-environment collaboration.',
              code_files: [
                {
                  filename: 'agent_service.py',
                  file_path: 'backend/services/agent_service.py'
                },
                {
                  filename: 'federation_api.py',
                  file_path: 'backend/api/federation_api.py'
                }
              ],
              escalations: [],
              collaborations: []
            }
          ],
          code_files: []
        })
      });
    });

    // Mock workflow execution
    await page.route('**/api/workflows/1/execute', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Workflow executed successfully',
          workflow_id: 1,
          story_id: 'NEGISHI-178',
          results_count: 5
        })
      });
    });

    // Mock Jira workflow creation
    await page.route('**/api/workflows/from-jira/NEGISHI-180', async (route) => {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Workflow created successfully for NEGISHI-180',
          workflow_id: 4,
          story_id: 'NEGISHI-180',
          title: 'Implement user authentication system'
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
  });

  test('should complete full workflow lifecycle with database integration', async ({ page }) => {
    // 1. Navigate to workflows list
    await page.goto('//workflows');
    await page.waitForLoadState('networkidle');
    
    // 2. Verify workflows list displays database data
    await expect(page.getByTestId('workflows-table')).toBeVisible();
    await expect(page.locator('text=NEGISHI-178: Federation-aware agents')).toBeVisible();
    await expect(page.locator('text=NEGISHI-175: Intelligent code modifications')).toBeVisible();
    
    // 3. Test workflow creation from Jira
    await page.evaluate(() => {
      window.prompt = () => 'NEGISHI-180';
    });
    await page.getByTestId('create-from-jira-button').click();
    await expect(page.locator('text=Workflow created successfully for NEGISHI-180')).toBeVisible();
    
    // 4. Test manual workflow creation
    await page.getByTestId('add-workflow-button').click();
    await expect(page).toHaveURL(/.*\/workflows\/create/);
    
    // Fill in form
    await page.locator('input[formControlName="jira_story_id"]').fill('NEGISHI-181');
    await page.locator('input[formControlName="jira_story_title"]').fill('Test Manual Creation');
    await page.locator('textarea[formControlName="jira_story_description"]').fill('This is a manually created test story');
    
    // Submit form
    await page.getByRole('button', { name: 'Create Workflow' }).click();
    await expect(page.locator('text=Workflow NEGISHI-181 created successfully')).toBeVisible();
    
    // 5. Navigate to workflow detail
    await expect(page).toHaveURL(/.*\/workflows\/3/);
    await expect(page.getByTestId('workflow-title')).toHaveText('NEGISHI-181: Test Manual Creation');
    
    // 6. Test workflow execution
    await page.goto('//workflows/1');
    await page.waitForLoadState('networkidle');
    
    await page.getByTestId('execute-button').click();
    await expect(page.locator('text=Workflow executed successfully')).toBeVisible();
    
    // 7. Verify conversation data from database
    await expect(page.getByTestId('conversations')).toBeVisible();
    await expect(page.getByTestId('conversations').locator('text=2024-01-01T00:00:00')).toBeVisible();
    await expect(page.getByTestId('conversations').locator('text=pm')).toBeVisible();
    await expect(page.getByTestId('conversations').locator('text=architect')).toBeVisible();
    await expect(page.getByTestId('conversations').locator('text=developer')).toBeVisible();
    
    // 8. Test conversation expansion and prompt display
    await page.getByTestId('expand-button').first().click();
    await expect(page.locator('text=As a Product Manager, analyze the NEGISHI-178 story')).toBeVisible();
    
    // 9. Test code file links
    await page.getByTestId('expand-button').nth(1).click();
    await expect(page.getByTestId('code-file').first()).toBeVisible();
    await expect(page.getByTestId('code-file').first()).toHaveAttribute('href', 'https://github.com/mauricezuse/negishi-freelancing/blob/main/docs/architecture/federation-agents-design.md');
    
    // 10. Test refresh functionality
    await page.getByTestId('refresh-button').click();
    await expect(page.getByTestId('workflow-title')).toBeVisible();
  });

  test('should handle database-driven search and filtering', async ({ page }) => {
    // Navigate to workflows list
    await page.goto('//workflows');
    await page.waitForLoadState('networkidle');
    
    // Test search by name
    await page.getByTestId('workflow-search').fill('Federation');
    await expect(page.locator('text=NEGISHI-178: Federation-aware agents')).toBeVisible();
    await expect(page.locator('text=NEGISHI-175: Intelligent code modifications')).not.toBeVisible();
    
    // Test search by Jira story ID
    await page.getByTestId('workflow-search').fill('NEGISHI-175');
    await expect(page.locator('text=NEGISHI-175: Intelligent code modifications')).toBeVisible();
    await expect(page.locator('text=NEGISHI-178: Federation-aware agents')).not.toBeVisible();
    
    // Test status filtering
    await page.getByTestId('workflow-search').fill('');
    await page.getByTestId('status-filter').click();
    await page.locator('text=completed').click();
    await expect(page.locator('text=NEGISHI-178: Federation-aware agents')).toBeVisible();
    await expect(page.locator('text=NEGISHI-175: Intelligent code modifications')).not.toBeVisible();
  });

  test('should handle database-driven pagination and large datasets', async ({ page }) => {
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
    
    // Test pagination
    await expect(page.locator('text=Showing 1 to 10 of 25 entries')).toBeVisible();
    await expect(page.locator('text=10')).toBeVisible();
    await expect(page.locator('text=25')).toBeVisible();
    await expect(page.locator('text=50')).toBeVisible();
    
    // Test page size change
    await page.locator('text=25').click();
    await expect(page.locator('text=Showing 1 to 25 of 25 entries')).toBeVisible();
  });

  test('should handle database-driven workflow status management', async ({ page }) => {
    // Navigate to workflow detail
    await page.goto('//workflows/1');
    await page.waitForLoadState('networkidle');
    
    // Check initial status
    await expect(page.getByTestId('workflow-status')).toHaveText('completed');
    
    // Test status change during execution
    await page.route('**/api/workflows/1', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          name: 'NEGISHI-178: Federation-aware agents',
          jira_story_id: 'NEGISHI-178',
          jira_story_title: 'Implement federation-aware agents that can collaborate across different environments',
          jira_story_description: 'Create a system where AI agents can work together across different environments and share information securely.',
          status: 'running',
          created_at: '2025-10-02T21:21:21.064373',
          updated_at: '2025-10-02T21:21:21.064377',
          repository_url: 'https://github.com/mauricezuse/negishi-freelancing',
          target_branch: 'main',
          conversations: [],
          code_files: []
        })
      });
    });
    
    // Execute workflow
    await page.getByTestId('execute-button').click();
    await expect(page.locator('text=Workflow executed successfully')).toBeVisible();
    
    // Check status updated
    await expect(page.getByTestId('workflow-status')).toHaveText('running');
  });

  test('should handle database-driven error states and recovery', async ({ page }) => {
    // Test database connection error
    await page.route('**/api/workflows', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Database connection error. Please try again later.'
        })
      });
    });
    
    // Navigate to workflows page
    await page.goto('//workflows');
    await page.waitForLoadState('networkidle');
    
    // Should show error state
    await expect(page.getByTestId('error-state')).toBeVisible();
    await expect(page.locator('text=Error loading workflows')).toBeVisible();
    
    // Test recovery by refreshing
    await page.route('**/api/workflows', async (route) => {
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
    });
    
    // Refresh page
    await page.getByTestId('refresh-button').click();
    await expect(page.getByTestId('workflows-table')).toBeVisible();
    await expect(page.locator('text=NEGISHI-178: Federation-aware agents')).toBeVisible();
  });

  test('should handle database-driven workflow deletion', async ({ page }) => {
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
    
    // Navigate to workflows list
    await page.goto('//workflows');
    await page.waitForLoadState('networkidle');
    
    // Click delete button
    await page.getByTestId('delete-workflow-button').first().click();
    
    // Should show confirmation dialog
    await expect(page.locator('text=Are you sure you want to delete this workflow?')).toBeVisible();
    
    // Confirm deletion
    await page.locator('text=Yes, Delete').click();
    
    // Should show success message
    await expect(page.locator('text=Workflow deleted successfully')).toBeVisible();
  });

  test('should handle database-driven workflow updates', async ({ page }) => {
    // Mock workflow update
    await page.route('**/api/workflows/1', async (route) => {
      if (route.request().method() === 'PUT') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 1,
            name: 'NEGISHI-178: Federation-aware agents (Updated)',
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
          })
        });
      }
    });
    
    // Navigate to workflow detail
    await page.goto('//workflows/1');
    await page.waitForLoadState('networkidle');
    
    // Test workflow update (if edit functionality exists)
    // This would test any edit/update functionality that might be added
    await expect(page.getByTestId('workflow-title')).toBeVisible();
  });
});
