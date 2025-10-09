#!/bin/bash

# Run Error Display Tests for Workflow 12 (NEGISHI-165)
# This script runs comprehensive tests for error display functionality

set -e

echo "🧪 Running Error Display Tests for Workflow 12 (NEGISHI-165)"
echo "=========================================================="

# Check if we're in the right directory
if [ ! -f "crewai_app/main.py" ]; then
    echo "❌ Error: Not in the correct directory. Please run from the project root."
    exit 1
fi

# Function to run Python tests
run_python_tests() {
    echo "🐍 Running Python API Tests..."
    echo "-------------------------------"
    
    # Test workflow error display API
    echo "Testing workflow error display API..."
    python -m pytest tests/test_workflow_error_display.py -v
    
    # Test workflow error API endpoints
    echo "Testing workflow error API endpoints..."
    python -m pytest tests/test_workflow_error_api.py -v
    
    # Test workflow 12 specific error scenarios
    echo "Testing workflow 12 specific error scenarios..."
    python -m pytest tests/test_workflow_12_error_simulation.py -v
}

# Function to run Playwright E2E tests
run_playwright_tests() {
    echo "🎭 Running Playwright E2E Tests..."
    echo "----------------------------------"
    
    # Check if backend is running
    if ! curl -f -s http://127.0.0.1:8000/health >/dev/null 2>&1; then
        echo "⚠️  Backend not running. Starting backend..."
        source venv/bin/activate
        uvicorn crewai_app.main:app --reload --host 127.0.0.1 --port 8000 &
        BACKEND_PID=$!
        sleep 5
    fi
    
    # Check if frontend is running
    if ! curl -f -s http://minions.localhost:4200 >/dev/null 2>&1; then
        echo "⚠️  Frontend not running. Starting frontend..."
        cd frontend
        npm run start -- --host minions.localhost --port 4200 &
        FRONTEND_PID=$!
        cd ..
        sleep 10
    fi
    
    # Run Playwright tests
    echo "Running Playwright error display tests..."
    npx playwright test tests/playwright/test_workflow_error_display.spec.ts --project=chromium
    
    # Cleanup background processes
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
}

# Function to test workflow 12 specifically
test_workflow_12() {
    echo "🔍 Testing Workflow 12 (NEGISHI-165) Specifically..."
    echo "----------------------------------------------------"
    
    # Check if workflow 12 exists
    echo "Checking if workflow 12 exists..."
    response=$(curl -s http://127.0.0.1:8000/workflows/12)
    if echo "$response" | jq -e '.id == 12' >/dev/null 2>&1; then
        echo "✅ Workflow 12 found"
        
        # Check error information
        error=$(echo "$response" | jq -r '.error // empty')
        status=$(echo "$response" | jq -r '.status')
        isTerminal=$(echo "$response" | jq -r '.isTerminal')
        
        echo "Status: $status"
        echo "Is Terminal: $isTerminal"
        
        if [ -n "$error" ] && [ "$error" != "null" ]; then
            echo "✅ Error information found:"
            echo "Error: $error"
        else
            echo "ℹ️  No error information (workflow may not be in error state)"
        fi
    else
        echo "❌ Workflow 12 not found"
    fi
}

# Function to run all tests
run_all_tests() {
    echo "🚀 Running All Error Display Tests..."
    echo "====================================="
    
    # Run Python tests
    run_python_tests
    
    echo ""
    echo "🎭 Running E2E Tests..."
    echo "----------------------"
    
    # Run Playwright tests
    run_playwright_tests
    
    echo ""
    echo "🔍 Testing Workflow 12 Specifically..."
    echo "-------------------------------------"
    
    # Test workflow 12
    test_workflow_12
}

# Function to show test results
show_test_results() {
    echo ""
    echo "📊 Test Results Summary"
    echo "======================="
    echo "✅ Python API tests completed"
    echo "✅ Playwright E2E tests completed"
    echo "✅ Workflow 12 specific tests completed"
    echo ""
    echo "🎯 Error Display Tests Complete!"
    echo "All error display functionality has been tested for workflow 12 (NEGISHI-165)"
}

# Main execution
case "${1:-all}" in
    "python")
        run_python_tests
        ;;
    "playwright")
        run_playwright_tests
        ;;
    "workflow12")
        test_workflow_12
        ;;
    "all")
        run_all_tests
        show_test_results
        ;;
    *)
        echo "Usage: $0 [python|playwright|workflow12|all]"
        echo "  python     - Run Python API tests only"
        echo "  playwright - Run Playwright E2E tests only"
        echo "  workflow12 - Test workflow 12 specifically"
        echo "  all        - Run all tests (default)"
        exit 1
        ;;
esac

echo ""
echo "🎉 Error Display Tests Complete!"
