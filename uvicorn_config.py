"""
Uvicorn configuration to exclude repos directory from file watching
"""
import uvicorn
from uvicorn.config import LOGGING_CONFIG

# Custom logging config that excludes repos directory
LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

def run_server():
    """Run uvicorn server with proper file watching exclusions"""
    uvicorn.run(
        "crewai_app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_excludes=[
            "repos/*",
            "repos/**/*",
            "*.log",
            "*.db",
            "*.db-journal",
            "venv/*",
            "venv/**/*",
            "__pycache__/*",
            "__pycache__/**/*",
            "*.pyc",
            "*.pyo",
            "node_modules/*",
            "node_modules/**/*",
            ".git/*",
            ".git/**/*",
            "backend.log",
            "ai_team.db*",
            "*.json",
            "*.cache",
            "*.tmp"
        ],
        log_level="info"
    )

if __name__ == "__main__":
    run_server()
