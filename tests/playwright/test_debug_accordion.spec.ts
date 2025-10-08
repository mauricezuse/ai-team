import { test, expect } from '@playwright/test';

test.describe('Debug Code Files Accordion', () => {
  test('debug workflow page structure', async ({ page }) => {
    // Navigate to workflow detail page
    await page.goto('/workflows/12');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
    
    // Take a screenshot for debugging
    await page.screenshot({ path: 'debug-workflow-page.png', fullPage: true });
    
    // Check if conversations are loaded
    const conversations = page.locator('[data-testid="conversation"]');
    const conversationCount = await conversations.count();
    console.log(`Found ${conversationCount} conversations`);
    
    // Check each conversation
    for (let i = 0; i < conversationCount; i++) {
      const conversation = conversations.nth(i);
      const step = await conversation.locator('.step-badge').textContent();
      console.log(`Conversation ${i}: ${step}`);
      
      // Check if this conversation has code files
      const codeFilesSection = conversation.locator('.code-files');
      const hasCodeFiles = await codeFilesSection.isVisible();
      console.log(`  Has code files: ${hasCodeFiles}`);
      
      if (hasCodeFiles) {
        const accordion = codeFilesSection.locator('p-accordion');
        const accordionVisible = await accordion.isVisible();
        console.log(`  Accordion visible: ${accordionVisible}`);
        
        const accordionTabs = accordion.locator('p-accordionTab');
        const tabCount = await accordionTabs.count();
        console.log(`  Accordion tabs: ${tabCount}`);
      }
    }
    
    // Check if any conversation has the step we're looking for
    const targetConversation = page.locator('[data-testid="conversation"]').filter({ hasText: 'implementation_plan_generated' });
    const targetCount = await targetConversation.count();
    console.log(`Found ${targetCount} conversations with implementation_plan_generated step`);
    
    if (targetCount > 0) {
      const codeFilesSection = targetConversation.locator('.code-files');
      const codeFilesVisible = await codeFilesSection.isVisible();
      console.log(`Code files section visible: ${codeFilesVisible}`);
      
      if (codeFilesVisible) {
        const accordion = codeFilesSection.locator('p-accordion');
        const accordionVisible = await accordion.isVisible();
        console.log(`Accordion visible: ${accordionVisible}`);
        
        const accordionTabs = accordion.locator('p-accordionTab');
        const tabCount = await accordionTabs.count();
        console.log(`Accordion tabs count: ${tabCount}`);
      }
    }
  });
});
