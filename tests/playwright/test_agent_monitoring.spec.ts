import { test, expect } from '@playwright/test';

test.describe('Agent Conversation Monitoring', () => {
  test.beforeEach(async ({ page }) => {
    // Mock comprehensive workflow data with detailed agent conversations
    await page.route('**/workflows', async route => {
      const workflows = [
        {
          id: 'enhanced_story_NEGISHI-175',
          name: 'Enhanced Story NEGISHI-175',
          status: 'completed',
          agents: ['pm', 'architect', 'developer', 'frontend', 'tester', 'reviewer'],
          created_at: '2024-07-20T10:00:00.000Z',
          last_step: 'pr_created'
        },
        {
          id: 'enhanced_story_NEGISHI-178',
          name: 'Enhanced Story NEGISHI-178',
          status: 'running',
          agents: ['pm', 'architect', 'developer'],
          created_at: '2024-07-21T11:00:00.000Z',
          last_step: 'developer_implementation'
        }
      ];
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(workflows)
      });
    });

    await page.route('**/workflows/enhanced_story_NEGISHI-175', async route => {
      const workflowDetail = {
        id: 'enhanced_story_NEGISHI-175',
        name: 'Enhanced Story NEGISHI-175',
        status: 'completed',
        created_at: '2024-07-20T10:00:00.000Z',
        conversations: [
          {
            step: 'story_retrieved',
            timestamp: '2024-07-20T10:00:05.000Z',
            agent: 'pm',
            status: 'completed',
            details: 'Jira story NEGISHI-175 retrieved successfully.',
            output: 'Story: Implement user profile management with avatar upload functionality',
            code_files: [],
            escalations: [],
            collaborations: []
          },
          {
            step: 'architect_plan',
            timestamp: '2024-07-20T10:01:00.000Z',
            agent: 'architect',
            status: 'completed',
            details: 'Architect generated comprehensive implementation plan.',
            output: 'Plan: Backend API for profile management, Frontend profile component with avatar upload, Database schema for user profiles',
            code_files: ['backend/models/user_profile.py', 'backend/schemas/profile_schema.py'],
            escalations: [],
            collaborations: [
              {
                from_agent: 'architect',
                to_agent: 'developer',
                request_type: 'API Specification',
                status: 'pending'
              }
            ]
          },
          {
            step: 'developer_implementation',
            timestamp: '2024-07-20T10:05:00.000Z',
            agent: 'developer',
            status: 'completed',
            details: 'Backend profile management API implemented with file upload support.',
            output: 'def update_profile(): ... def upload_avatar(): ...',
            code_files: [
              'backend/api/profile.py',
              'backend/services/file_upload.py',
              'backend/models/user_profile.py'
            ],
            escalations: [
              {
                from_agent: 'developer',
                to_agent: 'architect',
                reason: 'Complex file upload validation requirements',
                status: 'resolved'
              }
            ],
            collaborations: [
              {
                from_agent: 'developer',
                to_agent: 'frontend',
                request_type: 'API Contract',
                status: 'completed'
              }
            ]
          },
          {
            step: 'frontend_implementation',
            timestamp: '2024-07-20T10:15:00.000Z',
            agent: 'frontend',
            status: 'completed',
            details: 'Frontend profile component with drag-and-drop avatar upload.',
            output: '<app-profile-edit></app-profile-edit>',
            code_files: [
              'frontend/src/app/profile/profile-edit.component.ts',
              'frontend/src/app/profile/profile-edit.component.html',
              'frontend/src/app/profile/avatar-upload.component.ts'
            ],
            escalations: [],
            collaborations: []
          },
          {
            step: 'tester_tests',
            timestamp: '2024-07-20T10:20:00.000Z',
            agent: 'tester',
            status: 'completed',
            details: 'Comprehensive test suite generated including unit, integration, and E2E tests.',
            output: 'test_profile_api.py, test_avatar_upload.py, test_profile_edit.spec.ts',
            code_files: [
              'tests/backend/test_profile_api.py',
              'tests/backend/test_file_upload.py',
              'tests/playwright/test_profile_edit.spec.ts',
              'tests/integration/test_profile_flow.py'
            ],
            escalations: [],
            collaborations: []
          },
          {
            step: 'reviewer_review',
            timestamp: '2024-07-20T10:25:00.000Z',
            agent: 'reviewer',
            status: 'completed',
            details: 'Code review completed with security and performance recommendations.',
            output: 'Review: File upload validation needs improvement, consider rate limiting for avatar uploads',
            code_files: [],
            escalations: [],
            collaborations: []
          }
        ],
        collaboration_queue: [],
        escalation_queue: []
      };
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(workflowDetail)
      });
    });

    await page.route('**/agents', async route => {
      const agents = [
        { id: 'pm', name: 'Product Manager', role: 'Product Management', goal: 'Define product requirements' },
        { id: 'architect', name: 'Solution Architect', role: 'Architecture', goal: 'Design system architecture' },
        { id: 'developer', name: 'Backend Developer', role: 'Backend Development', goal: 'Implement backend services' },
        { id: 'frontend', name: 'Frontend Developer', role: 'Frontend Development', goal: 'Implement user interfaces' },
        { id: 'tester', name: 'QA Tester', role: 'Quality Assurance', goal: 'Ensure code quality' },
        { id: 'reviewer', name: 'Code Reviewer', role: 'Code Review', goal: 'Review code' }
      ];
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(agents)
      });
    });

    // Navigate to home and click Workflows in the top menubar for robust routing
    await page.goto('http://localhost:4001/');
    await page.waitForLoadState('domcontentloaded');
    // PrimeNG menubar items are menuitem role
    await page.getByRole('menuitem', { name: /Workflows/i }).click({ timeout: 10000 });
    await expect(page).toHaveURL(/\/workflows(\/?$)/);
    // Wait for either table or a workflow name to appear
    await Promise.race([
      page.getByRole('table').waitFor({ timeout: 10000 }).catch(() => {}),
      page.getByText('Enhanced Story NEGISHI-175').waitFor({ timeout: 10000 }).catch(() => {})
    ]);
  });

  test('should display workflow list with agent monitoring capabilities', async ({ page }) => {
    // Heading might be off-screen on mobile; assert presence of table or rows instead
    await Promise.race([
      page.getByRole('table').waitFor({ timeout: 5000 }).catch(() => {}),
      page.getByTestId('workflow-row').first().waitFor({ timeout: 5000 }).catch(() => {})
    ]);
    
    // Verify workflow entries show agent involvement
    await expect(page.getByText('Enhanced Story NEGISHI-175')).toBeVisible();
    await expect(page.getByText('Enhanced Story NEGISHI-178')).toBeVisible();
    
    // Check status indicators using specific workflow status badges
    const statusBadges = page.getByTestId('workflow-status');
    await expect(statusBadges.filter({ hasText: 'completed' }).first()).toBeVisible();
    await expect(statusBadges.filter({ hasText: 'running' }).first()).toBeVisible();
  });

  test('should navigate to workflow detail and show comprehensive agent conversations', async ({ page }) => {
    await page.getByText('Enhanced Story NEGISHI-175').click();
    await expect(page.url()).toContain('/workflows/enhanced_story_NEGISHI-175');
    
    // Verify workflow header
    await expect(page.getByText('Enhanced Story NEGISHI-175')).toBeVisible();
    await expect(page.getByText('Status: completed')).toBeVisible();
    
    // Verify agent involvement display
    await expect(page.getByText('Agents Involved')).toBeVisible();
    await expect(page.locator('.agent-chips .p-chip').count()).toBe(6);
    
    // Verify conversation list
    await expect(page.getByText('Agent Conversations')).toBeVisible();
    const conversations = page.locator('[data-testid="conversation"]');
    await expect(conversations).toHaveCount(6);
  });

  test('should display detailed agent conversation information', async ({ page }) => {
    await page.getByText('Enhanced Story NEGISHI-175').click();
    
    const conversations = page.locator('[data-testid="conversation"]');
    
    // Test PM conversation
    const pmConversation = conversations.nth(0);
    await expect(pmConversation.locator('.agent-badge')).toHaveText('pm');
    await expect(pmConversation.locator('.step-badge')).toHaveText('story_retrieved');
    await pmConversation.getByTestId('expand-button').click();
    await expect(pmConversation.getByText('Story: Implement user profile management with avatar upload functionality')).toBeVisible();
    
    // Test Architect conversation with collaborations
    const architectConversation = conversations.nth(1);
    await expect(architectConversation.locator('.agent-badge')).toHaveText('architect');
    await architectConversation.getByTestId('expand-button').click();
    await expect(architectConversation.getByText('Collaborations:')).toBeVisible();
    await expect(architectConversation.getByText('architect → developer')).toBeVisible();
    await expect(architectConversation.getByText('API Specification')).toBeVisible();
    
    // Test Developer conversation with escalations and collaborations
    const devConversation = conversations.nth(2);
    await expect(devConversation.locator('.agent-badge')).toHaveText('developer');
    await devConversation.getByTestId('expand-button').click();
    await expect(devConversation.getByText('Escalations:')).toBeVisible();
    await expect(devConversation.getByText('developer → architect')).toBeVisible();
    await expect(devConversation.getByText('Complex file upload validation requirements')).toBeVisible();
    await expect(devConversation.getByText('Collaborations:')).toBeVisible();
    await expect(devConversation.getByText('developer → frontend')).toBeVisible();
    
    // Test code files display
    await expect(devConversation.getByText('Code Files Generated:')).toBeVisible();
    await expect(devConversation.getByText('backend/api/profile.py')).toBeVisible();
    await expect(devConversation.getByText('backend/services/file_upload.py')).toBeVisible();
  });

  test('should filter conversations by specific agent', async ({ page }) => {
    await page.getByText('Enhanced Story NEGISHI-175').click();
    
    // Filter by developer
    await page.locator('.agent-filter').selectOption({ label: 'developer' });
    const conversations = page.locator('[data-testid="conversation"]');
    await expect(conversations).toHaveCount(1);
    await expect(conversations.first().locator('.agent-badge')).toHaveText('developer');
    
    // Filter by tester
    await page.locator('.agent-filter').selectOption({ label: 'tester' });
    await expect(conversations).toHaveCount(1);
    await expect(conversations.first().locator('.agent-badge')).toHaveText('tester');
    
    // Show all agents
    await page.locator('.agent-filter').selectOption({ label: 'All Agents' });
    await expect(conversations).toHaveCount(6);
  });

  test('should search conversations by content', async ({ page }) => {
    await page.getByText('Enhanced Story NEGISHI-175').click();
    
    // Search for "upload"
    await page.getByPlaceholder('Search conversations...').fill('upload');
    const conversations = page.locator('[data-testid="conversation"]');
    await expect(conversations).toHaveCount(2); // developer and frontend conversations
    
    // Search for "API"
    await page.getByPlaceholder('Search conversations...').clear();
    await page.getByPlaceholder('Search conversations...').fill('API');
    await expect(conversations).toHaveCount(2); // architect and developer conversations
    
    // Clear search
    await page.getByPlaceholder('Search conversations...').clear();
    await expect(conversations).toHaveCount(6);
  });

  test('should display escalation and collaboration details', async ({ page }) => {
    await page.getByText('Enhanced Story NEGISHI-175').click();
    
    const devConversation = page.locator('[data-testid="conversation"]').nth(2);
    await devConversation.getByTestId('expand-button').click();
    
    // Verify escalation details
    await expect(devConversation.getByText('Escalations:')).toBeVisible();
    await expect(devConversation.getByText('developer → architect')).toBeVisible();
    await expect(devConversation.getByText('Complex file upload validation requirements')).toBeVisible();
    await expect(devConversation.getByText('resolved')).toBeVisible();
    
    // Verify collaboration details
    await expect(devConversation.getByText('Collaborations:')).toBeVisible();
    await expect(devConversation.getByText('developer → frontend')).toBeVisible();
    await expect(devConversation.getByText('API Contract')).toBeVisible();
    await expect(devConversation.getByText('completed')).toBeVisible();
  });

  test('should display code files for each agent', async ({ page }) => {
    await page.getByText('Enhanced Story NEGISHI-175').click();
    
    // Test architect code files
    const architectConversation = page.locator('[data-testid="conversation"]').nth(1);
    await architectConversation.getByTestId('expand-button').click();
    await expect(architectConversation.getByText('Code Files Generated:')).toBeVisible();
    await expect(architectConversation.getByText('backend/models/user_profile.py')).toBeVisible();
    await expect(architectConversation.getByText('backend/schemas/profile_schema.py')).toBeVisible();
    
    // Test developer code files
    const devConversation = page.locator('[data-testid="conversation"]').nth(2);
    await devConversation.getByTestId('expand-button').click();
    await expect(devConversation.getByText('backend/api/profile.py')).toBeVisible();
    await expect(devConversation.getByText('backend/services/file_upload.py')).toBeVisible();
    
    // Test tester code files
    const testerConversation = page.locator('[data-testid="conversation"]').nth(4);
    await testerConversation.getByTestId('expand-button').click();
    await expect(testerConversation.getByText('tests/backend/test_profile_api.py')).toBeVisible();
    await expect(testerConversation.getByText('tests/playwright/test_profile_edit.spec.ts')).toBeVisible();
  });

  test('should show conversation timestamps and status', async ({ page }) => {
    await page.getByText('Enhanced Story NEGISHI-175').click();
    
    const conversations = page.locator('[data-testid="conversation"]');
    
    // Check timestamps are displayed
    await expect(conversations.first().locator('.timestamp')).toBeVisible();
    
    // Check status badges
    await expect(conversations.first().locator('.status-badge')).toHaveText('completed');
    
    // Verify conversation order (chronological)
    const pmConversation = conversations.nth(0);
    const architectConversation = conversations.nth(1);
    const devConversation = conversations.nth(2);
    
    await expect(pmConversation.locator('.step-badge')).toHaveText('story_retrieved');
    await expect(architectConversation.locator('.step-badge')).toHaveText('architect_plan');
    await expect(devConversation.locator('.step-badge')).toHaveText('developer_implementation');
  });

  test('should handle workflow execution and status updates', async ({ page }) => {
    // Mock workflow execution
    await page.route('**/workflows/enhanced_story_NEGISHI-175/execute', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ 
          message: 'Workflow executed successfully', 
          status: 'completed',
          results: [
            { step: 'story_retrieved', agent: 'pm', status: 'completed' },
            { step: 'architect_plan', agent: 'architect', status: 'completed' }
          ]
        })
      });
    });

    await page.getByText('Enhanced Story NEGISHI-175').click();
    
    // Execute workflow
    await page.getByRole('button', { name: 'Execute' }).click();
    await expect(page.getByText('Workflow execution started...')).toBeVisible();
    
    // Verify success message
    await expect(page.getByText('Workflow executed successfully')).toBeVisible();
  });

  test('should refresh workflow data and show updated conversations', async ({ page }) => {
    let requestCount = 0;
    await page.route('**/workflows/enhanced_story_NEGISHI-175', async route => {
      requestCount++;
      const workflowDetail = {
        id: 'enhanced_story_NEGISHI-175',
        name: 'Enhanced Story NEGISHI-175',
        status: requestCount === 1 ? 'running' : 'completed',
        created_at: '2024-07-20T10:00:00.000Z',
        conversations: requestCount === 1 ? [
          {
            step: 'story_retrieved',
            timestamp: '2024-07-20T10:00:05.000Z',
            agent: 'pm',
            status: 'completed',
            details: 'Jira story NEGISHI-175 retrieved successfully.',
            output: 'Story: Implement user profile management',
            code_files: [],
            escalations: [],
            collaborations: []
          }
        ] : [
          {
            step: 'story_retrieved',
            timestamp: '2024-07-20T10:00:05.000Z',
            agent: 'pm',
            status: 'completed',
            details: 'Jira story NEGISHI-175 retrieved successfully.',
            output: 'Story: Implement user profile management',
            code_files: [],
            escalations: [],
            collaborations: []
          },
          {
            step: 'architect_plan',
            timestamp: '2024-07-20T10:01:00.000Z',
            agent: 'architect',
            status: 'completed',
            details: 'Architect generated implementation plan.',
            output: 'Plan: Backend API for profile management',
            code_files: [],
            escalations: [],
            collaborations: []
          }
        ],
        collaboration_queue: [],
        escalation_queue: []
      };
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(workflowDetail)
      });
    });

    await page.getByText('Enhanced Story NEGISHI-175').click();
    
    // Initial state - running with 1 conversation
    await expect(page.getByText('Status: running')).toBeVisible();
    await expect(page.locator('[data-testid="conversation"]')).toHaveCount(1);
    
    // Refresh to get updated data
    await page.getByRole('button', { name: 'Refresh' }).click();
    await expect(page.getByText('Status: completed')).toBeVisible();
    await expect(page.locator('[data-testid="conversation"]')).toHaveCount(2);
  });
});
