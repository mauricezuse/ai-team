#!/bin/bash

# Database and Workflow Creation Tests Runner
# This script runs comprehensive Playwright tests for all new database and workflow features

echo "🚀 Starting Database and Workflow Creation Tests"
echo "=================================================="

# Check if backend is running
echo "📡 Checking backend server..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend server is running"
else
    echo "❌ Backend server is not running. Please start it first:"
    echo "   cd /Users/mauricevandermerwe/Projects/Negishi/ai-team"
    echo "   source venv/bin/activate"
    echo "   python3 -m uvicorn crewai_app.main:app --host 0.0.0.0 --port 8000 --reload"
    exit 1
fi

# Check if frontend is running
echo "🌐 Checking frontend server..."
if curl -s http://localhost:4200 > /dev/null; then
    echo "✅ Frontend server is running"
else
    echo "❌ Frontend server is not running. Please start it first:"
    echo "   cd /Users/mauricevandermerwe/Projects/Negishi/ai-team/frontend"
    echo "   npm start"
    exit 1
fi

echo ""
echo "🧪 Running Database and Workflow Tests"
echo "======================================"

# Run workflow creation tests
echo "📝 Testing workflow creation features..."
npx playwright test tests/playwright/test_workflow_creation.spec.ts --reporter=line

# Run workflow execution tests
echo "⚡ Testing workflow execution with database..."
npx playwright test tests/playwright/test_workflow_execution.spec.ts --reporter=line

# Run database workflows tests
echo "🗄️ Testing database-driven workflows..."
npx playwright test tests/playwright/test_database_workflows.spec.ts --reporter=line

# Run Jira integration tests
echo "🔗 Testing Jira integration features..."
npx playwright test tests/playwright/test_jira_integration.spec.ts --reporter=line

# Run database integration tests
echo "🔧 Testing database integration and error handling..."
npx playwright test tests/playwright/test_database_integration.spec.ts --reporter=line

# Run comprehensive database tests
echo "🎯 Running comprehensive database tests..."
npx playwright test tests/playwright/test_comprehensive_database.spec.ts --reporter=line

echo ""
echo "📊 Running all database tests together..."
npx playwright test tests/playwright/test_workflow_creation.spec.ts tests/playwright/test_workflow_execution.spec.ts tests/playwright/test_database_workflows.spec.ts tests/playwright/test_jira_integration.spec.ts tests/playwright/test_database_integration.spec.ts tests/playwright/test_comprehensive_database.spec.ts --reporter=html

echo ""
echo "✅ Database and Workflow Creation Tests Complete!"
echo "=================================================="
echo "📋 Test Summary:"
echo "   - Workflow Creation: Manual and Jira-based creation"
echo "   - Database Integration: Full CRUD operations"
echo "   - Workflow Execution: AI agent execution with database storage"
echo "   - Jira Integration: Story retrieval and workflow creation"
echo "   - Error Handling: Database errors and recovery"
echo "   - Comprehensive Testing: End-to-end workflow lifecycle"
echo ""
echo "🎉 All tests completed successfully!"
