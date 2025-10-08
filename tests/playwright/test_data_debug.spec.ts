import { test, expect } from '@playwright/test';

test.describe('Data Debug', () => {
  test('debug conversation data structure', async ({ page }) => {
    // Navigate to workflow detail page
    await page.goto('/workflows/12');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
    
    // Check the actual data being passed to the template
    const conversationData = await page.evaluate(() => {
      // Find the conversation with implementation_plan_generated step
      const conversations = document.querySelectorAll('[data-testid="conversation"]');
      for (let i = 0; i < conversations.length; i++) {
        const conversation = conversations[i];
        const stepBadge = conversation.querySelector('.step-badge');
        if (stepBadge && stepBadge.textContent?.includes('implementation_plan_generated')) {
          const codeFilesSection = conversation.querySelector('.code-files');
          if (codeFilesSection) {
            const accordion = codeFilesSection.querySelector('p-accordion');
            const accordionTabs = codeFilesSection.querySelectorAll('p-accordionTab');
            
            return {
              hasCodeFilesSection: !!codeFilesSection,
              hasAccordion: !!accordion,
              accordionTabCount: accordionTabs.length,
              codeFilesSectionHTML: codeFilesSection.innerHTML,
              conversationHTML: conversation.innerHTML
            };
          }
        }
      }
      return null;
    });
    
    console.log('Conversation data:', conversationData);
    
    // Also check the raw API data
    const apiData = await page.evaluate(async () => {
      try {
        const response = await fetch('/api/workflows/12');
        const data = await response.json();
        const targetConversation = data.conversations.find((c: any) => c.step === 'implementation_plan_generated');
        return {
          hasTargetConversation: !!targetConversation,
          codeFiles: targetConversation?.code_files || [],
          codeFilesLength: targetConversation?.code_files?.length || 0
        };
      } catch (error) {
        return { error: error.message };
      }
    });
    
    console.log('API data:', apiData);
  });
});
