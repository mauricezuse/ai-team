#!/usr/bin/env python3
"""
E2E Test Runner for message persistence with actual LLM calls.
"""
import sys
import os
import subprocess
import time
import requests
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_api_health():
    """Check if the API is running and healthy."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"❌ API health check failed: {e}")
        return False

def wait_for_api():
    """Wait for the API to become available."""
    print("🔍 Checking API availability...")
    
    for attempt in range(30):  # Wait up to 30 seconds
        if check_api_health():
            print("✅ API is available")
            return True
        
        print(f"   ⏳ Attempt {attempt + 1}/30 - API not ready yet...")
        time.sleep(1)
    
    print("❌ API not available after 30 seconds")
    return False

def run_e2e_test():
    """Run the E2E test for message persistence."""
    print("🧪 Running E2E Message Persistence Test")
    print("=" * 60)
    
    # Check if API is running
    if not wait_for_api():
        print("❌ Cannot run E2E test - API is not available")
        print("💡 Please start the server with: source venv/bin/activate && uvicorn crewai_app.main:app --reload --host 0.0.0.0 --port 8000")
        return False
    
    # Change to project root directory
    os.chdir(project_root)
    
    # Run the E2E test
    cmd = [
        "python", "-m", "pytest", 
        "tests/test_e2e_message_persistence.py",
        "-v",
        "-s",  # Don't capture output so we can see real-time progress
        "--tb=short",
        "--color=yes"
    ]
    
    try:
        print("🚀 Starting E2E test execution...")
        result = subprocess.run(cmd, cwd=project_root)
        
        if result.returncode == 0:
            print("\n✅ E2E test completed successfully!")
            print("🎉 Message persistence is working correctly with real LLM calls!")
        else:
            print("\n❌ E2E test failed!")
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running E2E test: {e}")
        return False

def run_specific_test(test_name):
    """Run a specific E2E test."""
    print(f"🧪 Running specific E2E test: {test_name}")
    print("=" * 60)
    
    if not wait_for_api():
        print("❌ Cannot run E2E test - API is not available")
        return False
    
    os.chdir(project_root)
    
    cmd = [
        "python", "-m", "pytest", 
        f"tests/test_e2e_message_persistence.py::{test_name}",
        "-v",
        "-s",
        "--tb=short",
        "--color=yes"
    ]
    
    try:
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running specific test: {e}")
        return False

def main():
    """Main function."""
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        success = run_specific_test(test_name)
    else:
        # Run all E2E tests
        success = run_e2e_test()
    
    if success:
        print("\n🎉 All E2E tests passed! Message persistence is working correctly.")
    else:
        print("\n❌ Some E2E tests failed. Check the output above for details.")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
