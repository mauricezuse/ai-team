import { test, expect } from '@playwright/test';

test.describe('Simple Accordion Test', () => {
  test('verify accordion is working', async ({ page }) => {
    // Navigate to workflow detail page
    await page.goto('http://localhost:4002/workflows/12');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
    
    // Take a screenshot for debugging
    await page.screenshot({ path: 'simple-accordion-test.png', fullPage: true });
    
    // Check if conversations are loaded
    const conversations = page.locator('[data-testid="conversation"]');
    const conversationCount = await conversations.count();
    console.log(`Found ${conversationCount} conversations`);
    
    // Find conversation with code files
    const conversationWithCodeFiles = page.locator('[data-testid="conversation"]').filter({ hasText: 'implementation_plan_generated' });
    await expect(conversationWithCodeFiles).toBeVisible();
    
    // Check if code files section is visible
    const codeFilesSection = conversationWithCodeFiles.locator('.code-files');
    const codeFilesVisible = await codeFilesSection.isVisible();
    console.log(`Code files section visible: ${codeFilesVisible}`);
    
    if (codeFilesVisible) {
      // Check for accordion
      const accordion = codeFilesSection.locator('p-accordion');
      const accordionVisible = await accordion.isVisible();
      console.log(`Accordion visible: ${accordionVisible}`);
      
      if (accordionVisible) {
        // Check for accordion tabs
        const accordionTabs = accordion.locator('p-accordionTab');
        const tabCount = await accordionTabs.count();
        console.log(`Accordion tabs count: ${tabCount}`);
        
        if (tabCount > 0) {
          // Get the first tab's content
          const firstTab = accordionTabs.first();
          const tabHTML = await firstTab.innerHTML();
          console.log(`First tab HTML: ${tabHTML.substring(0, 200)}...`);
          
          // Try to click the tab
          await firstTab.click();
          console.log('Clicked on accordion tab');
          
          // Check if content is visible after click
          const content = firstTab.locator('.code-file-content');
          const contentVisible = await content.isVisible();
          console.log(`Content visible after click: ${contentVisible}`);
        }
      }
    }
  });
});
