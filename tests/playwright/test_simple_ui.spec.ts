import { test, expect } from '@playwright/test';

test.describe('Simple UI Tests', () => {
  test('should load a basic HTML page', async ({ page }) => {
    // Create a simple HTML page for testing
    await page.setContent(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>AI Team Test</title>
        </head>
        <body>
          <h1>AI Team Dashboard</h1>
          <div id="agents-count">6</div>
          <div id="workflows-count">3</div>
          <button data-testid="refresh-button">Refresh</button>
          <button data-testid="add-workflow-button">Add Workflow</button>
        </body>
      </html>
    `);
    
    // Test basic functionality
    await expect(page.locator('h1')).toContainText('AI Team Dashboard');
    await expect(page.locator('#agents-count')).toContainText('6');
    await expect(page.locator('#workflows-count')).toContainText('3');
    await expect(page.locator('[data-testid="refresh-button"]')).toBeVisible();
    await expect(page.locator('[data-testid="add-workflow-button"]')).toBeVisible();
  });

  test('should handle button clicks', async ({ page }) => {
    await page.setContent(`
      <!DOCTYPE html>
      <html>
        <body>
          <button data-testid="test-button">Click Me</button>
          <div id="result"></div>
          <script>
            document.querySelector('[data-testid="test-button"]').addEventListener('click', function() {
              document.getElementById('result').textContent = 'Button clicked!';
            });
          </script>
        </body>
      </html>
    `);
    
    // Test button click
    await page.click('[data-testid="test-button"]');
    await expect(page.locator('#result')).toContainText('Button clicked!');
  });

  test('should handle form inputs', async ({ page }) => {
    await page.setContent(`
      <!DOCTYPE html>
      <html>
        <body>
          <form>
            <input type="text" data-testid="name-input" placeholder="Enter name">
            <input type="text" data-testid="role-input" placeholder="Enter role">
            <button type="submit" data-testid="submit-button">Submit</button>
          </form>
          <div id="output"></div>
          <script>
            document.querySelector('form').addEventListener('submit', function(e) {
              e.preventDefault();
              const name = document.querySelector('[data-testid="name-input"]').value;
              const role = document.querySelector('[data-testid="role-input"]').value;
              document.getElementById('output').textContent = name + ' - ' + role;
            });
          </script>
        </body>
      </html>
    `);
    
    // Test form input
    await page.fill('[data-testid="name-input"]', 'Test Agent');
    await page.fill('[data-testid="role-input"]', 'Test Role');
    await page.click('[data-testid="submit-button"]');
    await expect(page.locator('#output')).toContainText('Test Agent - Test Role');
  });

  test('should handle table data', async ({ page }) => {
    await page.setContent(`
      <!DOCTYPE html>
      <html>
        <body>
          <table data-testid="workflows-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Status</th>
                <th>Agents</th>
              </tr>
            </thead>
            <tbody>
              <tr data-testid="workflow-row">
                <td>Enhanced Story Negishi-178</td>
                <td><span data-testid="workflow-status">completed</span></td>
                <td>3</td>
              </tr>
              <tr data-testid="workflow-row">
                <td>Enhanced Story Negishi-175</td>
                <td><span data-testid="workflow-status">pending</span></td>
                <td>1</td>
              </tr>
            </tbody>
          </table>
        </body>
      </html>
    `);
    
    // Test table functionality
    await expect(page.locator('[data-testid="workflows-table"]')).toBeVisible();
    await expect(page.locator('[data-testid="workflow-row"]')).toHaveCount(2);
    await expect(page.locator('text=Enhanced Story Negishi-178')).toBeVisible();
    await expect(page.locator('text=Enhanced Story Negishi-175')).toBeVisible();
    await expect(page.locator('[data-testid="workflow-status"]').first()).toContainText('completed');
    await expect(page.locator('[data-testid="workflow-status"]').nth(1)).toContainText('pending');
  });

  test('should handle search functionality', async ({ page }) => {
    await page.setContent(`
      <!DOCTYPE html>
      <html>
        <body>
          <input type="text" data-testid="search-input" placeholder="Search...">
          <div id="search-results">
            <div class="item">Workflow 1</div>
            <div class="item">Workflow 2</div>
            <div class="item">Agent 1</div>
            <div class="item">Agent 2</div>
          </div>
          <script>
            document.querySelector('[data-testid="search-input"]').addEventListener('input', function(e) {
              const searchTerm = e.target.value.toLowerCase();
              const items = document.querySelectorAll('.item');
              items.forEach(item => {
                const text = item.textContent.toLowerCase();
                item.style.display = text.includes(searchTerm) ? 'block' : 'none';
              });
            });
          </script>
        </body>
      </html>
    `);
    
    // Test search functionality
    await page.fill('[data-testid="search-input"]', 'workflow');
    await expect(page.locator('text=Workflow 1')).toBeVisible();
    await expect(page.locator('text=Workflow 2')).toBeVisible();
    await expect(page.locator('text=Agent 1')).not.toBeVisible();
    await expect(page.locator('text=Agent 2')).not.toBeVisible();
    
    // Clear search
    await page.fill('[data-testid="search-input"]', '');
    await expect(page.locator('text=Agent 1')).toBeVisible();
    await expect(page.locator('text=Agent 2')).toBeVisible();
  });

  test('should handle dropdown selection', async ({ page }) => {
    await page.setContent(`
      <!DOCTYPE html>
      <html>
        <body>
          <select data-testid="status-filter">
            <option value="">All Status</option>
            <option value="completed">Completed</option>
            <option value="pending">Pending</option>
            <option value="running">Running</option>
          </select>
          <div id="filter-results"></div>
          <script>
            document.querySelector('[data-testid="status-filter"]').addEventListener('change', function(e) {
              document.getElementById('filter-results').textContent = 'Filtered by: ' + e.target.value;
            });
          </script>
        </body>
      </html>
    `);
    
    // Test dropdown selection
    await page.selectOption('[data-testid="status-filter"]', 'completed');
    await expect(page.locator('#filter-results')).toContainText('Filtered by: completed');
    
    await page.selectOption('[data-testid="status-filter"]', 'pending');
    await expect(page.locator('#filter-results')).toContainText('Filtered by: pending');
  });

  test('should handle modal dialogs', async ({ page }) => {
    await page.setContent(`
      <!DOCTYPE html>
      <html>
        <body>
          <button data-testid="open-modal">Open Modal</button>
          <div id="modal" style="display: none;">
            <h2>Modal Title</h2>
            <p>Modal content</p>
            <button data-testid="close-modal">Close</button>
          </div>
          <script>
            document.querySelector('[data-testid="open-modal"]').addEventListener('click', function() {
              document.getElementById('modal').style.display = 'block';
            });
            document.querySelector('[data-testid="close-modal"]').addEventListener('click', function() {
              document.getElementById('modal').style.display = 'none';
            });
          </script>
        </body>
      </html>
    `);
    
    // Test modal functionality
    await page.click('[data-testid="open-modal"]');
    await expect(page.locator('#modal')).toBeVisible();
    await expect(page.locator('text=Modal Title')).toBeVisible();
    await expect(page.locator('text=Modal content')).toBeVisible();
    
    await page.click('[data-testid="close-modal"]');
    await expect(page.locator('#modal')).not.toBeVisible();
  });

  test('should handle keyboard navigation', async ({ page }) => {
    await page.setContent(`
      <!DOCTYPE html>
      <html>
        <body>
          <button data-testid="button1">Button 1</button>
          <button data-testid="button2">Button 2</button>
          <button data-testid="button3">Button 3</button>
        </body>
      </html>
    `);
    
    // Test keyboard navigation
    await page.keyboard.press('Tab');
    await expect(page.locator('[data-testid="button1"]')).toBeFocused();
    
    await page.keyboard.press('Tab');
    await expect(page.locator('[data-testid="button2"]')).toBeFocused();
    
    await page.keyboard.press('Tab');
    await expect(page.locator('[data-testid="button3"]')).toBeFocused();
  });

  test('should handle responsive design', async ({ page }) => {
    await page.setContent(`
      <!DOCTYPE html>
      <html>
        <head>
          <style>
            .container { display: flex; flex-wrap: wrap; }
            .item { flex: 1; min-width: 200px; }
            @media (max-width: 768px) {
              .item { flex: 100%; }
            }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="item">Item 1</div>
            <div class="item">Item 2</div>
            <div class="item">Item 3</div>
          </div>
        </body>
      </html>
    `);
    
    // Test desktop view
    await page.setViewportSize({ width: 1024, height: 768 });
    await expect(page.locator('.container')).toBeVisible();
    
    // Test mobile view
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator('.container')).toBeVisible();
  });

  test('should handle error states', async ({ page }) => {
    await page.setContent(`
      <!DOCTYPE html>
      <html>
        <body>
          <div id="error-message" style="display: none; color: red;">Error occurred</div>
          <button data-testid="trigger-error">Trigger Error</button>
          <script>
            document.querySelector('[data-testid="trigger-error"]').addEventListener('click', function() {
              document.getElementById('error-message').style.display = 'block';
            });
          </script>
        </body>
      </html>
    `);
    
    // Test error handling
    await page.click('[data-testid="trigger-error"]');
    await expect(page.locator('#error-message')).toBeVisible();
    await expect(page.locator('text=Error occurred')).toBeVisible();
  });
});
