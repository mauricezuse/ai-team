# AI Team Production Setup Guide

This guide will help you set up the AI Team system for production use with real Jira integration.

## Prerequisites

Before setting up the production environment, ensure you have:

1. **Jira Access**: A Jira instance with API access
2. **Jira API Token**: Generate an API token from your Jira account
3. **OpenAI API Key**: For AI agent functionality
4. **GitHub Token**: For repository operations (optional but recommended)

## Quick Setup

1. **Clone and navigate to the project**:
   ```bash
   cd /Users/mauricevandermerwe/Projects/Negishi/ai-team
   ```

2. **Run the production setup script**:
   ```bash
   ./setup_production.sh
   ```

3. **Configure your credentials**:
   - Edit the `.env` file with your actual credentials
   - Set `NEGISHI_JIRA_API_TOKEN`, `NEGISHI_JIRA_EMAIL`, `NEGISHI_JIRA_BASE_URL`

## Manual Setup

If you prefer to set up manually:

### 1. Environment Configuration

Create a `.env` file with the following variables:

```bash
# Jira Configuration (Required)
NEGISHI_JIRA_API_TOKEN=your_jira_api_token_here
NEGISHI_JIRA_EMAIL=your_email@company.com
NEGISHI_JIRA_BASE_URL=https://your-domain.atlassian.net

# OpenAI Configuration (Required for AI agents)
OPENAI_API_KEY=your_openai_api_key_here

# GitHub Configuration (Optional but recommended)
GITHUB_TOKEN=your_github_token_here

# Database Configuration
DATABASE_URL=sqlite:///./ai_team.db

# Application Configuration
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

### 2. Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt

# Frontend dependencies
cd frontend
npm install
cd ..
```

### 3. Initialize Database

```bash
python -c "from crewai_app.database import init_database; init_database()"
```

### 4. Test Jira Connection

```bash
python -c "
from crewai_app.services.jira_service import JiraService
jira_service = JiraService(use_real=True)
test_story = jira_service.get_story('NEGISHI-178')
if test_story:
    print('✅ Jira connection successful!')
else:
    print('❌ Jira connection failed!')
"
```

## Running the Application

### Start the Backend

```bash
python -m uvicorn crewai_app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Start the Frontend

```bash
cd frontend
npm start
```

The application will be available at:
- Frontend: http://localhost:4200
- Backend API: http://localhost:8000

## Production Features

### Real Jira Integration

The production system now uses real Jira data instead of mock data:

- **Story Retrieval**: Fetches actual story details from your Jira instance
- **Authentication**: Uses your Jira API token for secure access
- **Error Handling**: Proper error messages for authentication and permission issues
- **Timeout Handling**: 30-second timeout for Jira API calls

### AI Agent Implementation

When you create a workflow from a Jira story, the AI Team will:

1. **Fetch the real story** from your Jira instance
2. **Analyze the requirements** using AI agents
3. **Generate implementation code** based on the story requirements
4. **Create files** in the target repository
5. **Track progress** in the database

### Database Persistence

All workflow data is stored in a SQLite database:

- **Workflows**: Story information and status
- **Conversations**: AI agent interactions and outputs
- **Code Files**: Generated files and their locations
- **Escalations**: Agent-to-agent communications
- **Collaborations**: Cross-agent coordination

## Troubleshooting

### Jira Connection Issues

If you get Jira connection errors:

1. **Check credentials**: Verify your API token, email, and base URL
2. **Test network**: Ensure you can reach your Jira instance
3. **Check permissions**: Verify your account has access to the stories
4. **Check story ID**: Ensure the story exists and is accessible

### Common Error Messages

- **"Jira integration not configured"**: Set the required environment variables
- **"Story not found"**: Check if the story ID exists and you have access
- **"Authentication failed"**: Verify your API token and email
- **"Access forbidden"**: Check your Jira permissions

### Testing the Integration

Test your setup with a real Jira story:

```bash
curl -X POST http://localhost:8000/workflows/from-jira/YOUR-STORY-ID \
  -H "Content-Type: application/json" \
  -d "{}"
```

## Security Considerations

1. **Environment Variables**: Never commit `.env` files to version control
2. **API Tokens**: Use strong, unique API tokens
3. **Network Security**: Use HTTPS for production Jira instances
4. **Access Control**: Limit Jira permissions to necessary stories only

## Monitoring and Logs

The system provides detailed logging:

- **Jira API calls**: All requests and responses are logged
- **Error tracking**: Detailed error messages for troubleshooting
- **Performance**: Request timing and status codes
- **Database operations**: Workflow creation and updates

## Support

If you encounter issues:

1. Check the logs for detailed error messages
2. Verify your Jira credentials and permissions
3. Test the Jira connection manually
4. Ensure all required environment variables are set

The AI Team is now ready for production use with real Jira integration!
