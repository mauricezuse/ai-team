# AI Team: CrewAI Orchestration Platform

## Overview
This project is a modular, production-ready orchestration platform for an AI-powered agent team (CrewAI) that generates, reviews, and tests code for a web application (e.g., Upwork-like MVP). It is designed for rapid development, Azure deployment, and best practices in modern software engineering.

## Features
- Modular agent roles: Product Manager, Architect, Developer, Reviewer, Tester
- Orchestrated workflows for code generation and review
- Azure OpenAI integration (GPT-4o/4)
- FastAPI REST API for orchestration
- Containerized with Docker
- Infrastructure-as-Code for Azure (Bicep/Terraform)
- CI/CD ready
- Observability and logging

## Project Structure
```
ai-team/
│
├── crewai_app/                # Main Python app (CrewAI orchestration)
│   ├── __init__.py
│   ├── main.py                # Entrypoint: FastAPI app (REST API for orchestration)
│   ├── config.py              # Settings, env vars, Azure OpenAI config
│   ├── agents/                # Agent role definitions, prompts, tools
│   │   ├── __init__.py
│   │   ├── pm.py
│   │   ├── architect.py
│   │   ├── developer.py
│   │   ├── reviewer.py
│   │   └── tester.py
│   ├── workflows/             # Orchestration logic, task flows
│   │   ├── __init__.py
│   │   └── mvp_workflow.py
│   ├── services/              # Integration services (Azure OpenAI, GitHub, Jira, etc.)
│   │   ├── __init__.py
│   │   ├── openai_service.py
│   │   ├── github_service.py
│   │   └── jira_service.py
│   ├── models/                # Pydantic models, schemas
│   │   ├── __init__.py
│   │   └── task.py
│   └── utils/                 # Utility functions, logging, error handling
│       ├── __init__.py
│       └── logger.py
│
├── tests/                     # Unit/integration tests for orchestration logic
│   └── test_workflow.py
│
├── infra/                     # Infrastructure-as-Code (Azure)
│   ├── bicep/                 # Bicep/ARM templates
│   └── terraform/             # Terraform scripts (optional)
│
├── .env                       # Environment variables (never commit secrets)
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Containerization
├── README.md                  # Project overview, setup, usage
└── .gitignore
```

## Local Development

Backend (FastAPI):
```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn crewai_app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend (Angular on port 4001):
```
cd frontend
npm install
npm run start -- --port 4001
```

Playwright E2E (points to http://localhost:4001):
```
npx playwright install
npx playwright test --project=chromium
```

## Setup
1. Clone the repo
2. Create a Python virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Set up your `.env` file with Azure OpenAI and other secrets
5. Run backend and frontend as above
6. Run E2E tests as above
7. See `docs/DEPLOYMENT.md` and `docs/CI_CD.md`

## Contributing
- Follow best practices for modular code and clear separation of concerns
- Use environment variables for all secrets/config
- Write tests in `tests/`
- Use PRs for all changes

## License
MIT 

## Commit Message Enforcement (Project Key)

This project enforces that all commit messages include the project key (e.g., `NEGISHI-123`) using a hybrid approach:

### 1. Dockerfile (for containerized agents)
- The Dockerfile automatically installs the `commit-msg` git hook in every container.
- **No manual steps required** when using Docker.

### 2. Setup Script (for flexible/local/CI environments)
- Use the provided `setup_hooks.sh` script to install the hook in any environment.
- **Usage:**
  ```sh
  ./setup_hooks.sh
  ```
  (Run from the root of your git repository.)

### 3. CI/CD Enforcement
- A GitHub Actions workflow checks all commit messages in PRs and pushes to protected branches.
- **No non-compliant commits can be merged.**

### 4. Agent Code Enforcement
- All AI agents (via `GitHubService`) programmatically ensure commit/PR messages include the project key.

---

## Onboarding Checklist for New Environments/Agents
- [ ] If using Docker, build your container as usual (hook is installed automatically).
- [ ] If not using Docker, run `./setup_hooks.sh` after cloning the repo.
- [ ] Ensure the `PROJECT_KEY` is set in your `.env` file for correct enforcement.
- [ ] All commit and PR messages must include the project key (e.g., `NEGISHI-123`).
- [ ] The CI/CD workflow will block any non-compliant commits.

--- 