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
- **Cloud Provider Abstraction**: Platform-agnostic cloud provider support (Azure/AWS)
- **Conversation Persistence**: Message-level tracking with governance
- **Real-time Streaming**: Server-Sent Events for live updates
- **Token Governance**: Context window management and prompt shrinking

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
├── providers/          # Cloud provider abstraction layer
│   ├── __init__.py     # Providers package
│   └── cloud_providers.py # Cloud provider abstraction layer
├── workflows/          # Workflow orchestration logic
│   ├── story_implementation_workflow.py
│   └── enhanced_story_workflow.py
├── services/           # External service integrations
│   ├── jira_service.py        # Jira API integration
│   ├── github_service.py      # GitHub API integration
│   ├── openai_service.py      # Azure OpenAI integration with token governance
│   ├── conversation_service.py # Conversation persistence and message tracking
│   ├── llm_tracking_service.py # LLM call tracking and cost management
│   ├── event_stream.py        # Real-time event streaming
│   └── cloud_provider_service.py # Cloud provider service layer
├── models/             # Database models and schemas
│   ├── workflow.py     # Workflow database model
│   ├── conversation.py # Conversation database model
│   ├── code_file.py    # Code file database model
│   └── message.py      # Message-level persistence model
├── tests/              # Test suites
│   └── test_cloud_providers.py # Cloud provider unit tests
└── utils/              # Utility functions
    ├── logger.py       # Logging configuration
    ├── logging_sse.py  # Logging and SSE parity helper
    └── helpers.py      # Helper functions
```

## API Endpoints

### Workflow Management
- `GET /workflows` - List all workflows
- `GET /workflows/{id}` - Get specific workflow with conversations and code files
- `POST /workflows` - Create new workflow
  - Idempotent: returns 200 and existing workflow if `jira_story_id` already exists
- `DELETE /workflows/{id}` - Delete workflow
- `POST /workflows/{id}/execute` - Execute workflow with AI agents (int-only)
- `POST /workflows/from-jira/{story_id}` - Create workflow from Jira story
    - On success: `{ "message": "Workflow created successfully for {story_id}", "workflow_id": <id> }`
    - On duplicate: same success message with existing `workflow_id`
    - On error: `{ "message": "Could not retrieve story {story_id} from Jira" }` with 404/500
- `GET /workflows/{id}/compare?with=<id2>` - Compare two workflow runs and return aggregate metrics

### Execution Management
- `GET /workflows/{id}/executions` - List all executions for a workflow
- `GET /workflows/{id}/executions/{execution_id}` - Get specific execution details
- `POST /workflows/{id}/executions/start` - Start a new execution for a workflow
- `GET /workflows/{id}/executions/{exec_a}/compare/{exec_b}` - Compare two executions

Note: Legacy string-id endpoints have been removed. Only integer workflow IDs are supported.

### Workflow Execution
- **Enhanced Conversations**: Each conversation includes detailed prompts and agent instructions
- **Code Files**: Generated code files are linked to specific conversations
- **Agent Collaboration**: Multi-agent workflow with Product Manager, Architect, Developer, Tester, and Reviewer
- **Real-time Updates**: Workflow status updates as agents complete their tasks

### LLM Calls
- `GET /conversations/{conversation_id}/llm-calls` - Get tracked LLM calls for a conversation
  - Query params: `page`, `page_size`, `sort_by` (timestamp|model|total_tokens|response_time_ms|cost|id), `sort_dir` (asc|desc), `model`, `q`, `date_from`, `date_to`
  - Returns: `{ conversation_id, total_tokens_used, total_cost, page, page_size, total, calls: [...] }`

### Real-time Streaming
- `GET /events/workflows/{workflow_id}` - Server-Sent Events for workflow status
- `GET /events/workflows/{workflow_id}/stream` - Real-time conversation and LLM call events
- `WebSocket /ws/workflows/{workflow_id}` - WebSocket for live updates

### Health & Status
- `GET /health` - Health check endpoint
- `GET /docs` - API documentation (Swagger UI)

### PR, Checks, Diffs, Artifacts
- `GET /workflows/{workflow_id}/pr` – Pull Request summary
- `GET /workflows/{workflow_id}/pr/checks` – PR checks (paginated)
- `GET /workflows/{workflow_id}/diffs` – Diffs for workflow (paginated, optional `path` filter)
- `GET /workflows/{workflow_id}/artifacts` – Artifacts (paginated, optional `kind` filter)
- `POST /workflows/{workflow_id}/pr/refresh` – Enqueue background refresh of PR & checks
- `POST /workflows/{workflow_id}/diffs/refresh` – Enqueue background refresh of diffs
- `POST /workflows/{workflow_id}/artifacts/refresh` – Enqueue background refresh of artifacts

### Webhooks
- `POST /webhooks/github` – GitHub webhook ingestion (pull_request, check_run/check_suite) with HMAC signature verification

## Advanced Features

### Cloud Provider Abstraction
Platform-agnostic cloud provider support enabling seamless switching between Azure and AWS:

- **Abstract Base Class**: `CloudProvider` with standardized interface
- **Azure Provider**: `AzureProvider` for Azure OpenAI, Cognitive Search, SQL Database, Service Bus, and Blob Storage
- **AWS Provider**: `AWSProvider` for Amazon Bedrock, OpenSearch, RDS, SQS, and S3
- **Provider Detection**: Automatic detection based on configuration
- **Service Layer**: `CloudProviderService` for clean interface management
- **Error Handling**: Provider-specific error classes and validation
- **Configuration-Driven**: Environment-based provider selection

#### Usage Example
```python
from crewai_app.services.cloud_provider_service import CloudProviderService

