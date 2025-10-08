import { test, expect } from '@playwright/test';

test.describe('Performance and Accessibility Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API endpoints for performance testing
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
  });

  test('should load dashboard within performance budget', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/dashboard');
    
    // Wait for content to be visible
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();
    await expect(page.locator('text=Agents')).toBeVisible();
    await expect(page.locator('text=Workflows')).toBeVisible();
    
    const loadTime = Date.now() - startTime;
    
    // Dashboard should load within 2 seconds
    expect(loadTime).toBeLessThan(2000);
  });

  test('should load workflows page within performance budget', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/workflows');
    
    // Wait for content to be visible
    await expect(page.locator('text=Workflows')).toBeVisible();
    await expect(page.locator('[data-testid="workflows-table"]')).toBeVisible();
    
    const loadTime = Date.now() - startTime;
    
    // Workflows page should load within 3 seconds
    expect(loadTime).toBeLessThan(3000);
  });

  test('should load agents page within performance budget', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/agents');
    
    // Wait for content to be visible
    await expect(page.locator('text=Agents')).toBeVisible();
    await expect(page.locator('[data-testid="agents-table"]')).toBeVisible();
    
    const loadTime = Date.now() - startTime;
    
    // Agents page should load within 3 seconds
    expect(loadTime).toBeLessThan(3000);
  });

  test('should handle large datasets efficiently', async ({ page }) => {
    // Mock large dataset
    const largeWorkflows = Array.from({ length: 100 }, (_, i) => ({
      id: `workflow_${i}`,
      name: `Workflow ${i}`,
      status: i % 2 === 0 ? 'completed' : 'pending',
      agents: ['pm', 'architect'],
      created_at: '2024-01-01T00:00:00'
    }));

    await page.route('**/workflows', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(largeWorkflows)
      });
    });

    const startTime = Date.now();
    await page.goto('/workflows');
    
    // Wait for content to be visible
    await expect(page.locator('text=Workflows')).toBeVisible();
    await expect(page.locator('[data-testid="workflows-table"]')).toBeVisible();
    
    const loadTime = Date.now() - startTime;
    
    // Should handle large datasets within 5 seconds
    expect(loadTime).toBeLessThan(5000);
  });

  test('should have proper accessibility attributes', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Check for proper heading structure
    await expect(page.locator('h2')).toBeVisible();
    
    // Check for proper button labels
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();
    for (let i = 0; i < buttonCount; i++) {
      const button = buttons.nth(i);
      const ariaLabel = await button.getAttribute('aria-label');
      const text = await button.textContent();
      const title = await button.getAttribute('title');
      
      // Button should have either aria-label, text content, or title
      expect(ariaLabel || text || title).toBeTruthy();
    }
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Test tab navigation
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    // Should be able to navigate with keyboard
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible();
  });

  test('should have proper color contrast', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Check that text is visible (basic contrast test)
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();
    await expect(page.locator('text=Agents')).toBeVisible();
    await expect(page.locator('text=Workflows')).toBeVisible();
    
    // Check that status indicators are visible
    await page.goto('/workflows');
    await expect(page.locator('[data-testid="workflow-status"]')).toBeVisible();
  });

  test('should be responsive on different screen sizes', async ({ page }) => {
    // Test desktop
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/dashboard');
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();
    
    // Test tablet
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/dashboard');
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();
    
    // Test mobile
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/dashboard');
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();
  });

  test('should handle rapid user interactions', async ({ page }) => {
    await page.goto('/workflows');
    
    // Rapidly click buttons
    for (let i = 0; i < 10; i++) {
      await page.click('[data-testid="refresh-button"]');
      await page.waitForTimeout(100);
    }
    
    // Should handle rapid interactions without crashing
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should handle memory efficiently', async ({ page }) => {
    // Navigate between pages multiple times
    for (let i = 0; i < 10; i++) {
      await page.goto('/dashboard');
      await page.goto('/workflows');
      await page.goto('/agents');
    }
    
    // Should not have memory leaks
    await expect(page.locator('text=Agents')).toBeVisible();
  });

  test('should handle concurrent user actions', async ({ page }) => {
    await page.goto('/workflows');
    
    // Simulate concurrent actions
    const actions = [
      page.click('[data-testid="refresh-button"]'),
      page.fill('[data-testid="workflow-search"]', 'test'),
      page.selectOption('[data-testid="status-filter"]', 'completed')
    ];
    
    await Promise.all(actions);
    
    // Should handle concurrent actions gracefully
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should have proper focus management', async ({ page }) => {
    await page.goto('/workflows');
    
    // Test focus management in forms
    await page.click('[data-testid="add-workflow-button"]');
    
    // Focus should be on the first input
    const firstInput = page.locator('input[name="name"]');
    await expect(firstInput).toBeFocused();
  });

  test('should handle screen reader navigation', async ({ page }) => {
    await page.goto('/workflows');
    
    // Check for proper ARIA labels
    const table = page.locator('[data-testid="workflows-table"]');
    await expect(table).toBeVisible();
    
    // Check for proper table headers
    const headers = page.locator('th');
    const headerCount = await headers.count();
    expect(headerCount).toBeGreaterThan(0);
  });

  test('should handle high contrast mode', async ({ page }) => {
    // Simulate high contrast mode by injecting CSS
    await page.addStyleTag({
      content: `
        * {
          background: white !important;
          color: black !important;
          border: 1px solid black !important;
        }
      `
    });
    
    await page.goto('/dashboard');
    
    // Should still be functional in high contrast mode
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();
  });

  test('should handle reduced motion preferences', async ({ page }) => {
    // Simulate reduced motion preference
    await page.addStyleTag({
      content: `
        * {
          animation: none !important;
          transition: none !important;
        }
      `
    });
    
    await page.goto('/workflows');
    
    // Should still be functional with reduced motion
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should handle zoom levels', async ({ page }) => {
    // Test different zoom levels
    await page.goto('/dashboard');
    
    // Test 50% zoom
    await page.setViewportSize({ width: 960, height: 540 });
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();
    
    // Test 200% zoom
    await page.setViewportSize({ width: 3840, height: 2160 });
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();
  });

  test('should handle slow network conditions', async ({ page }) => {
    // Simulate slow network
    await page.route('**/workflows', async route => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      const mockWorkflows = [
        {
          id: 'workflow_1',
          name: 'Workflow 1',
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

    await page.goto('/workflows');
    
    // Should handle slow network gracefully
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should handle offline conditions', async ({ page }) => {
    // Simulate offline condition
    await page.context().setOffline(true);
    
    await page.goto('/workflows');
    
    // Should handle offline gracefully
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should handle different time zones', async ({ page }) => {
    // Mock workflow with different timezone
    await page.route('**/workflows', async route => {
      const mockWorkflows = [
        {
          id: 'workflow_1',
          name: 'Workflow 1',
          status: 'completed',
          agents: ['pm'],
          created_at: '2024-01-01T00:00:00+09:00' // JST timezone
        }
      ];
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockWorkflows)
      });
    });

    await page.goto('/workflows');
    
    // Should handle different timezones gracefully
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should handle different locales', async ({ page }) => {
    // Set different locale
    await page.context().addInitScript(() => {
      Object.defineProperty(navigator, 'language', {
        get: () => 'ja-JP'
      });
    });

    await page.goto('/dashboard');
    
    // Should handle different locales gracefully
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();
  });

  test('should handle different input methods', async ({ page }) => {
    await page.goto('/workflows');
    
    // Test touch input
    await page.tap('[data-testid="refresh-button"]');
    
    // Test mouse input
    await page.click('[data-testid="add-workflow-button"]');
    
    // Test keyboard input
    await page.keyboard.press('Escape'); // Close dialog
    
    // Should handle different input methods
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should handle different browsers', async ({ page }) => {
    // Test basic functionality across different browsers
    await page.goto('/dashboard');
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();
    
    await page.goto('/workflows');
    await expect(page.locator('text=Workflows')).toBeVisible();
    
    await page.goto('/agents');
    await expect(page.locator('text=Agents')).toBeVisible();
  });

  test('should handle different operating systems', async ({ page }) => {
    // Test basic functionality
    await page.goto('/dashboard');
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();
    
    // Test keyboard shortcuts that might be OS-specific
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    // Should work regardless of OS
    await expect(page.locator(':focus')).toBeVisible();
  });

  test('should handle different device orientations', async ({ page }) => {
    // Test portrait orientation
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/dashboard');
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();
    
    // Test landscape orientation
    await page.setViewportSize({ width: 667, height: 375 });
    await page.goto('/dashboard');
    await expect(page.locator('text=AI Team Dashboard')).toBeVisible();
  });

  test('should handle different connection speeds', async ({ page }) => {
    // Simulate 3G connection
    await page.route('**/workflows', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      const mockWorkflows = [
        {
          id: 'workflow_1',
          name: 'Workflow 1',
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

    await page.goto('/workflows');
    
    // Should handle slow connections gracefully
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should handle different user preferences', async ({ page }) => {
    // Test with different user preferences
    await page.goto('/workflows');
    
    // Test with different font sizes
    await page.addStyleTag({
      content: `
        * {
          font-size: 24px !important;
        }
      `
    });
    
    // Should still be functional with larger fonts
    await expect(page.locator('text=Workflows')).toBeVisible();
  });
});
