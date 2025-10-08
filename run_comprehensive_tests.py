#!/usr/bin/env python3
"""
Comprehensive test runner for AI-Team project.
Runs all Python tests and provides instructions for Playwright tests.
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def run_command(command, description, cwd=None):
    """Run a command and return success status."""
    print(f"\n🔄 {description}...")
    print(f"Command: {command}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout:
                print("Output:", result.stdout)
            return True
        else:
            print(f"❌ {description} - FAILED")
            if result.stdout:
                print("Output:", result.stdout)
            if result.stderr:
                print("Error:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - TIMEOUT")
        return False
    except Exception as e:
        print(f"💥 {description} - ERROR: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    # Check Python dependencies
    python_deps = ['pytest', 'fastapi', 'uvicorn', 'httpx']
    missing_deps = []
    
    for dep in python_deps:
        try:
            __import__(dep)
        except ImportError:
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"❌ Missing Python dependencies: {missing_deps}")
        print("Installing missing dependencies...")
        install_cmd = f"{sys.executable} -m pip install {' '.join(missing_deps)}"
        if not run_command(install_cmd, "Installing Python dependencies"):
            return False
    
    # Check if frontend directory exists
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return False
    
    # Check if package.json exists in frontend
    package_json = frontend_dir / "package.json"
    if not package_json.exists():
        print("❌ package.json not found in frontend directory")
        return False
    
    print("✅ All dependencies check passed")
    return True

def run_python_tests():
    """Run all Python unit and integration tests."""
    print("\n" + "="*60)
    print("🐍 RUNNING PYTHON TESTS")
    print("="*60)
    
    test_files = [
        "tests/test_api_endpoints.py",
        "tests/test_workflow_integration.py", 
        "tests/test_workflow_data_parsing.py",
        "tests/test_agent_collaboration.py"
    ]
    
    # Check if test files exist
    existing_tests = []
    for test_file in test_files:
        if Path(test_file).exists():
            existing_tests.append(test_file)
        else:
            print(f"⚠️  Test file not found: {test_file}")
    
    if not existing_tests:
        print("❌ No test files found!")
        return False
    
    # Run pytest with verbose output
    test_cmd = f"{sys.executable} -m pytest {' '.join(existing_tests)} -v --tb=short"
    return run_command(test_cmd, "Python Unit and Integration Tests")

def run_playwright_tests():
    """Run Playwright E2E tests."""
    print("\n" + "="*60)
    print("🎭 RUNNING PLAYWRIGHT TESTS")
    print("="*60)
    
    # Check if Playwright is installed
    playwright_installed = run_command(
        "npx playwright --version",
        "Checking Playwright installation",
        cwd="frontend"
    )
    
    if not playwright_installed:
        print("Installing Playwright...")
        install_playwright = run_command(
            "npm install -D @playwright/test",
            "Installing Playwright",
            cwd="frontend"
        )
        if not install_playwright:
            return False
        
        install_browsers = run_command(
            "npx playwright install",
            "Installing Playwright browsers",
            cwd="frontend"
        )
        if not install_browsers:
            return False
    
    # Run Playwright tests
    playwright_cmd = "npx playwright test ../tests/playwright --reporter=html"
    return run_command(playwright_cmd, "Playwright E2E Tests", cwd="frontend")

def check_services_running():
    """Check if required services are running."""
    print("\n🔍 Checking if services are running...")
    
    # Check if backend is running on port 8000
    backend_running = run_command(
        "curl -s http://localhost:8000/health",
        "Checking backend service"
    )
    
    # Check if frontend is running on port 4200
    frontend_running = run_command(
        "curl -s http://localhost:4200/",
        "Checking frontend service"
    )
    
    if not backend_running:
        print("⚠️  Backend service not running on port 8000")
        print("   Please start the backend with: python -m crewai_app.main")
    
    if not frontend_running:
        print("⚠️  Frontend service not running on port 4200")
        print("   Please start the frontend with: cd frontend && npm start")
    
    return backend_running and frontend_running

def main():
    """Main test runner function."""
    print("🚀 AI-Team Comprehensive Test Suite")
    print("="*60)
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Dependency check failed")
        sys.exit(1)
    
    # Check if services are running
    services_ok = check_services_running()
    if not services_ok:
        print("\n⚠️  Some services are not running. Tests may fail.")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Exiting. Please start the required services first.")
            sys.exit(1)
    
    # Run Python tests
    python_success = run_python_tests()
    
    # Run Playwright tests
    playwright_success = run_playwright_tests()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    if python_success:
        print("✅ Python Tests: PASSED")
    else:
        print("❌ Python Tests: FAILED")
    
    if playwright_success:
        print("✅ Playwright Tests: PASSED")
    else:
        print("❌ Playwright Tests: FAILED")
    
    if python_success and playwright_success:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        sys.exit(0)
    else:
        print("\n💥 SOME TESTS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
