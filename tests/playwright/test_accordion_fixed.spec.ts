import { test, expect } from '@playwright/test';

test.describe('Code Files Accordion - Fixed', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to workflow detail page
    await page.goto('http://localhost:4002/workflows/12');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
  });

  test('should display code files accordion when conversation is expanded', async ({ page }) => {
    // Wait for conversations to load
    await page.waitForSelector('[data-testid="conversation"]', { timeout: 10000 });
    
    // Find a conversation that should have code files (implementation_plan_generated step)
    const conversationWithCodeFiles = page.locator('[data-testid="conversation"]').filter({ hasText: 'implementation_plan_generated' });
    await expect(conversationWithCodeFiles).toBeVisible();
    
    // Check if the conversation is expanded (should be by default)
    const expandedContent = conversationWithCodeFiles.locator('.conversation-details');
    await expect(expandedContent).toBeVisible();
    
    // Look for the code files section
    const codeFilesSection = conversationWithCodeFiles.locator('.code-files');
    await expect(codeFilesSection).toBeVisible();
    
    // Check for the accordion
    const accordion = codeFilesSection.locator('p-accordion');
    await expect(accordion).toBeVisible();
    
    // Check for accordion tabs
    const accordionTabs = accordion.locator('p-accordionTab');
    const tabCount = await accordionTabs.count();
    expect(tabCount).toBeGreaterThan(0);
  });

  test('should display code file information in accordion tabs', async ({ page }) => {
    // Wait for conversations to load
    await page.waitForSelector('[data-testid="conversation"]', { timeout: 10000 });
    
    // Find a conversation with code files
    const conversationWithCodeFiles = page.locator('[data-testid="conversation"]').filter({ hasText: 'implementation_plan_generated' });
    
    // Check for code file accordion tab
    const accordionTab = conversationWithCodeFiles.locator('p-accordionTab').first();
    await expect(accordionTab).toBeVisible();
    
    // Check for file name in accordion header
    const fileHeader = accordionTab.locator('.p-accordionheader');
    await expect(fileHeader).toContainText('implementation-plan.md');
    
    // Click on the accordion tab to expand it
    await accordionTab.click();
    
    // Check for code file content
    const codeFileContent = accordionTab.locator('.code-file-content');
    await expect(codeFileContent).toBeVisible();
    
    // Check for file name, path, and link
    const fileName = codeFileContent.locator('.file-name');
    await expect(fileName).toContainText('implementation-plan.md');
    
    const filePath = codeFileContent.locator('.file-path');
    await expect(filePath).toContainText('docs/architecture/implementation-plan.md');
    
    const fileLink = codeFileContent.locator('.file-link');
    await expect(fileLink).toBeVisible();
    await expect(fileLink).toContainText('View in Repository');
  });

  test('should display code preview when accordion tab is expanded', async ({ page }) => {
    // Wait for conversations to load
    await page.waitForSelector('[data-testid="conversation"]', { timeout: 10000 });
    
    // Find a conversation with code files
    const conversationWithCodeFiles = page.locator('[data-testid="conversation"]').filter({ hasText: 'implementation_plan_generated' });
    
    // Click on the accordion tab to expand it
    const accordionTab = conversationWithCodeFiles.locator('p-accordionTab').first();
    await accordionTab.click();
    
    // Check for code preview
    const codePreview = accordionTab.locator('.code-preview pre code');
    await expect(codePreview).toBeVisible();
    
    // Check that the code preview contains expected content
    const codeContent = await codePreview.textContent();
    expect(codeContent).toContain('implementation-plan.md');
    expect(codeContent).toContain('Description');
    expect(codeContent).toContain('Usage');
  });

  test('should handle conversations without code files gracefully', async ({ page }) => {
    // Wait for conversations to load
    await page.waitForSelector('[data-testid="conversation"]', { timeout: 10000 });
    
    // Find a conversation that should not have code files (story_retrieved_and_analyzed step)
    const conversationWithoutFiles = page.locator('[data-testid="conversation"]').filter({ hasText: 'story_retrieved_and_analyzed' });
    await expect(conversationWithoutFiles).toBeVisible();
    
    // Check that the code files section is not visible
    const codeFilesSection = conversationWithoutFiles.locator('.code-files');
    await expect(codeFilesSection).not.toBeVisible();
  });
});
