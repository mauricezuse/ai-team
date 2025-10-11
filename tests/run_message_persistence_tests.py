#!/usr/bin/env python3
"""
Test runner for agent message persistence tests.
"""
import sys
import os
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_tests():
    """Run the message persistence tests."""
    print("🧪 Running Agent Message Persistence Tests")
    print("=" * 50)
    
    # Change to project root directory
    os.chdir(project_root)
    
    # Run pytest with verbose output
    cmd = [
        "python", "-m", "pytest", 
        "tests/test_agent_message_persistence.py",
        "-v",
        "--tb=short",
        "--color=yes"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print(f"Exit code: {result.returncode}")
        
        if result.returncode == 0:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed!")
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def run_specific_test(test_name):
    """Run a specific test by name."""
    print(f"🧪 Running specific test: {test_name}")
    print("=" * 50)
    
    os.chdir(project_root)
    
    cmd = [
        "python", "-m", "pytest", 
        f"tests/test_agent_message_persistence.py::{test_name}",
        "-v",
        "--tb=short",
        "--color=yes"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        success = run_specific_test(test_name)
    else:
        # Run all tests
        success = run_tests()
    
    sys.exit(0 if success else 1)
