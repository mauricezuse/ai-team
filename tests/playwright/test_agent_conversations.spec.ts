import { test, expect } from '@playwright/test';

test.describe('Agent Conversations Display Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Mock detailed workflow with agent conversations
    await page.route('**/workflows/enhanced_story_NEGISHI-178', async route => {
      const mockWorkflowWithConversations = {
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
          },
          {
            step: 'frontend_implementation',
            timestamp: '2024-01-01T00:03:00',
            agent: 'frontend',
            status: 'completed',
            details: 'Frontend authentication components implemented',
            output: 'Created login form, auth service, and route guards',
            code_files: [
              'frontend/src/app/auth/login.component.ts',
              'frontend/src/app/auth/auth.service.ts',
              'frontend/src/app/auth/auth.guard.ts'
            ],
            escalations: [],
            collaborations: []
          },
          {
            step: 'tester_validation',
            timestamp: '2024-01-01T00:04:00',
            agent: 'tester',
            status: 'completed',
            details: 'Comprehensive test suite created',
            output: 'Generated unit tests, integration tests, and Playwright E2E tests',
            code_files: [
              'backend/tests/test_auth.py',
              'tests/playwright/test_auth.spec.ts',
              'frontend/src/app/auth/auth.service.spec.ts'
            ],
            escalations: [],
            collaborations: []
          }
        ],
        created_at: '2024-01-01T00:00:00',
        collaboration_queue: [],
        escalation_queue: []
      };
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockWorkflowWithConversations)
      });
    });
  });

  test('should display chronological agent conversations', async ({ page }) => {
    await page.goto('/workflows/enhanced_story_NEGISHI-178');
    
    // Check that conversations are displayed in chronological order
    const conversations = page.locator('[data-testid="conversation"]');
    await expect(conversations).toHaveCount(5);
    
    // Verify conversation order (should be chronological)
    await expect(conversations.nth(0)).toContainText('story_retrieved');
    await expect(conversations.nth(1)).toContainText('architect_review');
    await expect(conversations.nth(2)).toContainText('developer_implementation');
    await expect(conversations.nth(3)).toContainText('frontend_implementation');
    await expect(conversations.nth(4)).toContainText('tester_validation');
  });

  test('should display agent names and roles', async ({ page }) => {
    await page.goto('/workflows/enhanced_story_NEGISHI-178');
    
    // Check agent names are displayed
    await expect(page.locator('text=pm')).toBeVisible();
    await expect(page.locator('text=architect')).toBeVisible();
    await expect(page.locator('text=developer')).toBeVisible();
    await expect(page.locator('text=frontend')).toBeVisible();
    await expect(page.locator('text=tester')).toBeVisible();
    
    // Check agent roles (if displayed)
    await expect(page.locator('text=Product Manager')).toBeVisible();
    await expect(page.locator('text=Solution Architect')).toBeVisible();
    await expect(page.locator('text=Backend Developer')).toBeVisible();
    await expect(page.locator('text=Frontend Developer')).toBeVisible();
    await expect(page.locator('text=QA Tester')).toBeVisible();
  });

  test('should display conversation details and outputs', async ({ page }) => {
    await page.goto('/workflows/enhanced_story_NEGISHI-178');
    
    // Check that conversation details are displayed
    await expect(page.locator('text=Story retrieved successfully from Jira')).toBeVisible();
    await expect(page.locator('text=Architecture plan created with security considerations')).toBeVisible();
    await expect(page.locator('text=Backend implementation completed with security features')).toBeVisible();
    
    // Check that agent outputs are displayed
    await expect(page.locator('text=Story: Implement user authentication system with JWT tokens')).toBeVisible();
    await expect(page.locator('text=Plan: Use JWT tokens with FastAPI backend')).toBeVisible();
    await expect(page.locator('text=Implemented JWT authentication endpoints')).toBeVisible();
  });

  test('should display code files generated by each agent', async ({ page }) => {
    await page.goto('/workflows/enhanced_story_NEGISHI-178');
    
    // Check architect's code files
    await expect(page.locator('text=backend/auth/jwt_handler.py')).toBeVisible();
    await expect(page.locator('text=backend/auth/security.py')).toBeVisible();
    
    // Check developer's code files
    await expect(page.locator('text=backend/auth/endpoints.py')).toBeVisible();
    await expect(page.locator('text=backend/auth/models.py')).toBeVisible();
    await expect(page.locator('text=backend/auth/middleware.py')).toBeVisible();
    
    // Check frontend's code files
    await expect(page.locator('text=frontend/src/app/auth/login.component.ts')).toBeVisible();
    await expect(page.locator('text=frontend/src/app/auth/auth.service.ts')).toBeVisible();
    await expect(page.locator('text=frontend/src/app/auth/auth.guard.ts')).toBeVisible();
    
    // Check tester's code files
    await expect(page.locator('text=backend/tests/test_auth.py')).toBeVisible();
    await expect(page.locator('text=tests/playwright/test_auth.spec.ts')).toBeVisible();
    await expect(page.locator('text=frontend/src/app/auth/auth.service.spec.ts')).toBeVisible();
  });

  test('should display escalations between agents', async ({ page }) => {
    await page.goto('/workflows/enhanced_story_NEGISHI-178');
    
    // Check that escalations are displayed
    await expect(page.locator('text=Complex security requirements need backend expertise')).toBeVisible();
    await expect(page.locator('text=architect → developer')).toBeVisible();
    await expect(page.locator('text=resolved')).toBeVisible();
  });

  test('should display collaborations between agents', async ({ page }) => {
    await page.goto('/workflows/enhanced_story_NEGISHI-178');
    
    // Check that collaborations are displayed
    await expect(page.locator('text=API_contract')).toBeVisible();
    await expect(page.locator('text=developer → frontend')).toBeVisible();
    await expect(page.locator('text=completed')).toBeVisible();
  });

  test('should display conversation timestamps', async ({ page }) => {
    await page.goto('/workflows/enhanced_story_NEGISHI-178');
    
    // Check that timestamps are displayed
    await expect(page.locator('text=2024-01-01T00:00:00')).toBeVisible();
    await expect(page.locator('text=2024-01-01T00:01:00')).toBeVisible();
    await expect(page.locator('text=2024-01-01T00:02:00')).toBeVisible();
    await expect(page.locator('text=2024-01-01T00:03:00')).toBeVisible();
    await expect(page.locator('text=2024-01-01T00:04:00')).toBeVisible();
  });

  test('should filter conversations by agent', async ({ page }) => {
    await page.goto('/workflows/enhanced_story_NEGISHI-178');
    
    // Click on developer filter
    await page.click('button:has-text("Developer")');
    
    // Verify only developer conversations are shown
    await expect(page.locator('text=developer_implementation')).toBeVisible();
    await expect(page.locator('text=story_retrieved')).not.toBeVisible();
    await expect(page.locator('text=architect_review')).not.toBeVisible();
  });

  test('should expand/collapse conversation details', async ({ page }) => {
    await page.goto('/workflows/enhanced_story_NEGISHI-178');
    
    // Click to expand first conversation
    await page.click('[data-testid="conversation"]:first-child [data-testid="expand-button"]');
    
    // Check that details are expanded
    await expect(page.locator('text=Story retrieved successfully from Jira')).toBeVisible();
    
    // Click to collapse
    await page.click('[data-testid="conversation"]:first-child [data-testid="collapse-button"]');
    
    // Check that details are collapsed
    await expect(page.locator('text=Story retrieved successfully from Jira')).not.toBeVisible();
  });

  test('should highlight active agent conversations', async ({ page }) => {
    await page.goto('/workflows/enhanced_story_NEGISHI-178');
    
    // Check that completed conversations have proper styling
    const completedConversations = page.locator('[data-testid="conversation"][data-status="completed"]');
    await expect(completedConversations).toHaveCount(5);
    
    // Verify status indicators
    await expect(page.locator('text=completed')).toBeVisible();
  });

  test('should display conversation flow visualization', async ({ page }) => {
    await page.goto('/workflows/enhanced_story_NEGISHI-178');
    
    // Check that conversation flow is displayed
    await expect(page.locator('[data-testid="conversation-flow"]')).toBeVisible();
    
    // Verify flow connections between agents
    await expect(page.locator('[data-testid="flow-connection"][data-from="pm"][data-to="architect"]')).toBeVisible();
    await expect(page.locator('[data-testid="flow-connection"][data-from="architect"][data-to="developer"]')).toBeVisible();
    await expect(page.locator('[data-testid="flow-connection"][data-from="developer"][data-to="frontend"]')).toBeVisible();
  });

  test('should handle empty conversation data', async ({ page }) => {
    // Mock workflow with empty conversations
    await page.route('**/workflows/empty_workflow', async route => {
      const emptyWorkflow = {
        id: 'empty_workflow',
        name: 'Empty Workflow',
        status: 'pending',
        conversations: [],
        created_at: '2024-01-01T00:00:00',
        collaboration_queue: [],
        escalation_queue: []
      };
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(emptyWorkflow)
      });
    });

    await page.goto('/workflows/empty_workflow');
    
    // Check for empty state message
    await expect(page.locator('text=No conversations yet')).toBeVisible();
  });

  test('should search conversations by content', async ({ page }) => {
    await page.goto('/workflows/enhanced_story_NEGISHI-178');
    
    // Use search functionality
    await page.fill('[data-testid="conversation-search"]', 'JWT');
    
    // Verify filtered results
    await expect(page.locator('text=JWT tokens')).toBeVisible();
    await expect(page.locator('text=JWT authentication')).toBeVisible();
    
    // Clear search
    await page.fill('[data-testid="conversation-search"]', '');
    
    // Verify all conversations are shown again
    await expect(page.locator('[data-testid="conversation"]')).toHaveCount(5);
  });
});
