import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('🔧 Setting up global test environment...');
  
  // Initialize database if needed
  try {
    const { init_database } = await import('../../crewai_app/database');
    init_database();
    console.log('✅ Database initialized');
  } catch (error) {
    console.log('⚠️ Database initialization skipped (not critical for tests)');
  }
  
  console.log('✅ Global setup complete');
}

export default globalSetup;