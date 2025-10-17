import { test, expect } from '@playwright/test';

test.describe('Conversation Reviewer Feature', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to a workflow detail page
    await page.goto('/workflows/1');
    await page.waitForLoadState('networkidle');
  });

  test('should display conversation review tab', async ({ page }) => {
    // Check that the conversation review tab is visible
    await expect(page.locator('[data-testid="tab-conversation-review"]')).toBeVisible();
    
    // Click on the conversation review tab
    await page.click('[data-testid="tab-conversation-review"]');
    
    // Verify the tab content is displayed
    await expect(page.locator('.conversation-review-section')).toBeVisible();
    await expect(page.locator('h3:has-text("AI-Powered Workflow Optimization")')).toBeVisible();
  });

  test('should show generate review button and initial state', async ({ page }) => {
    await page.click('[data-testid="tab-conversation-review"]');
    
    // Check that the generate review button is visible
    await expect(page.locator('[data-testid="generate-review-button"]')).toBeVisible();
    await expect(page.locator('[data-testid="refresh-review-button"]')).toBeVisible();
    
    // Check initial state - no review available
    await expect(page.locator('.no-review')).toBeVisible();
    await expect(page.locator('p:has-text("No conversation review available yet")')).toBeVisible();
  });

  test('should handle generate review button click', async ({ page }) => {
    await page.click('[data-testid="tab-conversation-review"]');
    
    // Mock the API response for conversation review
    await page.route('**/workflows/1/conversation-review', async route => {
      const mockResponse = {
        summary: "This workflow shows good agent collaboration with room for optimization.",
        workflow_recommendations: [
          {
            title: "Streamline Agent Communication",
            description: "Reduce redundant messages between agents by implementing a shared context system."
          }
        ],
        prompt_recommendations: [
          {
            agent: "Product Manager",
            current_issue: "Prompts are too verbose",
            suggestion: "Use more concise, action-oriented prompts"
          }
        ],
        code_change_suggestions: [
          {
            path: "crewai_app/agents/pm.py",
            section: "review_story method",
            change_type: "edit",
            before_summary: "Long prompt with unnecessary details",
            after_summary: "Concise prompt focused on key requirements",
            patch_outline: "Replace verbose prompt with streamlined version"
          }
        ],
        risk_flags: ["High token usage detected"],
        quick_wins: ["Reduce prompt length by 30%"],
        estimated_savings: {
          messages: 15,
          cost_usd: 2.50,
          duration_minutes: 8
        }
      };
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockResponse)
      });
    });
    
    // Click generate review button
    await page.click('[data-testid="generate-review-button"]');
    
    // Wait for the review to be generated
    await expect(page.locator('[data-testid="conversation-review-results"]')).toBeVisible();
    
    // Verify the review content is displayed
    await expect(page.locator('h4:has-text("Summary")')).toBeVisible();
    await expect(page.locator('h4:has-text("Estimated Savings")')).toBeVisible();
    await expect(page.locator('h4:has-text("Workflow Recommendations")')).toBeVisible();
    await expect(page.locator('h4:has-text("Prompt Engineering Recommendations")')).toBeVisible();
    await expect(page.locator('h4:has-text("Code Change Suggestions")')).toBeVisible();
    await expect(page.locator('h4:has-text("Risk Flags")')).toBeVisible();
    await expect(page.locator('h4:has-text("Quick Wins")')).toBeVisible();
  });

  test('should display review results correctly', async ({ page }) => {
    await page.click('[data-testid="tab-conversation-review"]');
    
    // Mock the API response
    await page.route('**/workflows/1/conversation-review', async route => {
      const mockResponse = {
        summary: "Workflow analysis complete with optimization opportunities identified.",
        workflow_recommendations: [
          {
            title: "Optimize Agent Flow",
            description: "Implement parallel processing for independent tasks."
          }
        ],
        prompt_recommendations: [
          {
            agent: "Backend Developer",
            current_issue: "Unclear requirements",
            suggestion: "Add specific acceptance criteria to prompts"
          }
        ],
        code_change_suggestions: [
          {
            path: "crewai_app/workflows/story_implementation_workflow.py",
            section: "execute method",
            change_type: "add",
            before_summary: "Sequential execution only",
            after_summary: "Parallel execution for independent steps",
            patch_outline: "Add parallel execution logic using asyncio"
          }
        ],
        risk_flags: ["Memory usage high", "Long execution time"],
        quick_wins: ["Cache LLM responses", "Optimize database queries"],
        estimated_savings: {
          messages: 25,
          cost_usd: 4.20,
          duration_minutes: 12
        }
      };
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockResponse)
      });
    });
    
    // Generate review
    await page.click('[data-testid="generate-review-button"]');
    await expect(page.locator('[data-testid="conversation-review-results"]')).toBeVisible();
    
    // Verify summary content
    await expect(page.locator('.summary-content p')).toContainText('Workflow analysis complete');
    
    // Verify estimated savings
    await expect(page.locator('.savings-item').nth(0)).toContainText('Messages: 25');
    await expect(page.locator('.savings-item').nth(1)).toContainText('Cost: $4.20');
    await expect(page.locator('.savings-item').nth(2)).toContainText('Duration: 12 min');
    
    // Verify workflow recommendations
    await expect(page.locator('.recommendation-item h5')).toContainText('Optimize Agent Flow');
    await expect(page.locator('.recommendation-item p')).toContainText('Implement parallel processing');
    
    // Verify prompt recommendations
    await expect(page.locator('.agent-badge')).toContainText('Backend Developer');
    await expect(page.locator('.recommendation-item h5')).toContainText('Issue: Unclear requirements');
    
    // Verify code change suggestions
    await expect(page.locator('p-accordionTab')).toContainText('crewai_app/workflows/story_implementation_workflow.py');
    
    // Verify risk flags
    await expect(page.locator('.p-chip-warning').nth(0)).toContainText('Memory usage high');
    await expect(page.locator('.p-chip-warning').nth(1)).toContainText('Long execution time');
    
    // Verify quick wins
    await expect(page.locator('.p-chip-success').nth(0)).toContainText('Cache LLM responses');
    await expect(page.locator('.p-chip-success').nth(1)).toContainText('Optimize database queries');
  });

  test('should handle API errors gracefully', async ({ page }) => {
    await page.click('[data-testid="tab-conversation-review"]');
    
    // Mock API error response
    await page.route('**/workflows/1/conversation-review', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Failed to generate conversation review: Service unavailable'
        })
      });
    });
    
    // Click generate review button
    await page.click('[data-testid="generate-review-button"]');
    
    // Verify error is displayed
    await expect(page.locator('.review-error')).toBeVisible();
    await expect(page.locator('.error-message')).toContainText('Failed to generate conversation review');
  });

  test('should handle refresh review functionality', async ({ page }) => {
    await page.click('[data-testid="tab-conversation-review"]');
    
    // Mock the GET endpoint for refresh
    await page.route('**/workflows/1/conversation-review', async route => {
      if (route.request().method() === 'GET') {
        const mockResponse = {
          summary: "Updated review with latest analysis.",
          workflow_recommendations: [],
          prompt_recommendations: [],
          code_change_suggestions: [],
          risk_flags: [],
          quick_wins: [],
          estimated_savings: {
            messages: 0,
            cost_usd: 0,
            duration_minutes: 0
          }
        };
        
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockResponse)
        });
      }
    });
    
    // Click refresh review button
    await page.click('[data-testid="refresh-review-button"]');
    
    // Verify refresh worked
    await expect(page.locator('[data-testid="conversation-review-results"]')).toBeVisible();
    await expect(page.locator('.summary-content p')).toContainText('Updated review with latest analysis');
  });

  test('should expand code change suggestions accordion', async ({ page }) => {
    await page.click('[data-testid="tab-conversation-review"]');
    
    // Mock API response with code suggestions
    await page.route('**/workflows/1/conversation-review', async route => {
      const mockResponse = {
        summary: "Code optimization suggestions available.",
        workflow_recommendations: [],
        prompt_recommendations: [],
        code_change_suggestions: [
          {
            path: "crewai_app/agents/developer.py",
            section: "implement_feature method",
            change_type: "edit",
            before_summary: "Basic implementation",
            after_summary: "Optimized with error handling",
            patch_outline: "Add try-catch blocks and input validation"
          }
        ],
        risk_flags: [],
        quick_wins: [],
        estimated_savings: {
          messages: 0,
          cost_usd: 0,
          duration_minutes: 0
        }
      };
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockResponse)
      });
    });
    
    // Generate review
    await page.click('[data-testid="generate-review-button"]');
    await expect(page.locator('[data-testid="conversation-review-results"]')).toBeVisible();
    
    // Click on the code suggestion accordion
    await page.click('p-accordionTab:has-text("crewai_app/agents/developer.py")');
    
    // Verify the code suggestion content is displayed
    await expect(page.locator('.code-suggestion')).toBeVisible();
    await expect(page.locator('.file-path')).toContainText('crewai_app/agents/developer.py');
    await expect(page.locator('.change-type')).toContainText('edit');
    await expect(page.locator('.before h5')).toContainText('Before:');
    await expect(page.locator('.after h5')).toContainText('After:');
    await expect(page.locator('.patch-outline h5')).toContainText('Implementation:');
  });

  test('should show loading states during API calls', async ({ page }) => {
    await page.click('[data-testid="tab-conversation-review"]');
    
    // Mock slow API response
    await page.route('**/workflows/1/conversation-review', async route => {
      // Add delay to simulate slow response
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const mockResponse = {
        summary: "Review completed after delay.",
        workflow_recommendations: [],
        prompt_recommendations: [],
        code_change_suggestions: [],
        risk_flags: [],
        quick_wins: [],
        estimated_savings: {
          messages: 0,
          cost_usd: 0,
          duration_minutes: 0
        }
      };
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockResponse)
      });
    });
    
    // Click generate review button
    await page.click('[data-testid="generate-review-button"]');
    
    // Verify loading state is shown
    await expect(page.locator('[data-testid="generate-review-button"][loading="true"]')).toBeVisible();
    
    // Wait for completion
    await expect(page.locator('[data-testid="conversation-review-results"]')).toBeVisible();
    
    // Verify loading state is removed
    await expect(page.locator('[data-testid="generate-review-button"][loading="true"]')).not.toBeVisible();
  });

  test('should handle empty review results', async ({ page }) => {
    await page.click('[data-testid="tab-conversation-review"]');
    
    // Mock empty review response
    await page.route('**/workflows/1/conversation-review', async route => {
      const mockResponse = {
        summary: "No significant optimization opportunities found.",
        workflow_recommendations: [],
        prompt_recommendations: [],
        code_change_suggestions: [],
        risk_flags: [],
        quick_wins: [],
        estimated_savings: {
          messages: 0,
          cost_usd: 0,
          duration_minutes: 0
        }
      };
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockResponse)
      });
    });
    
    // Generate review
    await page.click('[data-testid="generate-review-button"]');
    await expect(page.locator('[data-testid="conversation-review-results"]')).toBeVisible();
    
    // Verify only summary is shown (other sections should be hidden)
    await expect(page.locator('h4:has-text("Summary")')).toBeVisible();
    await expect(page.locator('h4:has-text("Workflow Recommendations")')).not.toBeVisible();
    await expect(page.locator('h4:has-text("Prompt Engineering Recommendations")')).not.toBeVisible();
    await expect(page.locator('h4:has-text("Code Change Suggestions")')).not.toBeVisible();
    await expect(page.locator('h4:has-text("Risk Flags")')).not.toBeVisible();
    await expect(page.locator('h4:has-text("Quick Wins")')).not.toBeVisible();
  });
});
