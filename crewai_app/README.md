# CrewAI App - Backend Core

## Overview
This is the main Python backend application that orchestrates AI agents using CrewAI framework. It provides FastAPI endpoints for workflow management, agent collaboration, and integration with external services.

## Architecture

### Core Components
- **FastAPI Application**: REST API server on port 8000
- **Database Layer**: SQLAlchemy ORM with SQLite database
- **AI Agents**: CrewAI agents for different roles
- **Workflow Engine**: Orchestrates multi-agent collaboration
- **Service Integrations**: Jira, GitHub, Azure OpenAI

### Key Files
- `main.py` - FastAPI app with all API endpoints
- `database.py` - Database models and connection management
- `config.py` - Application configuration and environment variables

## Directory Structure

```
crewai_app/
├── agents/              # AI agent role definitions
│   ├── pm.py           # Product Manager agent
│   ├── architect.py    # Solution Architect agent
│   ├── developer.py    # Backend Developer agent
│   ├── frontend.py     # Frontend Developer agent
│   ├── tester.py       # QA Tester agent
│   └── reviewer.py     # Code Reviewer agent
├── workflows/          # Workflow orchestration logic
│   ├── story_implementation_workflow.py
│   └── enhanced_story_workflow.py
├── services/           # External service integrations
│   ├── jira_service.py    # Jira API integration
│   ├── github_service.py  # GitHub API integration
│   └── openai_service.py  # Azure OpenAI integration
├── models/             # Database models and schemas
│   ├── workflow.py     # Workflow database model
│   ├── conversation.py # Conversation database model
│   └── code_file.py    # Code file database model
└── utils/              # Utility functions
    ├── logger.py       # Logging configuration
    └── helpers.py      # Helper functions
```

## API Endpoints

### Workflow Management
- `GET /workflows` - List all workflows
- `GET /workflows/{id}` - Get specific workflow with conversations and code files
- `POST /workflows` - Create new workflow
-   - Idempotent: returns 200 and existing workflow if `jira_story_id` already exists
- `DELETE /workflows/{id}` - Delete workflow
- `POST /workflows/{id}/execute` - Execute workflow with AI agents
- `POST /workflows/from-jira/{story_id}` - Create workflow from Jira story
    - On success: `{ "message": "Workflow created successfully for {story_id}", "workflow_id": <id> }`
    - On duplicate: same success message with existing `workflow_id`
    - On error: `{ "message": "Could not retrieve story {story_id} from Jira" }` with 404/500
- `GET /workflows/{id}/compare?with=<id2>` - Compare two workflow runs and return aggregate metrics

### Workflow Execution
- **Enhanced Conversations**: Each conversation includes detailed prompts and agent instructions
- **Code Files**: Generated code files are linked to specific conversations
- **Agent Collaboration**: Multi-agent workflow with Product Manager, Architect, Developer, Tester, and Reviewer
- **Real-time Updates**: Workflow status updates as agents complete their tasks

### LLM Calls
- `GET /conversations/{conversation_id}/llm-calls` - Get tracked LLM calls for a conversation
  - Query params: `page`, `page_size`, `sort_by` (timestamp|model|total_tokens|response_time_ms|cost|id), `sort_dir` (asc|desc), `model`, `q`, `date_from`, `date_to`
  - Returns: `{ conversation_id, total_tokens_used, total_cost, page, page_size, total, calls: [...] }`

### Health & Status
- `GET /health` - Health check endpoint
- `GET /docs` - API documentation (Swagger UI)

## Database Models

### Workflow
- `id` - Primary key
- `name` - Workflow name
- `jira_story_id` - Jira story identifier
- `status` - Workflow status (pending, running, completed, failed)
- `repository_url` - Target repository URL
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

### Conversation
- `id` - Primary key
- `workflow_id` - Foreign key to workflow
- `agent` - Agent role (pm, architect, developer, etc.)
- `step` - Workflow step name
- `prompt` - Agent prompt
- `output` - Agent response
- `details` - Additional conversation details
- `timestamp` - Conversation timestamp

### CodeFile
- `id` - Primary key
- `conversation_id` - Foreign key to conversation
- `filename` - File name
- `content` - File content
- `file_type` - File type (python, typescript, etc.)

## Environment Variables

```bash
# Database
DATABASE_URL=sqlite:///./ai_team.db

# Jira Integration
NEGISHI_JIRA_API_TOKEN=your_token
NEGISHI_JIRA_EMAIL=your_email
NEGISHI_JIRA_BASE_URL=https://your-domain.atlassian.net

# GitHub Integration
GITHUB_TOKEN=your_token
NEGISHI_GITHUB_REPO=org/repo

# Azure OpenAI
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=your-deployment

# Feature Flags
AI_TEAM_REDACT_SENSITIVE=1
```

## Development

### Running the Server
```bash
# Activate virtual environment
source venv/bin/activate

# Start FastAPI server
uvicorn crewai_app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Run unit tests
pytest tests/

# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/workflows
```

## AI Agent Workflow

1. **Story Retrieval**: Fetch Jira story details
2. **Analysis**: Product Manager analyzes requirements
3. **Architecture**: Solution Architect designs system
4. **Implementation**: Backend/Frontend developers write code
5. **Testing**: QA Tester creates tests
6. **Review**: Code Reviewer reviews and optimizes
7. **Integration**: Files committed to target repository

## Error Handling

- **API Errors**: Proper HTTP status codes and error messages
- **Database Errors**: Transaction rollback and error logging
- **External Service Errors**: Graceful degradation and retry logic
- **Agent Errors**: Workflow state management and error recovery

## Logging

- **Structured Logging**: JSON format with context
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Files**: Rotating logs with size limits
- **Context**: Request ID, user ID, workflow ID tracking

## Security

- **Input Validation**: Pydantic models for all inputs
- **SQL Injection**: SQLAlchemy ORM protection
- **API Security**: CORS configuration and rate limiting
- **Secrets Management**: Environment variables for sensitive data
