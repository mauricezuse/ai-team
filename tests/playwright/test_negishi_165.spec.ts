import { test, expect } from '@playwright/test';

test.describe('NEGISHI-165 E2E - create, execute, validate conversations and files', () => {
  test('should recreate NEGISHI-165, execute, and show conversations and files', async ({ page, request }) => {
    test.setTimeout(120_000);
    const storyId = 'NEGISHI-165';
    const apiBase = 'http://localhost:8000';

    // Navigate directly to workflows list
    await page.goto('/workflows');
    await page.getByRole('heading', { name: 'Workflows' }).waitFor({ state: 'visible' });

    // Helper: find workflow id by story id via API
    async function findWorkflowId(): Promise<number | null> {
      const res = await request.get(`${apiBase}/workflows`, { timeout: 15000 });
      expect(res.ok()).toBeTruthy();
      const list = await res.json();
      const wf = list.find((w: any) => w.jira_story_id === storyId);
      return wf ? wf.id : null;
    }

    // If exists, delete via API for clean slate
    const existingId = await findWorkflowId();
    if (existingId) {
    const del = await request.delete(`${apiBase}/workflows/${existingId}`, { timeout: 15000 });
      expect(del.ok()).toBeTruthy();
      // Refresh UI list
      await page.reload();
    }

    // Ensure button is present
    await page.getByTestId('create-from-jira-button').waitFor({ state: 'visible' });

    // Register prompt handler BEFORE clicking
    page.once('dialog', async (dialog) => {
      expect(dialog.type()).toBe('prompt');
      await dialog.accept(storyId);
    });
    // Create from Jira via UI button
    await page.getByTestId('create-from-jira-button').click();

    // Wait for toast or table update
    await page.waitForTimeout(1000);

    // Verify it exists via API and capture id (poll up to 30s)
    let newId: number | null = null;
    const until = Date.now() + 30_000;
    while (Date.now() < until) {
      newId = await findWorkflowId();
      if (newId) break;
      await new Promise(r => setTimeout(r, 1000));
    }
    if (!newId) {
      // Diagnostics: dump backend list
      const resList = await request.get(`${apiBase}/workflows`, { timeout: 15000 });
      const body = resList.ok() ? await resList.json() : { error: await resList.text() };
      expect(newId, `Workflow was not created for NEGISHI-165. Diagnostics: ${JSON.stringify(body)}`).toBeTruthy();
    }

    // Open detail page via UI
    await page.getByTestId('workflows-table').getByRole('row').filter({ hasText: storyId }).first().click();
    await page.getByTestId('workflow-title').waitFor({ state: 'visible' });

    // Execute workflow
    await page.getByTestId('execute-button').click();

    // Wait for execution to complete (status should change to completed)
    // Poll backend for status up to 90s
    const deadline = Date.now() + 90_000;
    let status = 'running';
    while (Date.now() < deadline) {
      const res = await request.get(`${apiBase}/workflows/${newId}`, { timeout: 15000 });
      if (!res.ok()) break;
      const body = await res.json();
      status = body.status;
      if (status === 'completed' || status === 'error') break;
      await new Promise(r => setTimeout(r, 2000));
    }

    expect(status).toBe('completed');

    // Check conversations visible in UI
    const conversations = page.locator('[data-testid="conversation"]');
    await expect(conversations.first(), 'No conversations rendered in UI').toBeVisible();

    // Check code files visible in UI
    const codeFiles = page.locator('[data-testid="code-file"]');
    // Allow zero or more, but prefer at least one
    const codeFileCount = await codeFiles.count();

    if (codeFileCount === 0) {
      // Diagnose: fetch backend detail and fail with reason
      const detail = await request.get(`/api/workflows/${newId}`);
      const json = await detail.json();
      const convCount = (json.conversations || []).length;
      // If no conversations or code_files in backend, report
      const hasAnyFiles = (json.conversations || []).some((c: any) => (c.code_files || []).length > 0);
      const diag = JSON.stringify({ status: json.status, convCount, hasAnyFiles, conversations: json.conversations }, null, 2);
      expect(codeFileCount, `No code files rendered. Backend detail: ${diag}`).toBeGreaterThan(0);
    }
  });
});


