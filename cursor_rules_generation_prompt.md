# Prompt for Generating Comprehensive Cursor Rules

## Task
Create comprehensive cursor rules for an AI orchestration platform project that uses CrewAI for multi-agent collaboration. The rules should guide AI assistants in understanding the project structure, development workflows, testing requirements, and best practices.

## Project Context
This is a production-ready AI orchestration platform that:
- Uses CrewAI for multi-agent collaboration
- Manages workflows and integrates with Jira/GitHub
- Generates code for target projects
- Has a FastAPI backend (Python) on port 8000
- Has an Angular frontend on port 4001
- Uses SQLite with SQLAlchemy ORM
- Includes comprehensive Playwright E2E testing
- Integrates with Azure OpenAI for AI agents

## Required Cursor Rules Structure

### 1. Project Overview Section
- Brief description of the AI orchestration platform
- Core components and their purposes
- Technology stack overview
- Key architectural decisions

### 2. Directory Structure & File Organization
Create detailed rules for:
```
ai-team/
├── crewai_app/           # Main Python backend (FastAPI + CrewAI)
│   ├── agents/          # AI agent role definitions
│   ├── workflows/       # Workflow orchestration logic
│   ├── services/        # External service integrations
│   ├── models/          # Database models and schemas
│   └── utils/           # Utility functions and logging
├── frontend/             # Angular frontend (port 4001)
│   ├── src/app/features/ # Feature modules (workflows, agents, dashboard)
│   ├── src/app/shared/   # Shared components and services
│   └── src/assets/       # Static assets and styles
├── repos/               # Cloned target projects (git submodules)
│   └── {project-name}/  # Each project the AI team works on
├── tests/               # Comprehensive test suites
│   ├── playwright/      # E2E tests with Playwright
│   └── test_*.py        # Unit and integration tests
├── docs/                # Project documentation
│   ├── DEPLOYMENT.md    # Production deployment guide
│   ├── CI_CD.md         # CI/CD pipeline documentation
│   └── README.md        # Documentation overview
└── infra/               # Infrastructure as Code
    ├── bicep/           # Azure Bicep templates
    └── terraform/       # Terraform scripts
```

### 3. Development Guidelines
Include rules for:
- **Commit Message Standards**: 
  - AI Team project: Use `MINIONS-xxx:` prefix
  - Subprojects in /repos: Use `NEGISHI-xxx:` prefix
  - Format: `MINIONS-123: Brief description of changes`
- **Code Quality Standards**:
  - Python: Follow PEP 8, use type hints, docstrings
  - TypeScript/Angular: Use strict mode, proper interfaces
  - Testing: Write tests for all new features
  - Documentation: Update README/docs for significant changes

### 4. Technology Stack Rules
Create specific rules for:
- **Backend (Python)**: FastAPI with Pydantic models, SQLite with SQLAlchemy ORM, CrewAI with Azure OpenAI
- **Frontend (Angular)**: Angular with PrimeNG components, SCSS with PrimeFlex, port 4001
- **Testing**: Playwright E2E tests, Python pytest, desktop-only tests
- **AI Agents**: CrewAI integration, Azure OpenAI, multi-agent collaboration

### 5. Environment Configuration
Include rules for required environment variables:
```bash
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

# Database
DATABASE_URL=sqlite:///./ai_team.db
```

### 6. Development Workflow Rules
Create rules for:
- **Local Development**: Backend on port 8000, Frontend on port 4001, Test execution
- **Code Changes**: Backend changes, Frontend changes, Database changes, AI agent changes
- **Testing Requirements**: New features must include Playwright E2E tests, API endpoints testing, Frontend component testing

### 7. MANDATORY Playwright Testing Requirements
Create strict rules for:
- **MANDATORY**: Create Playwright tests for ALL UI changes and new features
- **UI Changes**: Every frontend component modification requires E2E test coverage
- **New Features**: All new UI features must have corresponding Playwright tests
- **Component Updates**: Any changes to existing components need test updates
- **User Interactions**: Test all user interactions (clicks, forms, navigation)
- **Visual Elements**: Test that UI elements are visible and functional
- **Data Display**: Test that data is properly displayed and formatted
- **Error Handling**: Test error states and edge cases
- **Responsive Design**: Test on different screen sizes (desktop focus)
- **Accessibility**: Test keyboard navigation and screen reader compatibility

### 8. When Playwright Tests Are MANDATORY
Create rules for:
- **New Components**: Any new Angular component requires E2E test
- **Component Modifications**: Changes to existing components need test updates
- **UI/UX Changes**: Any visual or interaction changes require tests
- **New Features**: All new frontend features must have tests
- **Bug Fixes**: UI bug fixes require test coverage
- **Styling Changes**: CSS/SCSS changes that affect functionality need tests
- **Form Updates**: Any form modifications require test coverage
- **Navigation Changes**: Route or navigation updates need tests
- **Data Display**: Changes to how data is shown require tests
- **User Workflows**: Any new user workflow requires end-to-end testing

