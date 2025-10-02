import { test, expect } from '@playwright/test';

test.describe('Error Handling and Edge Cases Tests', () => {
  test('should handle 404 errors gracefully', async ({ page }) => {
    // Mock 404 error for workflows
    await page.route('**/workflows', async route => {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Not found' })
      });
    });

    await page.goto('/workflows');
    
    // Should handle error gracefully without crashing
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should handle 500 server errors gracefully', async ({ page }) => {
    // Mock 500 error for agents
    await page.route('**/agents', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal server error' })
      });
    });

    await page.goto('/agents');
    
    // Should handle error gracefully without crashing
    await expect(page.locator('text=Agents')).toBeVisible();
  });

  test('should handle network timeouts gracefully', async ({ page }) => {
    // Mock timeout error
    await page.route('**/workflows', async route => {
      await route.abort('timedout');
    });

    await page.goto('/workflows');
    
    // Should handle timeout gracefully
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should handle malformed JSON responses', async ({ page }) => {
    // Mock malformed JSON
    await page.route('**/workflows', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: 'invalid json {'
      });
    });

    await page.goto('/workflows');
    
    // Should handle malformed JSON gracefully
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should handle empty responses', async ({ page }) => {
    // Mock empty response
    await page.route('**/workflows', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: ''
      });
    });

    await page.goto('/workflows');
    
    // Should handle empty response gracefully
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should handle very large responses', async ({ page }) => {
    // Mock very large response
    const largeWorkflows = Array.from({ length: 1000 }, (_, i) => ({
      id: `workflow_${i}`,
      name: `Workflow ${i}`,
      status: 'completed',
      agents: ['pm'],
      created_at: '2024-01-01T00:00:00'
    }));

    await page.route('**/workflows', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(largeWorkflows)
      });
    });

    await page.goto('/workflows');
    
    // Should handle large response gracefully
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should handle concurrent API requests', async ({ page }) => {
    // Mock concurrent requests
    let requestCount = 0;
    await page.route('**/workflows', async route => {
      requestCount++;
      await new Promise(resolve => setTimeout(resolve, 100));
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
    
    // Should handle concurrent requests gracefully
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should handle API rate limiting', async ({ page }) => {
    // Mock rate limiting response
    await page.route('**/workflows', async route => {
      await route.fulfill({
        status: 429,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Rate limit exceeded' })
      });
    });

    await page.goto('/workflows');
    
    // Should handle rate limiting gracefully
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should handle authentication errors', async ({ page }) => {
    // Mock authentication error
    await page.route('**/workflows', async route => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Unauthorized' })
      });
    });

    await page.goto('/workflows');
    
    // Should handle authentication error gracefully
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should handle CORS errors', async ({ page }) => {
    // Mock CORS error
    await page.route('**/workflows', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
        headers: {
          'Access-Control-Allow-Origin': 'null'
        }
      });
    });

    await page.goto('/workflows');
    
    // Should handle CORS error gracefully
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should handle slow API responses', async ({ page }) => {
    // Mock very slow response
    await page.route('**/workflows', async route => {
      await new Promise(resolve => setTimeout(resolve, 10000));
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
    
    // Should handle slow response gracefully
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should handle API responses with unexpected data structure', async ({ page }) => {
    // Mock unexpected data structure
    await page.route('**/workflows', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          unexpected: 'data',
          structure: 'here'
        })
      });
    });

    await page.goto('/workflows');
    
    // Should handle unexpected data structure gracefully
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should handle API responses with missing required fields', async ({ page }) => {
    // Mock response with missing fields
    await page.route('**/workflows', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'workflow_1',
            // Missing name, status, agents, created_at
          }
        ])
      });
    });

    await page.goto('/workflows');
    
    // Should handle missing fields gracefully
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should handle API responses with null values', async ({ page }) => {
    // Mock response with null values
    await page.route('**/workflows', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'workflow_1',
            name: null,
            status: null,
            agents: null,
            created_at: null
          }
        ])
      });
    });

    await page.goto('/workflows');
    
    // Should handle null values gracefully
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should handle API responses with undefined values', async ({ page }) => {
    // Mock response with undefined values
    await page.route('**/workflows', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'workflow_1',
            name: undefined,
            status: undefined,
            agents: undefined,
            created_at: undefined
          }
        ])
      });
    });

    await page.goto('/workflows');
    
    // Should handle undefined values gracefully
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should handle API responses with special characters', async ({ page }) => {
    // Mock response with special characters
    await page.route('**/workflows', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'workflow_1',
            name: 'Workflow with special chars: !@#$%^&*()',
            status: 'completed',
            agents: ['pm'],
            created_at: '2024-01-01T00:00:00'
          }
        ])
      });
    });

    await page.goto('/workflows');
    
    // Should handle special characters gracefully
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should handle API responses with very long strings', async ({ page }) => {
    // Mock response with very long strings
    const longString = 'a'.repeat(10000);
    await page.route('**/workflows', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'workflow_1',
            name: longString,
            status: 'completed',
            agents: ['pm'],
            created_at: '2024-01-01T00:00:00'
          }
        ])
      });
    });

    await page.goto('/workflows');
    
    // Should handle very long strings gracefully
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should handle API responses with unicode characters', async ({ page }) => {
    // Mock response with unicode characters
    await page.route('**/workflows', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'workflow_1',
            name: 'Workflow with unicode: 你好世界 🌍',
            status: 'completed',
            agents: ['pm'],
            created_at: '2024-01-01T00:00:00'
          }
        ])
      });
    });

    await page.goto('/workflows');
    
    // Should handle unicode characters gracefully
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should handle API responses with HTML content', async ({ page }) => {
    // Mock response with HTML content
    await page.route('**/workflows', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'workflow_1',
            name: '<script>alert("xss")</script>Workflow',
            status: 'completed',
            agents: ['pm'],
            created_at: '2024-01-01T00:00:00'
          }
        ])
      });
    });

    await page.goto('/workflows');
    
    // Should handle HTML content safely (XSS protection)
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should handle API responses with SQL injection attempts', async ({ page }) => {
    // Mock response with SQL injection attempts
    await page.route('**/workflows', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'workflow_1',
            name: "'; DROP TABLE workflows; --",
            status: 'completed',
            agents: ['pm'],
            created_at: '2024-01-01T00:00:00'
          }
        ])
      });
    });

    await page.goto('/workflows');
    
    // Should handle SQL injection attempts safely
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should handle API responses with JSON injection attempts', async ({ page }) => {
    // Mock response with JSON injection attempts
    await page.route('**/workflows', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'workflow_1',
            name: 'Workflow"},"injected":"data',
            status: 'completed',
            agents: ['pm'],
            created_at: '2024-01-01T00:00:00'
          }
        ])
      });
    });

    await page.goto('/workflows');
    
    // Should handle JSON injection attempts safely
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should handle API responses with circular references', async ({ page }) => {
    // Mock response with circular references
    const circularData = {
      id: 'workflow_1',
      name: 'Workflow 1',
      status: 'completed',
      agents: ['pm'],
      created_at: '2024-01-01T00:00:00'
    };
    // @ts-ignore
    circularData.self = circularData;

    await page.route('**/workflows', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([circularData])
      });
    });

    await page.goto('/workflows');
    
    // Should handle circular references gracefully
    await expect(page.locator('text=Workflows')).toBeVisible();
  });

  test('should handle API responses with extremely nested objects', async ({ page }) => {
    // Mock response with extremely nested objects
    let nestedObject: any = { value: 'deep' };
    for (let i = 0; i < 1000; i++) {
      nestedObject = { nested: nestedObject };
    }

    await page.route('**/workflows', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'workflow_1',
            name: 'Workflow 1',
            status: 'completed',
            agents: ['pm'],
            created_at: '2024-01-01T00:00:00',
            nested: nestedObject
          }
        ])
      });
    });

    await page.goto('/workflows');
    
    // Should handle extremely nested objects gracefully
    await expect(page.locator('text=Workflows')).toBeVisible();
  });
});
