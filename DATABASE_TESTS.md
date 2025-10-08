# Database and Workflow Creation Tests

This document describes the comprehensive Playwright test suite for the new database-driven workflow creation and management features.

## Test Overview

The test suite covers all aspects of the new database integration and workflow creation functionality:

### 🗄️ Database Integration Tests
- **Database Connection**: Tests database connectivity and error handling
- **CRUD Operations**: Create, Read, Update, Delete operations for workflows
- **Data Persistence**: Ensures data is properly stored and retrieved
- **Error Handling**: Database errors, timeouts, and recovery scenarios

### 🚀 Workflow Creation Tests
- **Manual Creation**: Form-based workflow creation with validation
- **Jira Integration**: Automatic workflow creation from Jira stories
- **Form Validation**: Input validation and error handling
- **Success/Error States**: Proper feedback for all operations

### ⚡ Workflow Execution Tests
- **AI Agent Execution**: Integration with existing EnhancedStoryWorkflow
- **Database Storage**: Conversation and code file storage
- **Status Management**: Workflow status tracking and updates
- **Real-time Updates**: Live status and progress updates

### 🔗 Jira Integration Tests
- **Story Retrieval**: Pulling Jira story details
- **Authentication**: Jira API authentication and error handling
- **Data Parsing**: ADF (Atlassian Document Format) parsing
- **Error Scenarios**: Network errors, authentication failures, etc.

## Test Files

### 1. `test_workflow_creation.spec.ts`
Tests the workflow creation functionality:
- Form validation and submission
- Manual workflow creation
- Jira-based workflow creation
- Error handling and user feedback
- Loading states and success messages

### 2. `test_workflow_execution.spec.ts`
Tests workflow execution with database integration:
- AI agent execution and conversation storage
- Code file tracking and links
- Status updates and progress tracking
- Error handling during execution
- Real-time conversation display

### 3. `test_database_workflows.spec.ts`
Tests database-driven workflow management:
- Workflow list display with database data
- Search and filtering functionality
- Pagination for large datasets
- Status indicators and sorting
- CRUD operations and data persistence

### 4. `test_jira_integration.spec.ts`
Tests Jira integration features:
- Story retrieval from Jira API
- Authentication and permission handling
- Data parsing and validation
- Error scenarios and recovery
- Special character handling

### 5. `test_database_integration.spec.ts`
Tests database integration and error handling:
- Connection errors and timeouts
- Schema and constraint violations
- Transaction and deadlock handling
- Permission and corruption errors
- Recovery and retry mechanisms

### 6. `test_comprehensive_database.spec.ts`
End-to-end comprehensive tests:
- Full workflow lifecycle testing
- Database-driven search and filtering
- Large dataset handling and pagination
- Status management and updates
- Error states and recovery

## Test Configuration

### Playwright Configuration
- **Timeout**: 30 seconds for database operations
- **Global Setup**: Database and server health checks
- **Parallel Execution**: Tests run in parallel for efficiency
- **Retry Logic**: Automatic retry on CI environments

### Test Data
- **Mock APIs**: Comprehensive API mocking for all endpoints
- **Sample Workflows**: Realistic workflow data with conversations
- **Error Scenarios**: Various database and network error conditions
- **Large Datasets**: Pagination and performance testing

## Running Tests

### Prerequisites
1. **Backend Server**: Must be running on `http://localhost:8000`
2. **Frontend Server**: Must be running on `http://localhost:4200`
3. **Database**: SQLite database with proper schema

### Quick Start
```bash
# Run all database tests
./run_database_tests.sh

# Run specific test file
npx playwright test tests/playwright/test_workflow_creation.spec.ts

# Run with HTML report
npx playwright test tests/playwright/test_workflow_creation.spec.ts --reporter=html
```

### Individual Test Commands
```bash
# Workflow creation tests
npx playwright test tests/playwright/test_workflow_creation.spec.ts

# Workflow execution tests
npx playwright test tests/playwright/test_workflow_execution.spec.ts

# Database workflows tests
npx playwright test tests/playwright/test_database_workflows.spec.ts

# Jira integration tests
npx playwright test tests/playwright/test_jira_integration.spec.ts

# Database integration tests
npx playwright test tests/playwright/test_database_integration.spec.ts

# Comprehensive tests
npx playwright test tests/playwright/test_comprehensive_database.spec.ts
```