# Azure configuration
azure_config = {
    "subscription_id": "your-subscription-id",
    "resource_group": "your-resource-group",
    "openai_resource_name": "your-openai-resource",
    "search_service_name": "your-search-service",
    "sql_server_name": "your-sql-server",
    "service_bus_namespace": "your-service-bus",
    "storage_account": "your-storage-account",
    "credentials": {"client_id": "your-client-id"}
}

# AWS configuration
aws_config = {
    "region": "us-east-1",
    "credentials": {"aws_access_key_id": "your-access-key"}
}

# Create service (automatically detects provider)
service = CloudProviderService(azure_config)  # or aws_config
llm_endpoint = service.get_llm_endpoint()
storage_endpoint = service.get_storage_endpoint()
```

### Conversation Persistence
The system now provides comprehensive conversation tracking with message-level persistence:

- **Message Model**: Each user/agent/tool message is stored with role, content, artifacts, and metadata
- **LLM Call Tracking**: Detailed tracking of model usage, tokens, costs, and governance decisions
- **Artifact Linking**: Messages can reference external artifacts with type, ID, URI, and checksum
- **Conversation Service**: Centralized service for managing conversations, messages, and LLM calls

### Token Governance
Advanced token management to prevent context overflow and ensure efficient usage:

- **Context Window Management**: Model-aware context window with safety buffers
- **Prompt Shrinking**: Automatic prompt reduction when context limits are exceeded
- **Budget Enforcement**: Per-step and per-agent token budgets with escalation
- **Loop Prevention**: Maximum shrink attempts to prevent infinite retry loops
- **Governance Logging**: Detailed logging of token decisions with SSE parity

### Real-time Streaming
Live updates for workflow execution and agent conversations:

- **Server-Sent Events**: Real-time workflow status and conversation updates
- **WebSocket Support**: Bidirectional communication for interactive workflows
- **Event Types**: Workflow, conversation, LLM call, escalation, collaboration, and error events
- **Logging Parity**: All significant events logged to both file and SSE streams

### Failure and Resume Semantics
Robust error handling with resumable execution:

- **Terminal Messages**: Clear error messages with token math and resume hints
- **Checkpoint System**: Resumable state with running summaries and artifact indices
- **Budget Tracking**: Remaining token budgets for each step and agent
- **Escalation Handling**: Structured escalation and collaboration tracking

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
- `llm_calls` - JSON array of LLM call data
- `total_tokens_used` - Aggregated token usage
- `total_cost` - Aggregated cost

### Message
- `id` - Primary key
- `conversation_id` - Foreign key to conversation
- `role` - Message role (system, user, assistant, tool)
- `content` - Message content (concise, large blobs summarized)
- `artifacts` - JSON array of artifact references
- `message_metadata` - JSON object with agent, step, timestamp info
- `created_at` - Message timestamp

### LLMCall
- `id` - Primary key
- `conversation_id` - Foreign key to conversation
- `model` - Model name (e.g., "gpt-4")
- `prompt_tokens` - Actual prompt tokens used
- `completion_tokens` - Actual completion tokens used
- `total_tokens` - Total tokens used
- `max_tokens` - Maximum tokens requested
- `total_tokens_requested` - Total tokens requested (prompt + max)
- `response_time_ms` - Response latency in milliseconds
- `status` - Call status (success, failed, truncated, skipped)
- `error_code` - Error code if failed
- `truncated_sections` - JSON array of truncated parts
- `prompt_hash` - SHA256 hash of prompt for deduplication
- `response_hash` - SHA256 hash of response for deduplication
- `budget_snapshot` - JSON object with remaining budgets
- `cost` - Calculated cost
- `timestamp` - Call timestamp
- `request_data` - Full request data for debugging
- `response_data` - Full response data for debugging

### CodeFile
- `id` - Primary key
- `conversation_id` - Foreign key to conversation
- `filename` - File name
- `content` - File content
- `file_type` - File type (python, typescript, etc.)

### Execution
- `id` - Primary key
- `workflow_id` - Foreign key to workflow
- `status` - Execution status (pending, running, completed, failed)
- `started_at` - Execution start timestamp
- `finished_at` - Execution completion timestamp
- `total_calls` - Total number of LLM calls
- `total_tokens` - Total tokens consumed
- `total_cost` - Total cost in dollars
- `avg_latency_ms` - Average response latency in milliseconds
- `models` - List of models used in execution
- `meta` - Additional metadata (prompt hashes, config flags, etc.)

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
USE_REAL_GITHUB=true
GITHUB_WEBHOOK_SECRET=your_webhook_secret

# Azure OpenAI
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=your-deployment

# Cloud Provider Configuration (Azure)
CLOUD_PROVIDER=azure
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_RESOURCE_GROUP=your-resource-group
AZURE_OPENAI_RESOURCE_NAME=your-openai-resource
AZURE_SEARCH_SERVICE_NAME=your-search-service
AZURE_SQL_SERVER_NAME=your-sql-server
AZURE_SERVICE_BUS_NAMESPACE=your-service-bus
AZURE_STORAGE_ACCOUNT=your-storage-account
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret

# Cloud Provider Configuration (AWS)
# CLOUD_PROVIDER=aws
# AWS_REGION=us-east-1
# AWS_ACCESS_KEY_ID=your-access-key
# AWS_SECRET_ACCESS_KEY=your-secret-key
# AWS_OPENSEARCH_DOMAIN=your-opensearch-domain

# Feature Flags
AI_TEAM_REDACT_SENSITIVE=1

# Heartbeat
HEARTBEAT_INTERVAL_SECONDS=15
HEARTBEAT_TIMEOUT_SECONDS=120
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

# Run cloud provider tests specifically
pytest crewai_app/tests/test_cloud_providers.py -v

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
