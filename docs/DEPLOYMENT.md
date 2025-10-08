## Deployment Guide

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Node 20+
- Jira/GitHub credentials configured in `.env`

### Environment Variables
Create `.env` at repo root:

```
NEGISHI_JIRA_BASE_URL=
NEGISHI_JIRA_EMAIL=
NEGISHI_JIRA_API_TOKEN=
OPENAI_API_KEY=
```

### Local Deployment (Docker)
```
docker build -t ai-team-backend .
docker run -p 8000:8000 --env-file .env ai-team-backend
```

Frontend (Angular):
```
cd frontend
npm install
npm run start -- --port 4001
```

### Cloud Deployment (outline)
- Build backend container and push to registry
- Provision app service/container app
- Configure env vars/secrets
- Expose port 8000
- Point frontend hosting to backend API via proxy

### Database
- SQLite by default (`ai_team.db`), mount persistent volume in production

### HealthCheck
- Backend: GET `/health` (proxied via Angular dev server config)


