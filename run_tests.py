#!/usr/bin/env python3
"""
Test runner script for the AI-Team project
Runs unit tests, integration tests, and Playwright tests
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✅ SUCCESS")
        if result.stdout:
            print("STDOUT:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ FAILED")
        print("STDERR:", e.stderr)
        if e.stdout:
            print("STDOUT:", e.stdout)
        return False

def main():
    """Main test runner"""
    print("🧪 AI-Team Test Suite")
    print("=" * 60)
    
    # Change to project root directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Test results tracking
    results = {}
    
    # 1. Run unit tests for API endpoints
    print("\n📋 Running Unit Tests...")
    unit_test_command = "python -m pytest tests/test_api_endpoints.py -v --tb=short"
    results['unit_tests'] = run_command(unit_test_command, "Unit Tests for API Endpoints")
    
    # 2. Run integration tests
    print("\n🔗 Running Integration Tests...")
    integration_test_command = "python -m pytest tests/test_workflow_integration.py -v --tb=short"
    results['integration_tests'] = run_command(integration_test_command, "Integration Tests for Workflow Execution")
    
    # 3. Run Playwright tests (if frontend is available)
    print("\n🎭 Running Playwright Tests...")
    if os.path.exists("frontend/package.json"):
        # Install Playwright browsers if needed
        print("Installing Playwright browsers...")
        playwright_install_command = "cd frontend && npx playwright install --with-deps"
        run_command(playwright_install_command, "Install Playwright Browsers")
        
        # Run Playwright tests
        playwright_test_command = "cd frontend && npx playwright test ../tests/playwright --reporter=html"
        results['playwright_tests'] = run_command(playwright_test_command, "Playwright E2E Tests")
    else:
        print("⚠️  Frontend not found, skipping Playwright tests")
        results['playwright_tests'] = None
    
    # 4. Run all tests together
    print("\n🚀 Running All Tests...")
    all_tests_command = "python -m pytest tests/ -v --tb=short"
    results['all_tests'] = run_command(all_tests_command, "All Python Tests")
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    for test_type, success in results.items():
        if success is None:
            status = "⏭️  SKIPPED"
        elif success:
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        print(f"{test_type.replace('_', ' ').title()}: {status}")
    
    # Overall result
    failed_tests = [k for k, v in results.items() if v is False]
    if failed_tests:
        print(f"\n❌ {len(failed_tests)} test suite(s) failed: {', '.join(failed_tests)}")
        sys.exit(1)
    else:
        print("\n🎉 All tests passed successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()
