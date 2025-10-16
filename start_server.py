#!/usr/bin/env python3
"""
Start the AI Team server with proper file watching exclusions
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    """Start the server with exclusions for repos directory"""
    
    # Ensure we're in the right directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Set environment variables
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    
    # Start uvicorn with exclusions
    cmd = [
        sys.executable, "-m", "uvicorn",
        "crewai_app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload",
        "--reload-exclude", "repos/*",
        "--reload-exclude", "repos/**/*",
        "--reload-exclude", "*.log",
        "--reload-exclude", "*.db*",
        "--reload-exclude", "venv/*",
        "--reload-exclude", "__pycache__/*",
        "--reload-exclude", "node_modules/*",
        "--reload-exclude", ".git/*",
        "--reload-exclude", "backend.log",
        "--reload-exclude", "ai_team.db*",
        "--reload-exclude", "*.json",
        "--reload-exclude", "*.cache",
        "--reload-exclude", "*.tmp"
    ]
    
    print("🚀 Starting AI Team server with proper file exclusions...")
    print("📁 Excluding repos/ directory from file watching")
    print("=" * 60)
    
    try:
        subprocess.run(cmd, env=env, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
