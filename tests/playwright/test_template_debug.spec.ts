import { test, expect } from '@playwright/test';

test.describe('Template Debug', () => {
  test('check actual template structure', async ({ page }) => {
    // Navigate to workflow detail page
    await page.goto('/workflows/12');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
    
    // Check if the accordion template is actually being used
    const hasAccordionTemplate = await page.evaluate(() => {
      const codeFilesSections = document.querySelectorAll('.code-files');
      for (let section of codeFilesSections) {
        const accordion = section.querySelector('p-accordion');
        if (accordion) {
          return true;
        }
      }
      return false;
    });
    
    console.log(`Accordion template found: ${hasAccordionTemplate}`);
    
    // Check what template is actually being used
    const templateStructure = await page.evaluate(() => {
      const codeFilesSections = document.querySelectorAll('.code-files');
      const structures = [];
      
      for (let section of codeFilesSections) {
        const children = Array.from(section.children).map(child => ({
          tagName: child.tagName,
          className: child.className,
          innerHTML: child.innerHTML.substring(0, 100) + '...'
        }));
        structures.push(children);
      }
      
      return structures;
    });
    
    console.log('Template structures:', JSON.stringify(templateStructure, null, 2));
    
    // Check if there are any Angular binding errors
    const bindingErrors = await page.evaluate(() => {
      const errorElements = document.querySelectorAll('[ng-reflect-ng-for-of="[object Object]"]');
      return errorElements.length;
    });
    
    console.log(`Binding errors found: ${bindingErrors}`);
  });
});