### 9. Playwright Test Structure Rules
Include rules for:
- **Test Files**: Create `test_[feature_name].spec.ts` for each feature
- **Test Organization**: Group related tests in describe blocks
- **Test Naming**: Use descriptive test names that explain the functionality
- **Data Test IDs**: Use `data-testid` attributes for reliable element selection
- **Page Objects**: Create reusable page object patterns for complex components
- **Mock Data**: Use consistent mock data for predictable test results
- **Test Isolation**: Each test should be independent and not rely on other tests
- **Cleanup**: Clean up test data after each test run
- **Parallel Execution**: Tests should be able to run in parallel safely

### 10. AI Agent Guidelines
Create rules for:
- **Agent Roles**: Product Manager, Solution Architect, Backend Developer, Frontend Developer, QA Tester, Code Reviewer
- **Workflow Execution**: Input (Jira story ID), Process (Multi-agent collaboration), Output (Generated code files), Version Control (Automatic commits and PRs)

### 11. File Organization Rules
Create detailed rules for:
- **Backend Files (crewai_app/)**: main.py, database.py, config.py, agents/, workflows/, services/, models/, utils/
- **Frontend Files (frontend/)**: Feature modules, shared components, services, models, assets
- **Test Files (tests/)**: Playwright E2E tests, Python unit and integration tests
- **Documentation Files (docs/)**: Deployment, CI/CD, README files
- **Target Projects (repos/)**: Cloned target projects managed as git submodules

### 12. Common Patterns
Include rules for:
- **API Response Format**: Standardized response structure
- **Frontend Component Structure**: Angular component patterns
- **Database Model Pattern**: SQLAlchemy model patterns

### 13. Debugging & Troubleshooting
Create rules for:
- **Common Issues**: API 500 errors, Frontend not loading, Database errors, Jira integration, Git submodules
- **Logging**: Backend structured logging, Frontend console logging, AI Agents detailed workflow execution logs

### 14. Production Deployment
Include rules for:
- **Requirements**: Production-ready environment, persistent storage, monitoring, security
- **Documentation**: Setup guides, CI/CD documentation, API documentation

### 15. Best Practices
Create rules for:
- **Code Organization**: Modular design, error handling, type safety, testing
- **Documentation Best Practices**: Immediate updates, comprehensive coverage, clear descriptions, code examples, version tracking
- **Git Workflow**: Branch naming, commit messages, pull requests, code review
- **Performance**: Database queries, API responses, frontend optimization, caching

### 16. Security Considerations
Include rules for:
- **API Security**: Input validation, authentication, rate limiting, CORS
- **Data Protection**: Secrets management, database security, logging, dependencies

### 17. Maintenance
Create rules for:
- **Regular Tasks**: Dependency updates, database cleanup, log rotation, performance monitoring
- **Monitoring**: API health, database performance, frontend errors, workflow execution

### 18. README Update Requirements
Create MANDATORY rules for:
- **README Updates**: MUST update README.md in any core folder when making changes
- **Core Folders**: crewai_app/, frontend/, tests/, docs/, repos/
- **Change Types**: New features, API changes, component changes, test updates
- **Update Scope**: Reflect new functionality, file changes, and architectural updates
- **Commit Message**: Include "Update README" in commit message when README is modified

## Output Requirements
Generate a comprehensive `.cursorrules` file that:
1. Is well-structured with clear sections and subsections
2. Includes specific, actionable rules for each aspect of the project
3. Provides code examples where appropriate
4. Emphasizes the MANDATORY nature of Playwright testing for UI changes
5. Includes detailed file organization rules
6. Covers all aspects of the development workflow
7. Includes troubleshooting and debugging guidance
8. Emphasizes the production-ready nature of the system
9. Includes comprehensive testing requirements
10. Covers documentation maintenance requirements

## Key Emphasis Points
- **MANDATORY Playwright Testing**: Every UI change requires E2E test coverage
- **Production-Ready**: This is a production system handling real Jira stories
- **Comprehensive Testing**: All new features must include tests
- **Documentation Maintenance**: README files must be updated with changes
- **Code Quality**: Follow strict coding standards and best practices
- **AI Agent Collaboration**: Multi-agent workflow execution with CrewAI
- **Version Control**: Proper git workflow with meaningful commit messages
- **Security**: Production security considerations and best practices

Generate a comprehensive cursor rules file that covers all these aspects in detail, with clear, actionable rules that will guide AI assistants in working effectively with this complex AI orchestration platform.
