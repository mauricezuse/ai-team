import { test, expect } from '@playwright/test';

test.describe('Console Errors Debug', () => {
  test('check for console errors on workflow page', async ({ page }) => {
    // Listen for console errors
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Navigate to workflow detail page
    await page.goto('/workflows/12');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
    
    // Wait a bit more for any async operations
    await page.waitForTimeout(2000);
    
    // Check for console errors
    if (consoleErrors.length > 0) {
      console.log('Console errors found:');
      consoleErrors.forEach(error => console.log(`  - ${error}`));
    } else {
      console.log('No console errors found');
    }
    
    // Take a screenshot
    await page.screenshot({ path: 'console-debug.png', fullPage: true });
    
    // Check if PrimeNG is loaded
    const primeNGLoaded = await page.evaluate(() => {
      return typeof (window as any).PrimeNG !== 'undefined';
    });
    console.log(`PrimeNG loaded: ${primeNGLoaded}`);
    
    // Check if the accordion component is available
    const accordionAvailable = await page.evaluate(() => {
      return document.querySelector('p-accordion') !== null;
    });
    console.log(`Accordion component found: ${accordionAvailable}`);
    
    // Check the actual HTML structure
    const htmlContent = await page.content();
    const hasCodeFiles = htmlContent.includes('code-files');
    const hasAccordion = htmlContent.includes('p-accordion');
    const hasAccordionTab = htmlContent.includes('p-accordionTab');
    
    console.log(`HTML contains 'code-files': ${hasCodeFiles}`);
    console.log(`HTML contains 'p-accordion': ${hasAccordion}`);
    console.log(`HTML contains 'p-accordionTab': ${hasAccordionTab}`);
    
    // Check if conversations are expanded
    const expandedConversations = await page.locator('.conversation-details').count();
    console.log(`Expanded conversations: ${expandedConversations}`);
  });
});
