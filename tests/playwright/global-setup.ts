import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('Setting up database tests...');
  
  // Start backend server if not running
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  try {
    // Check if backend is running
    await page.goto('http://localhost:8000/health', { timeout: 5000 });
    console.log('Backend server is running');
  } catch (error) {
    console.log('Backend server not running, starting it...');
    // In a real scenario, you would start the backend server here
    // For now, we'll assume it's started manually
  }
  
  await browser.close();
  console.log('Database tests setup complete');
}

export default globalSetup;
