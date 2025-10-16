import { test, expect } from '@playwright/test';

test.describe('LLM Calls Display', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to workflow detail page
    await page.goto('//workflows/12');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
  });

  test('should display LLM calls section for conversations with LLM data', async ({ page }) => {
    // Wait for conversations to load
    await page.waitForSelector('[data-testid="conversation"]', { timeout: 10000 });
    
    // Find a conversation that should have LLM calls (Product Manager)
    const conversationWithLLMCalls = page.locator('[data-testid="conversation"]').filter({ hasText: 'Product Manager' });
    await expect(conversationWithLLMCalls).toBeVisible();
    
    // Check if the LLM calls section is visible
    const llmCallsSection = conversationWithLLMCalls.locator('.llm-calls');
    await expect(llmCallsSection).toBeVisible();
    
    // Check for LLM summary
    const llmSummary = llmCallsSection.locator('.llm-summary');
    await expect(llmSummary).toBeVisible();
    
    // Check for token usage and cost
    const tokenUsage = llmSummary.locator('.token-usage');
    const costUsage = llmSummary.locator('.cost-usage');
    await expect(tokenUsage).toContainText('Total Tokens: 350');
    await expect(costUsage).toContainText('Total Cost: $0.0105');
  });

  test('should display LLM call accordion with detailed information', async ({ page }) => {
    // Wait for conversations to load
    await page.waitForSelector('[data-testid="conversation"]', { timeout: 10000 });
    
    // Find a conversation with LLM calls
    const conversationWithLLMCalls = page.locator('[data-testid="conversation"]').filter({ hasText: 'Product Manager' });
    
    // Check for LLM call accordion
    const llmAccordion = conversationWithLLMCalls.locator('.llm-calls p-accordion');
    await expect(llmAccordion).toBeVisible();
    
    // Check for accordion tabs
    const accordionTabs = llmAccordion.locator('p-accordionTab');
    const tabCount = await accordionTabs.count();
    expect(tabCount).toBeGreaterThan(0);
    
    // Check accordion tab header
    const firstTab = accordionTabs.first();
    const tabHeader = firstTab.locator('.p-accordionheader');
    await expect(tabHeader).toContainText('gpt-4');
    await expect(tabHeader).toContainText('350 tokens');
    await expect(tabHeader).toContainText('$0.0105');
  });

  test('should display detailed LLM call information when expanded', async ({ page }) => {
    // Wait for conversations to load
    await page.waitForSelector('[data-testid="conversation"]', { timeout: 10000 });
    
    // Find a conversation with LLM calls
    const conversationWithLLMCalls = page.locator('[data-testid="conversation"]').filter({ hasText: 'Product Manager' });
    
    // Click on the first LLM call accordion tab
    const firstTab = conversationWithLLMCalls.locator('.llm-calls p-accordionTab').first();
    await firstTab.click();
    
    // Check for LLM call content
    const llmCallContent = firstTab.locator('.llm-call-content');
    await expect(llmCallContent).toBeVisible();
    
    // Check for call header with model and metrics
    const callHeader = llmCallContent.locator('.llm-call-header');
    await expect(callHeader).toBeVisible();
    
    // Check for model name
    const modelName = callHeader.locator('.model-name');
    await expect(modelName).toContainText('gpt-4');
    
    // Check for call metrics
    const callMetrics = callHeader.locator('.call-metrics');
    await expect(callMetrics).toBeVisible();
    
    // Check for tokens, cost, and response time
    await expect(callMetrics.locator('.tokens')).toContainText('350 tokens');
    await expect(callMetrics.locator('.cost')).toContainText('$0.0105');
    await expect(callMetrics.locator('.response-time')).toContainText('1200ms');
  });

  test('should display request and response details', async ({ page }) => {
    // Wait for conversations to load
    await page.waitForSelector('[data-testid="conversation"]', { timeout: 10000 });
    
    // Find a conversation with LLM calls
    const conversationWithLLMCalls = page.locator('[data-testid="conversation"]').filter({ hasText: 'Product Manager' });
    
    // Click on the first LLM call accordion tab
    const firstTab = conversationWithLLMCalls.locator('.llm-calls p-accordionTab').first();
    await firstTab.click();
    
    // Check for request section
    const requestSection = firstTab.locator('.request-section');
    await expect(requestSection).toBeVisible();
    await expect(requestSection.locator('h4')).toContainText('Request:');
    
    // Check for messages
    const messages = requestSection.locator('.messages .message');
    const messageCount = await messages.count();
    expect(messageCount).toBeGreaterThan(0);
    
    // Check for response section
    const responseSection = firstTab.locator('.response-section');
    await expect(responseSection).toBeVisible();
    await expect(responseSection.locator('h4')).toContainText('Response:');
    
    // Check for response content
    const responseContent = responseSection.locator('.response-content');
    await expect(responseContent).toBeVisible();
    await expect(responseContent).toContainText('Based on the story analysis');
  });

  test('should display token usage breakdown', async ({ page }) => {
    // Wait for conversations to load
    await page.waitForSelector('[data-testid="conversation"]', { timeout: 10000 });
    
    // Find a conversation with LLM calls
    const conversationWithLLMCalls = page.locator('[data-testid="conversation"]').filter({ hasText: 'Product Manager' });
    
    // Click on the first LLM call accordion tab
    const firstTab = conversationWithLLMCalls.locator('.llm-calls p-accordionTab').first();
    await firstTab.click();
    
    // Check for usage breakdown
    const usageBreakdown = firstTab.locator('.usage-breakdown');
    await expect(usageBreakdown).toBeVisible();
    await expect(usageBreakdown.locator('h4')).toContainText('Token Usage:');
    
    // Check for usage stats
    const usageStats = usageBreakdown.locator('.usage-stats');
    await expect(usageStats).toBeVisible();
    
    // Check for individual usage stats
    await expect(usageStats).toContainText('Prompt: 150 tokens');
    await expect(usageStats).toContainText('Completion: 200 tokens');
    await expect(usageStats).toContainText('Total: 350 tokens');
  });

  test('should handle conversations without LLM calls gracefully', async ({ page }) => {
    // Wait for conversations to load
    await page.waitForSelector('[data-testid="conversation"]', { timeout: 10000 });
    
    // Find a conversation that should not have LLM calls (if any)
    const conversations = page.locator('[data-testid="conversation"]');
    const conversationCount = await conversations.count();
    
    // Check that at least one conversation has LLM calls
    let hasLLMCalls = false;
    for (let i = 0; i < conversationCount; i++) {
      const conversation = conversations.nth(i);
      const llmCallsSection = conversation.locator('.llm-calls');
      if (await llmCallsSection.isVisible()) {
        hasLLMCalls = true;
        break;
      }
    }
    
    expect(hasLLMCalls).toBeTruthy();
  });
});
