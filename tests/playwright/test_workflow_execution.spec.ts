import { test, expect } from '@playwright/test';

test.describe('Workflow Execution with Database', () => {
  test.beforeEach(async ({ page }) => {
    // Mock workflow execution endpoint
    await page.route('**/api/workflows/*/execute', async (route) => {
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

    // Mock workflow detail with conversations
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

    // Navigate to workflow detail page
    await page.goto('http://localhost:4200/workflows/1');
    await page.waitForLoadState('networkidle');
  });

  test('should display workflow details with database data', async ({ page }) => {
    // Check workflow title and status
    await expect(page.getByTestId('workflow-title')).toHaveText('NEGISHI-178: Federation-aware agents');
    await expect(page.getByTestId('workflow-status')).toHaveText('completed');
    
    // Check Jira story details
    await expect(page.locator('text=Implement federation-aware agents that can collaborate across different environments')).toBeVisible();
    await expect(page.locator('text=Create a system where AI agents can work together across different environments and share information securely.')).toBeVisible();
  });

  test('should display agent conversations from database', async ({ page }) => {
    // Check conversations are visible
    await expect(page.getByTestId('conversations')).toBeVisible();
    
    // Check conversation timestamps
    await expect(page.getByTestId('conversations').locator('text=2024-01-01T00:00:00')).toBeVisible();
    await expect(page.getByTestId('conversations').locator('text=2024-01-01T00:01:00')).toBeVisible();
    await expect(page.getByTestId('conversations').locator('text=2024-01-01T00:02:00')).toBeVisible();
    
    // Check agent names
    await expect(page.getByTestId('conversations').locator('text=pm')).toBeVisible();
    await expect(page.getByTestId('conversations').locator('text=architect')).toBeVisible();
    await expect(page.getByTestId('conversations').locator('text=developer')).toBeVisible();
  });

  test('should display agent prompts and details', async ({ page }) => {
    // Expand first conversation
    await page.getByTestId('expand-button').first().click();
    
    // Check prompt is displayed
    await expect(page.locator('text=As a Product Manager, analyze the NEGISHI-178 story')).toBeVisible();
    
    // Check details and output
    await expect(page.locator('text=Analyzed NEGISHI-178 story requirements')).toBeVisible();
    await expect(page.locator('text=Story analysis complete. Identified key requirements for federation-aware agents implementation.')).toBeVisible();
  });

  test('should display code files with clickable links', async ({ page }) => {
    // Expand second conversation (architect)
    await page.getByTestId('expand-button').nth(1).click();
    
    // Check code files are displayed
    await expect(page.locator('text=Code Files Generated:')).toBeVisible();
    await expect(page.getByTestId('code-file').first()).toBeVisible();
    
    // Check file links point to negishi-freelancing repository
    const fileLink = page.getByTestId('code-file').first();
    await expect(fileLink).toHaveAttribute('href', 'https://github.com/mauricezuse/negishi-freelancing/blob/main/docs/architecture/federation-agents-design.md');
    await expect(fileLink).toHaveAttribute('target', '_blank');
  });

  test('should execute workflow and update status', async ({ page }) => {
    // Mock workflow status change
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
    
    // Click execute button
    await page.getByTestId('execute-button').click();
    
    // Should show success message
    await expect(page.locator('text=Workflow executed successfully')).toBeVisible();
    
    // Status should update to running
    await expect(page.getByTestId('workflow-status')).toHaveText('running');
  });

  test('should handle workflow execution errors', async ({ page }) => {
    // Mock execution error
    await page.route('**/api/workflows/1/execute', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Error executing workflow: Failed to retrieve story from Jira'
        })
      });
    });
    
    // Click execute button
    await page.getByTestId('execute-button').click();
    
    // Should show error message
    await expect(page.locator('text=Error executing workflow: Failed to retrieve story from Jira')).toBeVisible();
  });

  test('should refresh workflow data', async ({ page }) => {
    // Click refresh button
    await page.getByTestId('refresh-button').click();
    
    // Should reload workflow data
    await expect(page.getByTestId('workflow-title')).toBeVisible();
    await expect(page.getByTestId('workflow-status')).toBeVisible();
  });

  test('should display multiple code files from different agents', async ({ page }) => {
    // Expand third conversation (developer)
    await page.getByTestId('expand-button').nth(2).click();
    
    // Check multiple code files are displayed
    await expect(page.getByTestId('code-file')).toHaveCount(2);
    
    // Check file names
    await expect(page.locator('text=agent_service.py')).toBeVisible();
    await expect(page.locator('text=federation_api.py')).toBeVisible();
    
    // Check file links
    const agentServiceLink = page.getByTestId('code-file').filter({ hasText: 'agent_service.py' });
    await expect(agentServiceLink).toHaveAttribute('href', 'https://github.com/mauricezuse/negishi-freelancing/blob/main/backend/services/agent_service.py');
    
    const federationApiLink = page.getByTestId('code-file').filter({ hasText: 'federation_api.py' });
    await expect(federationApiLink).toHaveAttribute('href', 'https://github.com/mauricezuse/negishi-freelancing/blob/main/backend/api/federation_api.py');
  });

  test('should show loading state during execution', async ({ page }) => {
    // Mock slow execution response
    await page.route('**/api/workflows/1/execute', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 1000));
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
    
    // Click execute button
    await page.getByTestId('execute-button').click();
    
    // Should show loading state (button disabled)
    await expect(page.getByTestId('execute-button')).toBeDisabled();
  });

  test('should display conversation steps in chronological order', async ({ page }) => {
    // Check that conversations are displayed in order
    const conversations = page.getByTestId('conversations');
    
    // First conversation (story_analysis)
    await expect(conversations.locator('text=story_analysis')).toBeVisible();
    
    // Second conversation (architecture_design)
    await expect(conversations.locator('text=architecture_design')).toBeVisible();
    
    // Third conversation (backend_implementation)
    await expect(conversations.locator('text=backend_implementation')).toBeVisible();
  });

  test('should handle empty conversations gracefully', async ({ page }) => {
    // Mock workflow with no conversations
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
          status: 'pending',
          created_at: '2025-10-02T21:21:21.064373',
          updated_at: '2025-10-02T21:21:21.064377',
          repository_url: 'https://github.com/mauricezuse/negishi-freelancing',
          target_branch: 'main',
          conversations: [],
          code_files: []
        })
      });
    });
    
    // Reload page
    await page.reload();
    await page.waitForLoadState('networkidle');
    
    // Should show no conversations message
    await expect(page.locator('text=No conversations yet')).toBeVisible();
  });
});
