#!/bin/bash

# Production Setup Script for AI Team
# This script sets up the production environment with real Jira integration

echo "🚀 Setting up AI Team for Production..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.production.template .env
    echo "⚠️  Please edit .env file with your actual credentials before running the application"
    echo "   Required: NEGISHI_JIRA_API_TOKEN, NEGISHI_JIRA_EMAIL, NEGISHI_JIRA_BASE_URL"
    exit 1
fi

# Check if required environment variables are set
echo "🔍 Checking environment configuration..."

if [ -z "$NEGISHI_JIRA_API_TOKEN" ]; then
    echo "❌ NEGISHI_JIRA_API_TOKEN is not set"
    echo "   Please set your Jira API token in the .env file"
    exit 1
fi

if [ -z "$NEGISHI_JIRA_EMAIL" ]; then
    echo "❌ NEGISHI_JIRA_EMAIL is not set"
    echo "   Please set your Jira email in the .env file"
    exit 1
fi

if [ -z "$NEGISHI_JIRA_BASE_URL" ]; then
    echo "❌ NEGISHI_JIRA_BASE_URL is not set"
    echo "   Please set your Jira base URL in the .env file"
    exit 1
fi

echo "✅ Environment configuration looks good!"

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Initialize database
echo "🗄️  Initializing database..."
python -c "from crewai_app.database import init_database; init_database()"

# Test Jira connection
echo "🔗 Testing Jira connection..."
python -c "
from crewai_app.services.jira_service import JiraService
import os
jira_service = JiraService(use_real=True)
# Test with a known story ID
test_story = jira_service.get_story('NEGISHI-178')
if test_story:
    print('✅ Jira connection successful!')
    print(f'   Found story: {test_story.get(\"key\", \"Unknown\")}')
else:
    print('❌ Jira connection failed!')
    print('   Please check your credentials and network connection')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "🎉 Production setup complete!"
    echo ""
    echo "To start the application:"
    echo "  Backend:  python -m uvicorn crewai_app.main:app --host 0.0.0.0 --port 8000 --reload"
    echo "  Frontend: cd frontend && npm start"
    echo ""
    echo "The AI Team is now ready for production use with real Jira integration!"
else
    echo "❌ Setup failed. Please check your Jira credentials and try again."
    exit 1
fi
