#!/bin/bash

# AI Team Server Startup Script
# This script starts the AI Team server with proper file exclusions
# to prevent unnecessary restarts when AI agents modify target project files

echo "🚀 Starting AI Team Server..."
echo "📁 Excluding repos/ directory from file watching"
echo "=" * 50

# Activate virtual environment
source venv/bin/activate

# Start uvicorn with exclusions
uvicorn crewai_app.main:app \
    --reload \
    --host 0.0.0.0 \
    --port 8000 \
    --reload-exclude "repos/*" \
    --reload-exclude "repos/**/*" \
    --reload-exclude "*.log" \
    --reload-exclude "*.db*" \
    --reload-exclude "venv/*" \
    --reload-exclude "__pycache__/*" \
    --reload-exclude "node_modules/*" \
    --reload-exclude ".git/*" \
    --reload-exclude "backend.log" \
    --reload-exclude "ai_team.db*" \
    --reload-exclude "*.json" \
    --reload-exclude "*.cache" \
    --reload-exclude "*.tmp"
