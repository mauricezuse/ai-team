# Tests - Test Suites and Quality Assurance

## Overview
Comprehensive testing suite for the AI Team orchestration platform. Includes unit tests, integration tests, and end-to-end (E2E) tests using Playwright for frontend testing and pytest for backend testing.

## Test Architecture

### Test Types
- **Unit Tests**: Individual component and function testing
- **Integration Tests**: API endpoint and service integration testing
- **E2E Tests**: Full user workflow testing with Playwright
- **Performance Tests**: Load and stress testing
- **Accessibility Tests**: WCAG compliance testing

### Test Framework
- **Backend**: pytest with async support
- **Frontend**: Playwright with Chromium browser
- **API Testing**: requests library with test fixtures
- **Database Testing**: SQLite in-memory database for tests

## Directory Structure

```
tests/
├── playwright/              # E2E test suites
│   ├── test_workflow_creation.spec.ts
│   ├── test_workflow_execution.spec.ts
│   ├── test_agent_conversations.spec.ts
│   ├── test_negishi_165.spec.ts
│   └── playwright.config.ts
├── test_workflow_creation_unit.py
├── test_workflow_creation_integration.py
├── global-setup.ts
└── README.md
```

## Playwright E2E Tests

### Configuration
- **Browser**: Chromium (desktop only, mobile disabled)
- **Base URL**: http://localhost:4001 (Angular dev server)
- **Timeout**: 30 seconds for API calls, 120 seconds for workflow execution
- **Parallel**: 4 workers for parallel test execution
- **Retries**: 2 retries for flaky tests

### Test Suites

#### Workflow Creation Tests
- **test_workflow_creation.spec.ts**: Create workflows from Jira stories
- **test_negishi_165.spec.ts**: Specific NEGISHI-165 workflow test
- **Coverage**: Workflow creation, validation, and error handling

#### Workflow Execution Tests
- **test_workflow_execution.spec.ts**: Execute AI agent workflows
- **Coverage**: Workflow execution, agent collaboration, file generation
- **Validation**: Status updates, conversation flow, code file creation

#### Agent Conversation Tests
- **test_agent_conversations.spec.ts**: Agent conversation display
- **Coverage**: Conversation filtering, agent roles, conversation details
- **UI Testing**: Expand/collapse, search functionality, timestamp display

#### Database Integration Tests
- **test_database_integration.spec.ts**: Database operations
- **test_comprehensive_database.spec.ts**: Full database workflow
- **Coverage**: CRUD operations, data persistence, relationship integrity

### Test Data Management
- **Mock Data**: Realistic test data for workflows and conversations
- **Fixtures**: Reusable test data and setup functions
- **Cleanup**: Automatic test data cleanup after each test
- **Isolation**: Each test runs in isolation with fresh data

## Backend Tests

### Unit Tests
- **test_workflow_creation_unit.py**: Workflow creation logic
- **Coverage**: Business logic, validation, error handling
- **Mocking**: External service mocking for isolated testing

### Integration Tests
- **test_workflow_creation_integration.py**: Full workflow integration
- **Coverage**: API endpoints, database operations, service integration
- **Real Services**: Optional real service integration testing

## Test Configuration

### Playwright Config
```typescript
// playwright.config.ts
export default defineConfig({
  testDir: './tests/playwright',
  fullyParallel: true,
  forbidOnly: !!process.env['CI'],
  retries: process.env['CI'] ? 2 : 0,
  workers: process.env['CI'] ? 1 : 4,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:4001',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
```

### Test Environment
- **Backend**: FastAPI server on port 8000
- **Frontend**: Angular dev server on port 4001
- **Database**: SQLite test database
- **External Services**: Mocked or test instances

## Running Tests

### E2E Tests
```bash
# Install Playwright browsers
npx playwright install

# Run all E2E tests
npx playwright test

# Run specific test file
npx playwright test test_negishi_165.spec.ts

# Run tests in headed mode (see browser)
npx playwright test --headed

# Run tests in debug mode
npx playwright test --debug
```

### Backend Tests
```bash
# Run unit tests
pytest tests/test_workflow_creation_unit.py

# Run integration tests
pytest tests/test_workflow_creation_integration.py

# Run all tests with coverage
pytest --cov=crewai_app tests/
```

### Test Reports
- **HTML Report**: Playwright HTML report in `playwright-report/`
- **Coverage Report**: pytest-cov HTML report in `htmlcov/`
- **Screenshots**: Failed test screenshots in `test-results/`
- **Traces**: Playwright traces for debugging

## Test Data

### Mock Workflows
```typescript
const mockWorkflow = {
  id: 1,
  name: "NEGISHI-165: Test Workflow",
  status: "completed",
  conversations: [...],
  code_files: [...]
};
```

### Mock Conversations
```typescript
const mockConversations = [
  {
    agent: "Product Manager",
    step: "story_analysis",
    prompt: "Analyze the requirements...",
    output: "Requirements analysis complete...",
    timestamp: "2024-01-01T00:00:00Z"
  }
];
```

## Quality Assurance

### Test Coverage
- **Backend**: >90% code coverage target
- **Frontend**: Critical user flows covered
- **API**: All endpoints tested
- **Database**: All models and relationships tested

### Performance Testing
- **Load Testing**: Multiple concurrent workflows
- **Stress Testing**: High-volume data processing
- **Memory Testing**: Memory leak detection
- **Response Time**: API response time validation

### Accessibility Testing
- **WCAG Compliance**: Automated accessibility testing
- **Keyboard Navigation**: Full keyboard support testing
- **Screen Reader**: Screen reader compatibility
- **Color Contrast**: Visual accessibility validation

## CI/CD Integration

### GitHub Actions
- **Test Execution**: Automated test runs on PRs
- **Coverage Reporting**: Coverage threshold enforcement
- **Test Artifacts**: Test reports and screenshots
- **Parallel Execution**: Optimized test execution

### Test Environment
- **Docker**: Containerized test environment
- **Database**: Test database setup and teardown
- **External Services**: Mock service configuration
- **Secrets**: Test-specific environment variables

## Debugging Tests

### Playwright Debugging
```bash
# Debug specific test
npx playwright test test_negishi_165.spec.ts --debug

# Show browser during test
npx playwright test --headed

# Generate test code
npx playwright codegen localhost:4001
```

### Test Logs
- **Console Logs**: Browser console output
- **Network Logs**: API request/response logging
- **Screenshots**: Visual test failure documentation
- **Traces**: Step-by-step test execution traces

## Best Practices

### Test Writing
- **Descriptive Names**: Clear test descriptions
- **Single Responsibility**: One assertion per test
- **Setup/Teardown**: Proper test isolation
- **Mocking**: Appropriate use of mocks and stubs

### Test Maintenance
- **Regular Updates**: Keep tests current with code changes
- **Flaky Test Handling**: Identify and fix flaky tests
- **Performance Monitoring**: Track test execution time
- **Coverage Monitoring**: Maintain coverage thresholds
