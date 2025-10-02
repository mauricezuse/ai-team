import { test, expect } from '@playwright/test';

test.describe('Dashboard Functionality Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API endpoints for dashboard
    await page.route('**/agents', async route => {
      const mockAgents = [
        { id: 'pm', name: 'Product Manager', role: 'Product Management', goal: 'Define product requirements' },
        { id: 'architect', name: 'Solution Architect', role: 'Architecture', goal: 'Design system architecture' },
        { id: 'developer', name: 'Backend Developer', role: 'Backend Development', goal: 'Implement backend services' },
        { id: 'frontend', name: 'Frontend Developer', role: 'Frontend Development', goal: 'Implement user interfaces' },
        { id: 'tester', name: 'QA Tester', role: 'Quality Assurance', goal: 'Ensure code quality' },
        { id: 'reviewer', name: 'Code Reviewer', role: 'Code Review', goal: 'Review code for quality' }
      ];
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAgents)
      });
    });

    await page.route('**/workflows', async route => {
      const mockWorkflows = [
        {
          id: 'enhanced_story_NEGISHI-178',
          name: 'Enhanced Story Negishi-178',
          status: 'completed',
          agents: ['pm', 'architect', 'developer'],
          created_at: '2024-01-01T00:00:00'
        },
        {
          id: 'enhanced_story_NEGISHI-175',
          name: 'Enhanced Story Negishi-175',
          status: 'pending',
          agents: ['pm'],
          created_at: '2024-01-01T01:00:00'
        },
        {
          id: 'enhanced_story_NEGISHI-180',
          name: 'Enhanced Story Negishi-180',
          status: 'running',
          agents: ['pm', 'architect'],
          created_at: '2024-01-01T02:00:00'
        }
      ];
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockWorkflows)
      });
    });
  });

  test('should display dashboard with correct agent and workflow counts', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Check dashboard title
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();
    
    // Check agent count
    await expect(page.locator('text=Agents')).toBeVisible();
    await expect(page.locator('text=6')).toBeVisible(); // 6 agents from mock data
    
    // Check workflow count
    await expect(page.locator('text=Workflows')).toBeVisible();
    await expect(page.locator('text=3')).toBeVisible(); // 3 workflows from mock data
  });

  test('should handle API errors gracefully on dashboard', async ({ page }) => {
    // Mock API error for agents
    await page.route('**/agents', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal server error' })
      });
    });

    await page.goto('/dashboard');
    
    // Dashboard should still load even with API errors
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();
    await expect(page.locator('text=Agents')).toBeVisible();
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should handle empty data gracefully', async ({ page }) => {
    // Mock empty responses
    await page.route('**/agents', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([])
      });
    });

    await page.route('**/workflows', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([])
      });
    });

    await page.goto('/dashboard');
    
    // Should show zero counts
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();
    await expect(page.locator('text=Agents')).toBeVisible();
    await expect(page.locator('text=0')).toBeVisible();
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should be responsive on mobile devices', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto('/dashboard');
    
    // Check that dashboard content is still visible and properly laid out
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();
    await expect(page.locator('text=Agents')).toBeVisible();
    await expect(page.locator('text=Workflows')).toBeVisible();
    
    // Check that counts are visible
    await expect(page.locator('text=6')).toBeVisible();
    await expect(page.locator('text=3')).toBeVisible();
  });

  test('should load dashboard quickly', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/dashboard');
    
    // Wait for content to be visible
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();
    await expect(page.locator('text=Agents')).toBeVisible();
    await expect(page.locator('text=Workflows')).toBeVisible();
    
    const loadTime = Date.now() - startTime;
    
    // Dashboard should load within 3 seconds
    expect(loadTime).toBeLessThan(3000);
  });

  test('should handle slow API responses', async ({ page }) => {
    // Mock slow API responses
    await page.route('**/agents', async route => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      const mockAgents = [
        { id: 'pm', name: 'Product Manager', role: 'Product Management', goal: 'Define product requirements' }
      ];
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAgents)
      });
    });

    await page.route('**/workflows', async route => {
      await new Promise(resolve => setTimeout(resolve, 1500));
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

    await page.goto('/dashboard');
    
    // Should show loading state initially, then update with data
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();
    
    // Wait for data to load
    await expect(page.locator('text=1')).toBeVisible(); // Agent count
    await expect(page.locator('text=1')).toBeVisible(); // Workflow count
  });

  test('should maintain dashboard state during navigation', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Verify initial state
    await expect(page.locator('text=6')).toBeVisible(); // Agent count
    await expect(page.locator('text=3')).toBeVisible(); // Workflow count
    
    // Navigate to workflows
    await page.click('text=Workflows');
    await expect(page).toHaveURL(/.*workflows/);
    
    // Navigate back to dashboard
    await page.click('text=Dashboard');
    await expect(page).toHaveURL(/.*dashboard/);
    
    // Dashboard should still show the same counts
    await expect(page.locator('text=6')).toBeVisible(); // Agent count
    await expect(page.locator('text=3')).toBeVisible(); // Workflow count
  });

  test('should display dashboard with different data sets', async ({ page }) => {
    // Mock different data set
    await page.route('**/agents', async route => {
      const mockAgents = [
        { id: 'pm', name: 'Product Manager', role: 'Product Management', goal: 'Define product requirements' },
        { id: 'architect', name: 'Solution Architect', role: 'Architecture', goal: 'Design system architecture' }
      ];
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAgents)
      });
    });

    await page.route('**/workflows', async route => {
      const mockWorkflows = [
        {
          id: 'workflow_1',
          name: 'Workflow 1',
          status: 'completed',
          agents: ['pm'],
          created_at: '2024-01-01T00:00:00'
        },
        {
          id: 'workflow_2',
          name: 'Workflow 2',
          status: 'pending',
          agents: ['architect'],
          created_at: '2024-01-01T01:00:00'
        },
        {
          id: 'workflow_3',
          name: 'Workflow 3',
          status: 'running',
          agents: ['pm', 'architect'],
          created_at: '2024-01-01T02:00:00'
        },
        {
          id: 'workflow_4',
          name: 'Workflow 4',
          status: 'error',
          agents: ['pm'],
          created_at: '2024-01-01T03:00:00'
        }
      ];
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockWorkflows)
      });
    });

    await page.goto('/dashboard');
    
    // Should show updated counts
    await expect(page.locator('text=2')).toBeVisible(); // Agent count
    await expect(page.locator('text=4')).toBeVisible(); // Workflow count
  });

  test('should handle network failures gracefully', async ({ page }) => {
    // Mock network failure
    await page.route('**/agents', async route => {
      await route.abort('failed');
    });

    await page.route('**/workflows', async route => {
      await route.abort('failed');
    });

    await page.goto('/dashboard');
    
    // Dashboard should still load even with network failures
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();
    await expect(page.locator('text=Agents')).toBeVisible();
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should display dashboard with real-time updates', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Verify initial state
    await expect(page.locator('text=6')).toBeVisible(); // Agent count
    await expect(page.locator('text=3')).toBeVisible(); // Workflow count
    
    // Mock updated data
    await page.route('**/agents', async route => {
      const mockAgents = [
        { id: 'pm', name: 'Product Manager', role: 'Product Management', goal: 'Define product requirements' },
        { id: 'architect', name: 'Solution Architect', role: 'Architecture', goal: 'Design system architecture' },
        { id: 'developer', name: 'Backend Developer', role: 'Backend Development', goal: 'Implement backend services' },
        { id: 'frontend', name: 'Frontend Developer', role: 'Frontend Development', goal: 'Implement user interfaces' },
        { id: 'tester', name: 'QA Tester', role: 'Quality Assurance', goal: 'Ensure code quality' },
        { id: 'reviewer', name: 'Code Reviewer', role: 'Code Review', goal: 'Review code for quality' },
        { id: 'new_agent', name: 'New Agent', role: 'New Role', goal: 'New goal' }
      ];
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAgents)
      });
    });

    // Refresh the page to get updated data
    await page.reload();
    
    // Should show updated agent count
    await expect(page.locator('text=7')).toBeVisible(); // Updated agent count
  });
});
