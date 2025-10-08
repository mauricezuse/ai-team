#!/bin/bash

# Comprehensive Playwright Test Runner for AI Team Frontend
# This script runs all Playwright tests and ensures the UI functions correctly

set -e  # Exit on any error

echo "🚀 Starting Comprehensive Playwright Test Suite"
echo "================================================"

# Check if Playwright is installed
if ! command -v npx &> /dev/null; then
    echo "❌ Error: npx not found. Please install Node.js and npm."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found. Please run this script from the project root."
    exit 1
fi

# Install dependencies if needed
echo "📦 Checking dependencies..."
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Install Playwright browsers if needed
echo "🎭 Installing Playwright browsers..."
npx playwright install

# Create test results directory
mkdir -p test-results/playwright

# Run the comprehensive UI tests
echo "🧪 Running Complete UI Functionality Tests..."
npx playwright test tests/playwright/test_complete_ui.spec.ts \
    --reporter=html \
    --output-dir=test-results/playwright \
    --retries=2 \
    --timeout=30000

# Run the agent detail tests
echo "👤 Running Agent Detail Page Tests..."
npx playwright test tests/playwright/test_agent_detail.spec.ts \
    --reporter=html \
    --output-dir=test-results/playwright \
    --retries=2 \
    --timeout=30000

# Run all Playwright tests
echo "🎯 Running All Playwright Tests..."
npx playwright test tests/playwright/ \
    --reporter=html \
    --output-dir=test-results/playwright \
    --retries=2 \
    --timeout=30000

# Generate test report
echo "📊 Generating Test Report..."
npx playwright show-report test-results/playwright

echo "✅ All Playwright tests completed!"
echo "📁 Test results saved to: test-results/playwright"
echo "🌐 Open the HTML report to view detailed results"