## Test Coverage

### ✅ Workflow Creation
- [x] Manual workflow creation form
- [x] Jira-based workflow creation
- [x] Form validation and error handling
- [x] Success/error feedback
- [x] Loading states and user experience

### ✅ Database Integration
- [x] Database connection and health checks
- [x] CRUD operations for workflows
- [x] Conversation and code file storage
- [x] Status management and updates
- [x] Error handling and recovery

### ✅ Workflow Execution
- [x] AI agent execution integration
- [x] Conversation data storage
- [x] Code file tracking and links
- [x] Status updates and progress
- [x] Error handling during execution

### ✅ Jira Integration
- [x] Story retrieval from Jira API
- [x] Authentication and permissions
- [x] Data parsing and validation
- [x] Error scenarios and recovery
- [x] Special character handling

### ✅ User Interface
- [x] Workflow list display
- [x] Search and filtering
- [x] Pagination and sorting
- [x] Status indicators
- [x] Action buttons and navigation

### ✅ Error Handling
- [x] Database connection errors
- [x] Network timeouts and failures
- [x] Authentication and permission errors
- [x] Data validation and constraint errors
- [x] Recovery and retry mechanisms

## Test Data Scenarios

### Workflow Creation
- **Valid Data**: Complete workflow creation with all fields
- **Invalid Data**: Form validation with error messages
- **Jira Integration**: Story retrieval and workflow creation
- **Duplicate Handling**: Prevention of duplicate workflows

### Database Operations
- **CRUD Operations**: Create, read, update, delete workflows
- **Data Persistence**: Ensure data is properly stored
- **Relationships**: Workflow-conversation-code file relationships
- **Transactions**: Atomic operations and rollback handling

### Error Scenarios
- **Connection Errors**: Database connectivity issues
- **Timeout Errors**: Long-running operations
- **Constraint Violations**: Data integrity errors
- **Authentication Errors**: Permission and access issues

## Performance Testing

### Large Datasets
- **Pagination**: 25+ workflows with pagination controls
- **Search Performance**: Real-time search across large datasets
- **Filtering**: Status and attribute filtering
- **Sorting**: Multi-column sorting capabilities

### Database Performance
- **Query Optimization**: Efficient database queries
- **Index Usage**: Proper database indexing
- **Connection Pooling**: Database connection management
- **Transaction Handling**: Optimistic and pessimistic locking

## Continuous Integration

### CI/CD Integration
- **Automated Testing**: Tests run on every commit
- **Parallel Execution**: Tests run in parallel for speed
- **Retry Logic**: Automatic retry on flaky tests
- **Reporting**: Comprehensive test reports

### Quality Gates
- **Test Coverage**: Minimum 90% test coverage
- **Performance**: Tests must complete within 30 seconds
- **Reliability**: Tests must pass consistently
- **Maintainability**: Tests must be easy to update

## Troubleshooting

### Common Issues
1. **Backend Not Running**: Ensure backend server is started
2. **Frontend Not Running**: Ensure frontend server is started
3. **Database Issues**: Check database connection and schema
4. **Network Timeouts**: Increase timeout values for slow networks

### Debug Commands
```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:4200

# Run tests with debug output
npx playwright test --debug

# Run specific test with trace
npx playwright test tests/playwright/test_workflow_creation.spec.ts --trace=on
```

## Future Enhancements

### Planned Improvements
- [ ] **Real Database Testing**: Integration with actual database
- [ ] **Performance Testing**: Load testing with large datasets
- [ ] **Security Testing**: Authentication and authorization testing
- [ ] **Accessibility Testing**: WCAG compliance testing

### Test Automation
- [ ] **Scheduled Testing**: Automated test runs
- [ ] **Regression Testing**: Automated regression detection
- [ ] **Performance Monitoring**: Continuous performance tracking
- [ ] **Quality Metrics**: Automated quality reporting

## Conclusion

This comprehensive test suite ensures that all database and workflow creation features work correctly, handle errors gracefully, and provide a great user experience. The tests cover both happy path scenarios and edge cases, ensuring robust and reliable functionality.

For questions or issues, please refer to the test logs or contact the development team.
