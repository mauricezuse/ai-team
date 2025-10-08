# AI Team: Technical User Manual

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Installation & Setup](#installation--setup)
4. [Core Components](#core-components)
5. [API Reference](#api-reference)
6. [Database Schema](#database-schema)
7. [AI Agents](#ai-agents)
8. [Workflow Execution](#workflow-execution)
9. [Frontend Components](#frontend-components)
10. [Configuration](#configuration)
11. [Testing](#testing)
12. [Troubleshooting](#troubleshooting)
13. [Development Guidelines](#development-guidelines)

## System Overview

The AI Team is a modular, production-ready orchestration platform for an AI-powered agent team (CrewAI) that generates, reviews, and tests code for web applications. It features a FastAPI backend with SQLite database, Angular frontend, and comprehensive AI agent workflows.

### Key Features
- **Modular AI Agents**: Product Manager, Architect, Developer, Frontend, Tester, Reviewer
- **Database-Driven Workflows**: SQLite database with full CRUD operations
- **Jira Integration**: Automatic story retrieval and workflow creation
- **Repository Integration**: Clones and works with external repositories (negishi-freelancing)
- **Real-time Collaboration**: Agent escalation and collaboration tracking
- **Comprehensive Testing**: Playwright E2E tests and Python unit tests
- **Modern UI**: Angular with PrimeNG components

## Architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (Angular)     │◄──►│   (FastAPI)     │◄──►│   (SQLite)      │
│   Port: 4200    │    │   Port: 8000    │    │   ai_team.db    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PrimeNG UI    │    │   AI Agents     │    │   Workflow      │
│   Components    │    │   (CrewAI)      │    │   Results       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Technology Stack
- **Backend**: FastAPI, SQLAlchemy, CrewAI, Azure OpenAI
- **Frontend**: Angular 17, PrimeNG, TypeScript, SCSS
- **Database**: SQLite with SQLAlchemy ORM
- **AI/ML**: Azure OpenAI GPT-4, CrewAI orchestration
- **Testing**: Playwright, Pytest, Angular Testing Utilities
- **DevOps**: Docker, GitHub Actions (planned)

## Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js 18+
- npm 9+
- Git

### Backend Setup
```bash
# Clone repository
git clone <repository-url>
cd ai-team

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your Azure OpenAI credentials

# Initialize database
python3 -c "from crewai_app.database import init_database; init_database()"

# Start backend server
python3 -m uvicorn crewai_app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

### Environment Variables
```bash
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=your_deployment_name

# Multi-model deployments (optional)
AZURE_OPENAI_DEPLOYMENT_PM=pm-deployment
AZURE_OPENAI_DEPLOYMENT_ARCHITECT=architect-deployment
AZURE_OPENAI_DEPLOYMENT_DEVELOPER=developer-deployment
AZURE_OPENAI_DEPLOYMENT_FRONTEND=frontend-deployment

# External Services
USE_REAL_JIRA=false
USE_REAL_GITHUB=false
PROJECT_KEY=NEGISHI
```

## Core Components

### Backend (FastAPI)
- **Main Application**: `crewai_app/main.py`
- **Database Models**: `crewai_app/database.py`
- **AI Agents**: `crewai_app/agents/`
- **Workflows**: `crewai_app/workflows/`
- **Services**: `crewai_app/services/`

### Frontend (Angular)
- **Main App**: `frontend/src/app/`
- **Features**: Dashboard, Agents, Workflows
- **Services**: API communication services
- **Components**: Reusable UI components

### Database (SQLite)
- **Workflows**: Workflow definitions and status
- **Conversations**: Agent conversation logs
- **Code Files**: Generated code file tracking
- **Escalations**: Agent escalation tracking
- **Collaborations**: Agent collaboration records

## API Reference

### Core Endpoints

#### Health Check
```http
GET /health
```
Returns system health status.

#### Workflows
```http
GET /workflows
```
Returns all workflows from database.

```http
GET /workflows/{workflow_id}
```
Returns specific workflow with conversations and code files.

```http
POST /workflows
```
Creates a new workflow manually.

```http
POST /workflows/{workflow_id}/execute
```
Executes a workflow using AI agents.

```http
POST /workflows/from-jira/{story_id}
```
Creates workflow from Jira story.

#### Agents
```http
GET /agents
```
Returns all available AI agents.

```http
GET /agents/{agent_id}
```
Returns specific agent details.

### Request/Response Models

#### WorkflowCreate
```json
{
  "jira_story_id": "NEGISHI-178",
  "jira_story_title": "Implement federation-aware agents",
  "jira_story_description": "Create a system where AI agents can work together...",
  "repository_url": "https://github.com/mauricezuse/negishi-freelancing",
  "target_branch": "main"
}
```

#### WorkflowResponse
```json
{
  "id": 1,
  "name": "NEGISHI-178: Federation-aware agents",
  "jira_story_id": "NEGISHI-178",
  "jira_story_title": "Implement federation-aware agents",
  "jira_story_description": "Create a system where AI agents can work together...",
  "status": "completed",
  "created_at": "2025-10-02T21:21:21.064373",
  "updated_at": "2025-10-02T21:21:21.064377",
  "repository_url": "https://github.com/mauricezuse/negishi-freelancing",
  "target_branch": "main",
  "conversations": [],
  "code_files": []
}
```

## Database Schema

### Tables

#### Workflows
```sql
CREATE TABLE workflows (
    id INTEGER PRIMARY KEY,
    name VARCHAR,
    jira_story_id VARCHAR UNIQUE,
    jira_story_title VARCHAR,
    jira_story_description TEXT,
    status VARCHAR DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    repository_url VARCHAR,
    target_branch VARCHAR DEFAULT 'main'
);
```

#### Conversations
```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY,
    workflow_id INTEGER REFERENCES workflows(id),
    step VARCHAR,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    agent VARCHAR,
    status VARCHAR DEFAULT 'pending',
    details TEXT,
    output TEXT,
    prompt TEXT
);
```

#### Code Files
```sql
CREATE TABLE code_files (
    id INTEGER PRIMARY KEY,
    workflow_id INTEGER REFERENCES workflows(id),
    conversation_id INTEGER REFERENCES conversations(id),
    filename VARCHAR,
    file_path VARCHAR,
    file_content TEXT,
    file_type VARCHAR,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### Escalations
```sql
CREATE TABLE escalations (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id),
    from_agent VARCHAR,
    to_agent VARCHAR,
    reason TEXT,
    status VARCHAR DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### Collaborations
```sql
CREATE TABLE collaborations (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id),
    from_agent VARCHAR,
    to_agent VARCHAR,
    request_type VARCHAR,
    status VARCHAR DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## AI Agents

### Agent Architecture

All agents inherit from `BaseAgent` which provides:
- LLM interaction with retry logic
- Output parsing and validation
- Error handling and escalation
- Collaboration and context management
- Caching and logging

### Available Agents

#### 1. Product Manager (PM)
- **Role**: Requirements analysis and user story creation
- **Capabilities**: Story analysis, acceptance criteria generation
- **Tools**: PMTool for story review and analysis
- **Deployment**: `deployment_pm`

#### 2. System Architect
- **Role**: System design and architecture
- **Capabilities**: API design, data models, component structure
- **Tools**: ArchitectTool for design generation
- **Deployment**: `deployment_architect`

#### 3. Backend Developer
- **Role**: Backend implementation and APIs
- **Capabilities**: Python/FastAPI code generation, backend testing
- **Tools**: CodeGeneratorTool for implementation
- **Deployment**: `deployment_developer`

#### 4. Frontend Developer
- **Role**: Frontend implementation and UI
- **Capabilities**: Angular development, UI/UX implementation
- **Specialization**: Angular Native Federation micro-frontend architecture
- **Deployment**: `deployment_frontend`

#### 5. QA Tester
- **Role**: Testing and quality assurance
- **Capabilities**: Test case generation, quality validation
- **Tools**: TesterTool for test creation
- **Deployment**: `deployment_tester`

#### 6. Code Reviewer
- **Role**: Code review and quality standards
- **Capabilities**: Code review, quality assessment
- **Tools**: ReviewerTool for code analysis
- **Deployment**: `deployment_reviewer`

### Agent Collaboration

Agents can:
- **Escalate** tasks to other agents when requirements are unclear
- **Collaborate** on complex tasks requiring multiple perspectives
- **Share context** through the shared context system
- **Track interactions** through escalation and collaboration logs

## Workflow Execution

### Workflow Types

#### 1. Enhanced Story Workflow
- **File**: `crewai_app/workflows/enhanced_story_workflow.py`
- **Purpose**: Complete story implementation with AI agents
- **Features**: Collaboration, escalation, error recovery
- **Checkpointing**: Automatic save/restore functionality

#### 2. Story Implementation Workflow
- **File**: `crewai_app/workflows/story_implementation_workflow.py`
- **Purpose**: Basic story implementation
- **Features**: Codebase indexing, semantic search
- **Focus**: Backend and frontend implementation

#### 3. Planning Workflow
- **File**: `crewai_app/workflows/planning_workflow.py`
- **Purpose**: Architecture planning and design
- **Features**: Product vision analysis, component design

### Workflow Execution Process

1. **Story Retrieval**: Get Jira story details
2. **Codebase Indexing**: Analyze existing codebase
3. **Implementation Planning**: Generate implementation plan
4. **Task Breakdown**: Break down into agent-specific tasks
5. **Agent Execution**: Execute tasks with collaboration
6. **Code Generation**: Generate and save code files
7. **Testing**: Run tests and validation
8. **Review**: Final review and quality check

### Checkpoint System

Workflows support checkpointing for:
- **Resume functionality**: Continue from last successful step
- **Error recovery**: Handle failures gracefully
- **Progress tracking**: Monitor workflow execution
- **Data persistence**: Save conversation logs and code files

## Frontend Components

### Application Structure

```
frontend/src/app/
├── app.component.ts          # Root component
├── app.routes.ts            # Routing configuration
├── layout/                  # Main layout
│   ├── layout.component.ts
│   └── layout.component.html
├── features/                # Feature modules
│   ├── dashboard/           # Dashboard feature
│   ├── agents/              # Agents management
│   └── workflows/           # Workflows management
└── core/                    # Core services
    └── services/            # API services
```

### Key Components

#### Dashboard Component
- **Purpose**: System overview and statistics
- **Features**: Agent count, workflow count, system status
- **Location**: `features/dashboard/dashboard.component.ts`

#### Workflows List Component
- **Purpose**: Display and manage workflows
- **Features**: Search, filter, pagination, CRUD operations
- **Location**: `features/workflows/workflows-list.component.ts`

#### Workflow Detail Component
- **Purpose**: Detailed workflow view
- **Features**: Conversation display, code file links, execution controls
- **Location**: `features/workflows/workflow-detail.component.ts`

#### Create Workflow Component
- **Purpose**: Manual workflow creation
- **Features**: Form validation, Jira integration
- **Location**: `features/workflows/create-workflow.component.ts`

### UI Framework

#### PrimeNG Components
- **Table**: Data display and management
- **Button**: Action buttons with icons
- **Dialog**: Modal dialogs and forms
- **Toast**: User notifications
- **Input**: Form controls
- **Dropdown**: Selection controls

#### Styling
- **SCSS**: Component-specific styles
- **PrimeNG Themes**: Consistent UI components
- **Responsive Design**: Mobile-friendly layouts
- **Custom Variables**: Design system consistency

## Configuration

### Backend Configuration

#### Settings Class
```python
class Settings(BaseSettings):
    azure_openai_api_key: Optional[str]
    azure_openai_endpoint: Optional[str]
    azure_openai_deployment: Optional[str]
    deployment_pm: Optional[str]
    deployment_architect: Optional[str]
    deployment_developer: Optional[str]
    deployment_frontend: Optional[str]
    project_key: Optional[str] = "NEGISHI"
    use_real_github: bool = False
    use_real_jira: bool = False
```

#### Database Configuration
```python
SQLALCHEMY_DATABASE_URL = "sqlite:///./ai_team.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
```

### Frontend Configuration

#### Angular Configuration
```json
{
  "projects": {
    "frontend": {
      "architect": {
        "build": {
          "options": {
            "styles": [
              "node_modules/primeicons/primeicons.css",
              "node_modules/primeflex/primeflex.css",
              "src/styles.scss"
            ]
          }
        }
      }
    }
  }
}
```

#### Proxy Configuration
```json
{
  "/api/workflows": {
    "target": "http://localhost:8000",
    "secure": true,
    "changeOrigin": true,
    "pathRewrite": {
      "^/api": ""
    }
  }
}
```

## Testing

### Test Structure

```
tests/
├── playwright/              # E2E tests
│   ├── test_workflow_creation.spec.ts
│   ├── test_workflow_execution.spec.ts
│   ├── test_database_workflows.spec.ts
│   ├── test_jira_integration.spec.ts
│   ├── test_database_integration.spec.ts
│   └── test_comprehensive_database.spec.ts
├── test_agent_collaboration.py
├── test_api_endpoints.py
├── test_workflow_data_parsing.py
└── test_workflow_integration.py
```

### Test Categories

#### 1. Playwright E2E Tests
- **Workflow Creation**: Manual and Jira-based creation
- **Workflow Execution**: AI agent execution and database storage
- **Database Integration**: CRUD operations and error handling
- **Jira Integration**: Story retrieval and workflow creation
- **UI Testing**: Component interaction and user flows

#### 2. Python Unit Tests
- **API Endpoints**: Backend API functionality
- **Agent Collaboration**: Agent interaction and escalation
- **Workflow Integration**: End-to-end workflow testing
- **Data Parsing**: Workflow data processing

### Running Tests

#### Playwright Tests
```bash
# Run all E2E tests
npx playwright test

# Run specific test file
npx playwright test tests/playwright/test_workflow_creation.spec.ts

# Run with HTML report
npx playwright test --reporter=html
```

#### Python Tests
```bash
# Run all Python tests
python -m pytest

# Run specific test file
python -m pytest tests/test_api_endpoints.py

# Run with coverage
python -m pytest --cov=crewai_app
```

## Troubleshooting

### Common Issues

#### 1. Backend Server Issues
```bash
# Port already in use
ERROR: [Errno 48] Address already in use
# Solution: Kill existing process or use different port
lsof -ti:8000 | xargs kill -9
```

#### 2. Frontend Build Issues
```bash
# PrimeNG theme import errors
ERROR: Could not resolve "primeng/resources/themes/lara-light-blue/theme.css"
# Solution: Remove theme imports from styles.scss
```

#### 3. Database Issues
```bash
# Database not found
ls: ai_team.db: No such file or directory
# Solution: Initialize database
python3 -c "from crewai_app.database import init_database; init_database()"
```

#### 4. Jira Integration Issues
```bash
# Jira authentication failed
ERROR: Jira authentication failed. Please check your credentials.
# Solution: Verify Jira credentials and permissions
```

### Debug Commands

#### Backend Debugging
```bash
# Check backend health
curl http://localhost:8000/health

# Check database
sqlite3 ai_team.db ".tables"

# View logs
tail -f logs/ai_team.log
```

#### Frontend Debugging
```bash
# Check frontend
curl http://localhost:4200

# Check build
npm run build

# Check linting
npm run lint
```

### Performance Issues

#### Database Performance
- **Indexing**: Ensure proper database indexes
- **Connection Pooling**: Monitor database connections
- **Query Optimization**: Optimize slow queries

#### Frontend Performance
- **Bundle Size**: Monitor bundle size and lazy loading
- **Component Optimization**: Use OnPush change detection
- **Memory Leaks**: Monitor component lifecycle

## Development Guidelines

### Code Standards

#### Python
- **PEP 8**: Follow Python style guidelines
- **Type Hints**: Use type annotations
- **Docstrings**: Document all functions and classes
- **Error Handling**: Implement proper exception handling

#### TypeScript/Angular
- **ESLint**: Follow Angular style guide
- **TypeScript**: Use strict type checking
- **Components**: Use standalone components
- **Services**: Implement proper dependency injection

### Git Workflow

#### Branch Naming
- **Feature**: `feature/description`
- **Bugfix**: `bugfix/description`
- **Hotfix**: `hotfix/description`

#### Commit Messages
- **Format**: `MINIONS-1: Description of changes`
- **Scope**: Include component or feature name
- **Description**: Clear, concise description

### Testing Guidelines

#### Test Coverage
- **Minimum**: 80% code coverage
- **Critical Paths**: 100% coverage for critical functionality
- **Edge Cases**: Test error conditions and edge cases

#### Test Data
- **Mock Data**: Use realistic test data
- **Isolation**: Tests should be independent
- **Cleanup**: Clean up test data after tests

### Documentation

#### Code Documentation
- **Functions**: Document all public functions
- **Classes**: Document class purpose and usage
- **API**: Document all API endpoints
- **Examples**: Include usage examples

#### User Documentation
- **Setup**: Clear installation instructions
- **Usage**: Step-by-step usage guides
- **Troubleshooting**: Common issues and solutions
- **API Reference**: Complete API documentation

---

## Conclusion

This technical manual provides comprehensive documentation for the AI Team platform. For additional support or questions, please refer to the codebase or contact the development team.

**Last Updated**: 2025-01-02
**Version**: 1.0.0
**Maintainer**: AI Team Development Team
