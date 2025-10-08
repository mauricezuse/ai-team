import { test, expect } from '@playwright/test';

test.describe('Navigation and Routing Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Mock all API endpoints
    await page.route('**/workflows', async route => {
      const mockWorkflows = [
        {
          id: 'enhanced_story_NEGISHI-178',
          name: 'Enhanced Story Negishi-178',
          status: 'completed',
          agents: ['pm', 'architect', 'developer'],
          created_at: '2024-01-01T00:00:00'
        }
      ];
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockWorkflows)
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
        }
      ];
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAgents)
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
            details: 'Story retrieved successfully',
            output: 'Story details',
            code_files: [],
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
        body: JSON.stringify(mockWorkflowDetail)
      });
    });

    await page.route('**/agents/pm', async route => {
      const mockAgentDetail = {
        id: 'pm',
        name: 'Product Manager',
        role: 'Product Management',
        goal: 'Define product requirements and user stories',
        backstory: 'Experienced product manager',
        capabilities: ['Requirements analysis', 'User story creation']
      };
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAgentDetail)
      });
    });
  });

  test('should navigate between all main pages', async ({ page }) => {
    // Start at dashboard
    await page.goto('/dashboard');
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();
    await expect(page).toHaveURL(/.*dashboard/);

    // Navigate to workflows
    await page.click('text=Workflows', { first: true });
    await expect(page).toHaveURL(/.*workflows/);
    await expect(page.getByRole('heading', { name: 'Workflows' })).toBeVisible();

    // Navigate to agents
    await page.click('text=Agents', { first: true });
    await expect(page).toHaveURL(/.*agents/);
    await expect(page.getByRole('heading', { name: 'Agents' })).toBeVisible();

    // Navigate back to dashboard
    await page.click('text=Dashboard');
    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();
  });

  test('should handle direct URL navigation', async ({ page }) => {
    // Navigate directly to workflows
    await page.goto('/workflows');
    await expect(page.getByRole('heading', { name: 'Workflows' })).toBeVisible();
    await expect(page).toHaveURL(/.*workflows/);

    // Navigate directly to agents
    await page.goto('/agents');
    await expect(page.getByRole('heading', { name: 'Agents' })).toBeVisible();
    await expect(page).toHaveURL(/.*agents/);

    // Navigate directly to dashboard
    await page.goto('/dashboard');
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();
    await expect(page).toHaveURL(/.*dashboard/);
  });

  test('should navigate to workflow detail page', async ({ page }) => {
    await page.goto('/workflows');
    
    // Click on workflow to view details
    await page.click('[data-testid="view-workflow-button"]');
    await expect(page).toHaveURL(/.*workflows\/enhanced_story_NEGISHI-178/);
    await expect(page.locator('text=Enhanced Story Negishi-178')).toBeVisible();
  });

  test('should navigate to agent detail page', async ({ page }) => {
    await page.goto('/agents');
    
    // Click on agent to view details
    await page.click('[data-testid="view-agent-button"]');
    await expect(page).toHaveURL(/.*agents\/pm/);
    await expect(page.locator('text=Product Manager')).toBeVisible();
  });

  test('should handle browser back and forward navigation', async ({ page }) => {
    // Start at dashboard
    await page.goto('/dashboard');
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();

    // Navigate to workflows
    await page.click('text=Workflows', { first: true });
    await expect(page.getByRole('heading', { name: 'Workflows' })).toBeVisible();

    // Navigate to agents
    await page.click('text=Agents', { first: true });
    await expect(page.getByRole('heading', { name: 'Agents' })).toBeVisible();

    // Use browser back button
    await page.goBack();
    await expect(page.getByRole('heading', { name: 'Workflows' })).toBeVisible();
    await expect(page).toHaveURL(/.*workflows/);

    // Use browser back button again
    await page.goBack();
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();
    await expect(page).toHaveURL(/.*dashboard/);

    // Use browser forward button
    await page.goForward();
    await expect(page.getByRole('heading', { name: 'Workflows' })).toBeVisible();
    await expect(page).toHaveURL(/.*workflows/);
  });

  test('should handle invalid routes gracefully', async ({ page }) => {
    // Navigate to invalid route
    await page.goto('/invalid-route');
    
    // Should redirect to dashboard (based on wildcard route)
    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();
  });

  test('should maintain navigation state during page refreshes', async ({ page }) => {
    // Navigate to workflows
    await page.goto('/workflows');
    await expect(page.getByRole('heading', { name: 'Workflows' })).toBeVisible();

    // Refresh the page
    await page.reload();
    await expect(page.getByRole('heading', { name: 'Workflows' })).toBeVisible();
    await expect(page).toHaveURL(/.*workflows/);

    // Navigate to workflow detail
    await page.click('[data-testid="view-workflow-button"]');
    await expect(page).toHaveURL(/.*workflows\/enhanced_story_NEGISHI-178/);

    // Refresh the page
    await page.reload();
    await expect(page.locator('text=Enhanced Story Negishi-178')).toBeVisible();
    await expect(page).toHaveURL(/.*workflows\/enhanced_story_NEGISHI-178/);
  });

  test('should handle deep linking to workflow detail', async ({ page }) => {
    // Navigate directly to workflow detail
    await page.goto('/workflows/enhanced_story_NEGISHI-178');
    await expect(page.locator('text=Enhanced Story Negishi-178')).toBeVisible();
    await expect(page).toHaveURL(/.*workflows\/enhanced_story_NEGISHI-178/);
  });

  test('should handle deep linking to agent detail', async ({ page }) => {
    // Navigate directly to agent detail
    await page.goto('/agents/pm');
    await expect(page.locator('text=Product Manager')).toBeVisible();
    await expect(page).toHaveURL(/.*agents\/pm/);
  });

  test('should handle navigation with query parameters', async ({ page }) => {
    // Navigate with query parameters
    await page.goto('/workflows?status=completed');
    await expect(page.getByRole('heading', { name: 'Workflows' })).toBeVisible();
    await expect(page).toHaveURL(/.*workflows/);
  });

  test('should handle navigation with hash fragments', async ({ page }) => {
    // Navigate with hash fragment
    await page.goto('/workflows#section1');
    await expect(page.getByRole('heading', { name: 'Workflows' })).toBeVisible();
    await expect(page).toHaveURL(/.*workflows/);
  });

  test('should handle rapid navigation between pages', async ({ page }) => {
    // Rapidly navigate between pages
    await page.goto('/dashboard');
    await page.goto('/workflows');
    await page.goto('/agents');
    await page.goto('/dashboard');
    await page.goto('/workflows');

    // Should end up on workflows page
    await expect(page.getByRole('heading', { name: 'Workflows' })).toBeVisible();
    await expect(page).toHaveURL(/.*workflows/);
  });

  test('should handle navigation during API loading', async ({ page }) => {
    // Mock slow API response
    await page.route('**/workflows', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      const mockWorkflows = [
        {
          id: 'test_workflow',
          name: 'Test Workflow',
          status: 'completed',
          agents: ['pm'],
          created_at: '2024-01-01T00:00:00'
        }
      ];
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockWorkflows)
      });
    });

    // Navigate to workflows while API is loading
    await page.goto('/workflows');
    
    // Navigate away before API completes
    await page.click('text=Agents', { first: true });
    await expect(page.getByRole('heading', { name: 'Agents' })).toBeVisible();
    await expect(page).toHaveURL(/.*agents/);
  });

  test('should handle navigation with browser history', async ({ page }) => {
    // Create a navigation history
    await page.goto('/dashboard');
    await page.goto('/workflows');
    await page.goto('/agents');
    await page.goto('/workflows/enhanced_story_NEGISHI-178');
    await page.goto('/agents/pm');

    // Use browser back button multiple times
    await page.goBack();
    await expect(page.locator('text=Enhanced Story Negishi-178')).toBeVisible();
    await expect(page).toHaveURL(/.*workflows\/enhanced_story_NEGISHI-178/);

    await page.goBack();
    await expect(page.getByRole('heading', { name: 'Agents' })).toBeVisible();
    await expect(page).toHaveURL(/.*agents/);

    await page.goBack();
    await expect(page.getByRole('heading', { name: 'Workflows' })).toBeVisible();
    await expect(page).toHaveURL(/.*workflows/);

    await page.goBack();
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();
    await expect(page).toHaveURL(/.*dashboard/);
  });

  test('should handle navigation with keyboard shortcuts', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Use Alt+Left arrow to go back (if supported by browser)
    await page.keyboard.press('Alt+ArrowLeft');
    // Note: This might not work in all browsers, but it tests the functionality
    
    // Use Alt+Right arrow to go forward (if supported by browser)
    await page.keyboard.press('Alt+ArrowRight');
  });

  test('should handle navigation with middle-click', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Middle-click on workflows link (opens in new tab)
    await page.click('text=Workflows', { button: 'middle' });
    
    // Should open in new tab, original tab should remain on dashboard
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();
  });

  test('should handle navigation with right-click context menu', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Right-click on workflows link
    await page.click('text=Workflows', { button: 'right' });
    
    // Context menu should appear (this is browser-dependent)
    // The main test is that the page doesn't crash
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();
  });

  test('should handle navigation with touch gestures on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto('/dashboard');
    
    // Test touch navigation
    await page.click('text=Workflows', { first: true });
    await expect(page.getByRole('heading', { name: 'Workflows' })).toBeVisible();
    await expect(page).toHaveURL(/.*workflows/);
    
    await page.click('text=Agents', { first: true });
    await expect(page.getByRole('heading', { name: 'Agents' })).toBeVisible();
    await expect(page).toHaveURL(/.*agents/);
  });
});
