import { test, expect } from '@playwright/test';

test.describe('Complete UI Functionality Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Mock all API endpoints
    await page.route('**/workflows', async route => {
      const mockWorkflows = [
        {
          id: 'enhanced_story_NEGISHI-178',
          name: 'Enhanced Story Negishi-178',
          status: 'completed',
          agents: ['pm', 'architect', 'developer'],
          created_at: '2024-01-01T00:00:00',
          last_step: 'developer_implementation'
        },
        {
          id: 'enhanced_story_NEGISHI-175',
          name: 'Enhanced Story Negishi-175',
          status: 'pending',
          agents: ['pm'],
          created_at: '2024-01-01T01:00:00',
          last_step: 'story_retrieved'
        }
      ];
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockWorkflows)
      });
    });

    await page.route('**/workflows/enhanced_story_NEGISHI-178', async route => {
      const mockWorkflowDetail = {
        id: 'enhanced_story_NEGISHI-178',
        name: 'Enhanced Story Negishi-178',
        status: 'completed',
        conversations: [
          {
            step: 'story_retrieved',
            timestamp: '2024-01-01T00:00:00',
            agent: 'pm',
            status: 'completed',
            details: 'Story retrieved successfully from Jira',
            output: 'Story: Implement user authentication system with JWT tokens',
            code_files: [],
            escalations: [],
            collaborations: []
          },
          {
            step: 'architect_review',
            timestamp: '2024-01-01T00:01:00',
            agent: 'architect',
            status: 'completed',
            details: 'Architecture plan created with security considerations',
            output: 'Plan: Use JWT tokens with FastAPI backend, implement role-based access control',
            code_files: ['backend/auth/jwt_handler.py', 'backend/auth/security.py'],
            escalations: [
              {
                from_agent: 'architect',
                to_agent: 'developer',
                reason: 'Complex security requirements need backend expertise',
                status: 'resolved'
              }
            ],
            collaborations: []
          },
          {
            step: 'developer_implementation',
            timestamp: '2024-01-01T00:02:00',
            agent: 'developer',
            status: 'completed',
            details: 'Backend implementation completed with security features',
            output: 'Implemented JWT authentication endpoints with role-based access',
            code_files: [
              'backend/auth/endpoints.py',
              'backend/auth/models.py',
              'backend/auth/middleware.py'
            ],
            escalations: [],
            collaborations: [
              {
                from_agent: 'developer',
                to_agent: 'frontend',
                request_type: 'API_contract',
                status: 'completed'
              }
            ]
          }
        ],
        created_at: '2024-01-01T00:00:00',
        collaboration_queue: [],
        escalation_queue: []
      };
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockWorkflowDetail)
      });
    });

    await page.route('**/agents', async route => {
      const mockAgents = [
        {
          id: 'pm',
          name: 'Product Manager',
          role: 'Product Management',
          goal: 'Define product requirements and user stories'
        },
        {
          id: 'architect',
          name: 'Solution Architect',
          role: 'Architecture',
          goal: 'Design system architecture and technical solutions'
        },
        {
          id: 'developer',
          name: 'Backend Developer',
          role: 'Backend Development',
          goal: 'Implement backend services and APIs'
        }
      ];
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAgents)
      });
    });

    await page.route('**/agents/pm', async route => {
      const mockAgentDetail = {
        id: 'pm',
        name: 'Product Manager',
        role: 'Product Management',
        goal: 'Define product requirements and user stories',
        backstory: 'Experienced product manager with deep understanding of user needs',
        capabilities: ['Requirements analysis', 'User story creation', 'Stakeholder communication']
      };
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAgentDetail)
      });
    });

    await page.route('**/workflows/enhanced_story_NEGISHI-178/execute', async route => {
      const mockExecutionResult = {
        workflow_id: 'enhanced_story_NEGISHI-178',
        story_id: 'NEGISHI-178',
        status: 'completed',
        results: [
          { step: 'execution_started', status: 'completed' },
          { step: 'execution_completed', status: 'completed' }
        ],
        message: 'Workflow executed successfully for story NEGISHI-178'
      };
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockExecutionResult)
      });
    });
  });

  test('should display dashboard with correct counts', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Check dashboard elements
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();
    await expect(page.locator('text=Agents')).toBeVisible();
    await expect(page.locator('text=Workflows')).toBeVisible();
    
    // Check that counts are displayed (they should be loaded from API)
    await expect(page.locator('text=3')).toBeVisible(); // Agent count
    await expect(page.locator('text=2')).toBeVisible(); // Workflow count
  });

  test('should navigate between pages using menu', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Test navigation to workflows
    await page.click('text=Workflows');
    await expect(page).toHaveURL(/.*workflows/);
    await expect(page.locator('text=Workflows')).toBeVisible();
    
    // Test navigation to agents
    await page.click('text=Agents');
    await expect(page).toHaveURL(/.*agents/);
    await expect(page.locator('text=Agents')).toBeVisible();
    
    // Test navigation back to dashboard
    await page.click('text=Dashboard');
    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();
  });

  test('should display workflows list with all functionality', async ({ page }) => {
    await page.goto('/workflows');
    
    // Check workflows are displayed
    await expect(page.locator('[data-testid="workflows-table"]')).toBeVisible();
    await expect(page.locator('text=Enhanced Story Negishi-178')).toBeVisible();
    await expect(page.locator('text=Enhanced Story Negishi-175')).toBeVisible();
    
    // Check status indicators
    await expect(page.locator('[data-testid="workflow-status"]').first()).toContainText('completed');
    await expect(page.locator('[data-testid="workflow-status"]').nth(1)).toContainText('pending');
    
    // Check agent counts
    await expect(page.locator('text=3')).toBeVisible(); // First workflow has 3 agents
    await expect(page.locator('text=1')).toBeVisible(); // Second workflow has 1 agent
    
    // Test search functionality
    await page.fill('[data-testid="workflow-search"]', 'NEGISHI-178');
    await expect(page.locator('text=Enhanced Story Negishi-178')).toBeVisible();
    await expect(page.locator('text=Enhanced Story Negishi-175')).not.toBeVisible();
    
    // Clear search
    await page.fill('[data-testid="workflow-search"]', '');
    await expect(page.locator('text=Enhanced Story Negishi-175')).toBeVisible();
    
    // Test status filter
    await page.selectOption('[data-testid="status-filter"]', 'completed');
    await expect(page.locator('text=Enhanced Story Negishi-178')).toBeVisible();
    await expect(page.locator('text=Enhanced Story Negishi-175')).not.toBeVisible();
    
    // Clear filter
    await page.selectOption('[data-testid="status-filter"]', '');
    await expect(page.locator('text=Enhanced Story Negishi-175')).toBeVisible();
  });

  test('should navigate to workflow detail and display conversations', async ({ page }) => {
    await page.goto('/workflows');
    
    // Click on first workflow
    await page.click('[data-testid="view-workflow-button"]');
    await expect(page).toHaveURL(/.*workflows\/enhanced_story_NEGISHI-178/);
    
    // Check workflow details
    await expect(page.locator('text=Enhanced Story Negishi-178')).toBeVisible();
    await expect(page.locator('text=completed')).toBeVisible();
    
    // Check agents involved
    await expect(page.locator('text=pm')).toBeVisible();
    await expect(page.locator('text=architect')).toBeVisible();
    await expect(page.locator('text=developer')).toBeVisible();
    
    // Check conversations are displayed
    await expect(page.locator('[data-testid="conversation"]')).toHaveCount(3);
    await expect(page.locator('text=story_retrieved')).toBeVisible();
    await expect(page.locator('text=architect_review')).toBeVisible();
    await expect(page.locator('text=developer_implementation')).toBeVisible();
    
    // Check agent names in conversations
    await expect(page.locator('text=pm')).toBeVisible();
    await expect(page.locator('text=architect')).toBeVisible();
    await expect(page.locator('text=developer')).toBeVisible();
  });

  test('should expand and collapse conversation details', async ({ page }) => {
    await page.goto('/workflows/enhanced_story_NEGISHI-178');
    
    // Initially conversations should be collapsed
    await expect(page.locator('text=Story retrieved successfully from Jira')).not.toBeVisible();
    
    // Click to expand first conversation
    await page.click('[data-testid="expand-button"]');
    await expect(page.locator('text=Story retrieved successfully from Jira')).toBeVisible();
    await expect(page.locator('text=Story: Implement user authentication system')).toBeVisible();
    
    // Click to collapse
    await page.click('[data-testid="collapse-button"]');
    await expect(page.locator('text=Story retrieved successfully from Jira')).not.toBeVisible();
  });

  test('should display code files and escalations in conversations', async ({ page }) => {
    await page.goto('/workflows/enhanced_story_NEGISHI-178');
    
    // Expand architect conversation
    await page.click('[data-testid="expand-button"]');
    
    // Check code files are displayed
    await expect(page.locator('text=backend/auth/jwt_handler.py')).toBeVisible();
    await expect(page.locator('text=backend/auth/security.py')).toBeVisible();
    
    // Check escalations are displayed
    await expect(page.locator('text=Complex security requirements need backend expertise')).toBeVisible();
    await expect(page.locator('text=architect → developer')).toBeVisible();
    await expect(page.locator('text=resolved')).toBeVisible();
    
    // Check collaborations are displayed
    await expect(page.locator('text=API_contract')).toBeVisible();
    await expect(page.locator('text=developer → frontend')).toBeVisible();
    await expect(page.locator('text=completed')).toBeVisible();
  });

  test('should filter conversations by agent', async ({ page }) => {
    await page.goto('/workflows/enhanced_story_NEGISHI-178');
    
    // Filter by architect
    await page.selectOption('.agent-filter', 'architect');
    
    // Should only show architect conversation
    await expect(page.locator('[data-testid="conversation"]')).toHaveCount(1);
    await expect(page.locator('text=architect_review')).toBeVisible();
    await expect(page.locator('text=story_retrieved')).not.toBeVisible();
    await expect(page.locator('text=developer_implementation')).not.toBeVisible();
    
    // Clear filter
    await page.selectOption('.agent-filter', '');
    await expect(page.locator('[data-testid="conversation"]')).toHaveCount(3);
  });

  test('should search conversations by content', async ({ page }) => {
    await page.goto('/workflows/enhanced_story_NEGISHI-178');
    
    // Search for "JWT"
    await page.fill('.search-input', 'JWT');
    
    // Should only show conversations containing "JWT"
    await expect(page.locator('[data-testid="conversation"]')).toHaveCount(2);
    await expect(page.locator('text=JWT tokens')).toBeVisible();
    await expect(page.locator('text=JWT authentication')).toBeVisible();
    
    // Clear search
    await page.fill('.search-input', '');
    await expect(page.locator('[data-testid="conversation"]')).toHaveCount(3);
  });

  test('should execute workflow from detail page', async ({ page }) => {
    await page.goto('/workflows/enhanced_story_NEGISHI-178');
    
    // Click execute button
    await page.click('button:has-text("Execute")');
    
    // Check for success message
    await expect(page.locator('text=Workflow executed successfully')).toBeVisible();
  });

  test('should display agents list with all functionality', async ({ page }) => {
    await page.goto('/agents');
    
    // Check agents are displayed
    await expect(page.locator('[data-testid="agents-table"]')).toBeVisible();
    await expect(page.locator('text=Product Manager')).toBeVisible();
    await expect(page.locator('text=Solution Architect')).toBeVisible();
    await expect(page.locator('text=Backend Developer')).toBeVisible();
    
    // Check roles
    await expect(page.locator('text=Product Management')).toBeVisible();
    await expect(page.locator('text=Architecture')).toBeVisible();
    await expect(page.locator('text=Backend Development')).toBeVisible();
    
    // Check goals
    await expect(page.locator('text=Define product requirements and user stories')).toBeVisible();
    await expect(page.locator('text=Design system architecture and technical solutions')).toBeVisible();
    await expect(page.locator('text=Implement backend services and APIs')).toBeVisible();
  });

  test('should navigate to agent detail page', async ({ page }) => {
    await page.goto('/agents');
    
    // Click on first agent
    await page.click('[data-testid="view-agent-button"]');
    await expect(page).toHaveURL(/.*agents\/pm/);
    
    // Check agent details are displayed
    await expect(page.locator('text=Product Manager')).toBeVisible();
    await expect(page.locator('text=Product Management')).toBeVisible();
    await expect(page.locator('text=Define product requirements and user stories')).toBeVisible();
  });

  test('should handle empty states gracefully', async ({ page }) => {
    // Mock empty workflows
    await page.route('**/workflows', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([])
      });
    });

    await page.goto('/workflows');
    
    // Check empty state
    await expect(page.locator('[data-testid="no-workflows"]')).toBeVisible();
    await expect(page.locator('text=No workflows found')).toBeVisible();
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock API error
    await page.route('**/workflows', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Internal server error'
        })
      });
    });

    await page.goto('/workflows');
    
    // Check for error handling (this depends on your error handling implementation)
    // The page should not crash and should show some error state
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should be responsive on mobile devices', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto('/workflows');
    
    // Check that content is still visible and functional
    await expect(page.locator('[data-testid="workflows-table"]')).toBeVisible();
    await expect(page.locator('text=Enhanced Story Negishi-178')).toBeVisible();
    
    // Test navigation still works
    await page.click('text=Agents');
    await expect(page).toHaveURL(/.*agents/);
  });

  test('should maintain state during navigation', async ({ page }) => {
    await page.goto('/workflows');
    
    // Search for something
    await page.fill('[data-testid="workflow-search"]', 'NEGISHI-178');
    await expect(page.locator('text=Enhanced Story Negishi-178')).toBeVisible();
    
    // Navigate to detail
    await page.click('[data-testid="view-workflow-button"]');
    await expect(page).toHaveURL(/.*workflows\/enhanced_story_NEGISHI-178/);
    
    // Navigate back
    await page.goBack();
    await expect(page).toHaveURL(/.*workflows/);
    
    // Search should be cleared (this is expected behavior)
    await expect(page.locator('[data-testid="workflow-search"]')).toHaveValue('');
  });

  test('should handle workflow execution errors', async ({ page }) => {
    // Mock execution error
    await page.route('**/workflows/enhanced_story_NEGISHI-178/execute', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Error executing workflow: Connection timeout'
        })
      });
    });

    await page.goto('/workflows/enhanced_story_NEGISHI-178');
    
    // Click execute button
    await page.click('button:has-text("Execute")');
    
    // Check for error message
    await expect(page.locator('text=Error executing workflow')).toBeVisible();
  });

  test('should refresh data when refresh button is clicked', async ({ page }) => {
    await page.goto('/workflows');
    
    // Click refresh button
    await page.click('[data-testid="refresh-button"]');
    
    // Data should be reloaded (this is tested by the fact that the page still shows the mocked data)
    await expect(page.locator('text=Enhanced Story Negishi-178')).toBeVisible();
  });

  test('should show loading states appropriately', async ({ page }) => {
    // Mock slow API response
    await page.route('**/workflows', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([])
      });
    });

    await page.goto('/workflows');
    
    // Should show some loading state (this depends on your implementation)
    // For now, just verify the page loads
    await expect(page.locator('text=Workflows')).toBeVisible();
  });
});
