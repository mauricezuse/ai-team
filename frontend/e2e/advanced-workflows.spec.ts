import { test, expect } from '@playwright/test';

// Assumes dev server proxy to backend is configured (frontend/proxy.conf.json)

test.describe('Advanced Workflows UI', () => {
  test('should navigate to advanced timeline and render', async ({ page }) => {
    // Navigate to an example workflow detail first if needed; directly open advanced path
    await page.goto('/workflows/1/advanced');
    await expect(page.getByTestId('advanced-workflow-timeline')).toBeVisible();
  });

  test('should open llm calls table route', async ({ page }) => {
    await page.goto('/workflows/1/advanced/llm-calls?conversationId=1');
    await expect(page.getByTestId('llm-calls-table')).toBeVisible();
  });

  test('should open prompt/output viewer route', async ({ page }) => {
    await page.goto('/workflows/1/advanced/prompt-viewer');
    await expect(page.getByTestId('prompt-output-viewer')).toBeVisible();
  });

  test('should open run comparison route', async ({ page }) => {
    await page.goto('/workflows/1/advanced/comparison');
    await expect(page.getByTestId('run-comparison')).toBeVisible();
  });

  test('should open error diagnostics route', async ({ page }) => {
    await page.goto('/workflows/1/advanced/diagnostics');
    await expect(page.getByTestId('error-diagnostics')).toBeVisible();
  });

  test('should open code artifacts route', async ({ page }) => {
    await page.goto('/workflows/1/advanced/artifacts');
    await expect(page.getByTestId('code-artifacts')).toBeVisible();
  });

  test('should open collaboration graph route', async ({ page }) => {
    await page.goto('/workflows/1/advanced/collaboration');
    await expect(page.getByTestId('collaboration-graph')).toBeVisible();
  });

  test('timeline step link should open LLM Calls with conversationId', async ({ page }) => {
    await page.goto('/workflows/12/advanced');
    const link = page.getByTestId('open-llm-calls').first();
    await link.click();
    await expect(page.getByTestId('llm-calls-table')).toBeVisible();
  });
});
