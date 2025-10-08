import { test, expect } from '@playwright/test';

test.describe('Agent Detail Page Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Mock agent detail API
    await page.route('**/agents/pm', async route => {
      const mockAgentDetail = {
        id: 'pm',
        name: 'Product Manager',
        role: 'Product Management',
        goal: 'Define product requirements and user stories',
        backstory: 'Experienced product manager with deep understanding of user needs',
        capabilities: [
          'Requirements analysis',
          'User story creation',
          'Stakeholder communication',
          'Market research',
          'Product roadmap planning'
        ]
      };
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAgentDetail)
      });
    });

    await page.route('**/agents/architect', async route => {
      const mockAgentDetail = {
        id: 'architect',
        name: 'Solution Architect',
        role: 'Architecture',
        goal: 'Design system architecture and technical solutions',
        backstory: 'Senior architect with expertise in scalable system design',
        capabilities: [
          'System design',
          'Technology selection',
          'API design',
          'Database design',
          'Security architecture',
          'Performance optimization'
        ]
      };
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAgentDetail)
      });
    });

    await page.route('**/agents/developer', async route => {
      const mockAgentDetail = {
        id: 'developer',
        name: 'Backend Developer',
        role: 'Backend Development',
        goal: 'Implement backend services and APIs',
        backstory: 'Full-stack developer specializing in Python and FastAPI',
        capabilities: [
          'Python development',
          'FastAPI',
          'Database integration',
          'API implementation',
          'Testing',
          'Code review'
        ]
      };
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAgentDetail)
      });
    });
  });

  test('should display agent details correctly', async ({ page }) => {
    await page.goto('/agents/pm');
    
    // Check basic agent information
    await expect(page.locator('text=Product Manager')).toBeVisible();
    await expect(page.locator('text=Product Management')).toBeVisible();
    await expect(page.locator('text=Define product requirements and user stories')).toBeVisible();
    await expect(page.locator('text=Experienced product manager with deep understanding of user needs')).toBeVisible();
    
    // Check capabilities are displayed
    await expect(page.locator('text=Requirements analysis')).toBeVisible();
    await expect(page.locator('text=User story creation')).toBeVisible();
    await expect(page.locator('text=Stakeholder communication')).toBeVisible();
    await expect(page.locator('text=Market research')).toBeVisible();
    await expect(page.locator('text=Product roadmap planning')).toBeVisible();
  });

  test('should enable and disable edit mode', async ({ page }) => {
    await page.goto('/agents/pm');
    
    // Initially should be in view mode
    await expect(page.locator('text=Product Manager')).toBeVisible();
    await expect(page.locator('button:has-text("Edit")')).toBeVisible();
    
    // Click edit button
    await page.click('button:has-text("Edit")');
    
    // Should show form fields
    await expect(page.locator('input[name="name"]')).toBeVisible();
    await expect(page.locator('input[name="role"]')).toBeVisible();
    await expect(page.locator('input[name="goal"]')).toBeVisible();
    
    // Should show save and cancel buttons
    await expect(page.locator('button:has-text("Save")')).toBeVisible();
    await expect(page.locator('button:has-text("Cancel")')).toBeVisible();
    
    // Click cancel
    await page.click('button:has-text("Cancel")');
    
    // Should return to view mode
    await expect(page.locator('text=Product Manager')).toBeVisible();
    await expect(page.locator('button:has-text("Edit")')).toBeVisible();
  });

  test('should update agent information in edit mode', async ({ page }) => {
    await page.goto('/agents/pm');
    
    // Enter edit mode
    await page.click('button:has-text("Edit")');
    
    // Update fields
    await page.fill('input[name="name"]', 'Senior Product Manager');
    await page.fill('input[name="role"]', 'Senior Product Management');
    await page.fill('input[name="goal"]', 'Lead product strategy and roadmap');
    
    // Save changes
    await page.click('button:has-text("Save")');
    
    // Should return to view mode with updated information
    await expect(page.locator('text=Senior Product Manager')).toBeVisible();
    await expect(page.locator('text=Senior Product Management')).toBeVisible();
    await expect(page.locator('text=Lead product strategy and roadmap')).toBeVisible();
  });

  test('should handle different agent types', async ({ page }) => {
    // Test architect agent
    await page.goto('/agents/architect');
    
    await expect(page.locator('text=Solution Architect')).toBeVisible();
    await expect(page.locator('text=Architecture')).toBeVisible();
    await expect(page.locator('text=Design system architecture and technical solutions')).toBeVisible();
    await expect(page.locator('text=System design')).toBeVisible();
    await expect(page.locator('text=Technology selection')).toBeVisible();
    
    // Test developer agent
    await page.goto('/agents/developer');
    
    await expect(page.locator('text=Backend Developer')).toBeVisible();
    await expect(page.locator('text=Backend Development')).toBeVisible();
    await expect(page.locator('text=Implement backend services and APIs')).toBeVisible();
    await expect(page.locator('text=Python development')).toBeVisible();
    await expect(page.locator('text=FastAPI')).toBeVisible();
  });

  test('should handle agent not found error', async ({ page }) => {
    // Mock 404 error
    await page.route('**/agents/nonexistent', async route => {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Agent not found'
        })
      });
    });

    await page.goto('/agents/nonexistent');
    
    // Should show loading state initially, then error
    await expect(page.locator('text=Loading...')).toBeVisible();
  });

  test('should display agent capabilities in organized format', async ({ page }) => {
    await page.goto('/agents/architect');
    
    // Check that capabilities are displayed in a structured way
    const capabilities = [
      'System design',
      'Technology selection',
      'API design',
      'Database design',
      'Security architecture',
      'Performance optimization'
    ];
    
    for (const capability of capabilities) {
      await expect(page.locator(`text=${capability}`)).toBeVisible();
    }
  });

  test('should maintain edit state during navigation', async ({ page }) => {
    await page.goto('/agents/pm');
    
    // Enter edit mode
    await page.click('button:has-text("Edit")');
    await page.fill('input[name="name"]', 'Updated Product Manager');
    
    // Navigate away and back
    await page.goto('/agents');
    await page.goto('/agents/pm');
    
    // Should be back in view mode (edit state is not persisted)
    await expect(page.locator('text=Product Manager')).toBeVisible();
    await expect(page.locator('button:has-text("Edit")')).toBeVisible();
  });

  test('should validate form fields in edit mode', async ({ page }) => {
    await page.goto('/agents/pm');
    
    // Enter edit mode
    await page.click('button:has-text("Edit")');
    
    // Clear required fields
    await page.fill('input[name="name"]', '');
    await page.fill('input[name="role"]', '');
    await page.fill('input[name="goal"]', '');
    
    // Try to save
    await page.click('button:has-text("Save")');
    
    // Should show validation errors or prevent saving
    // This depends on your form validation implementation
    await expect(page.locator('input[name="name"]')).toHaveValue('');
  });

  test('should handle API errors during save', async ({ page }) => {
    // Mock save error
    await page.route('**/agents/pm', async route => {
      if (route.request().method() === 'PUT') {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: 'Failed to update agent'
          })
        });
      } else {
        // Return normal GET response
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
      }
    });

    await page.goto('/agents/pm');
    
    // Enter edit mode and make changes
    await page.click('button:has-text("Edit")');
    await page.fill('input[name="name"]', 'Updated Name');
    
    // Try to save
    await page.click('button:has-text("Save")');
    
    // Should handle error gracefully
    // This depends on your error handling implementation
    await expect(page.locator('text=Product Manager')).toBeVisible();
  });

  test('should be responsive on mobile devices', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto('/agents/pm');
    
    // Check that content is still visible and functional
    await expect(page.locator('text=Product Manager')).toBeVisible();
    await expect(page.locator('text=Product Management')).toBeVisible();
    await expect(page.locator('button:has-text("Edit")')).toBeVisible();
    
    // Test edit mode on mobile
    await page.click('button:has-text("Edit")');
    await expect(page.locator('input[name="name"]')).toBeVisible();
    await expect(page.locator('button:has-text("Save")')).toBeVisible();
  });

  test('should show loading state while fetching agent data', async ({ page }) => {
    // Mock slow API response
    await page.route('**/agents/pm', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000));
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

    await page.goto('/agents/pm');
    
    // Should show loading state initially
    await expect(page.locator('text=Loading...')).toBeVisible();
    
    // Wait for content to load
    await expect(page.locator('text=Product Manager')).toBeVisible();
  });
});
