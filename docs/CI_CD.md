## CI/CD Pipeline

### Goals
- Lint, build, and test backend and frontend
- Run Playwright E2E against dev server on port 4001
- Enforce commit message pattern `MINIONS-1:` and project key

### Suggested GitHub Actions Workflow

```
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Install frontend deps
        working-directory: frontend
        run: npm ci

      - name: Start frontend
        working-directory: frontend
        run: npm run start -- --port 4001 &

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install backend deps
        run: pip install -r requirements.txt

      - name: Start backend
        run: uvicorn crewai_app.main:app --host 0.0.0.0 --port 8000 &

      - name: Install Playwright
        run: npx playwright install --with-deps

      - name: Run Playwright tests
        run: npx playwright test --project=chromium
```

### Enforcements
- Use commit messages prefixed with `MINIONS-1:`
- Include Jira story keys (e.g., `NEGISHI-165`) when relevant


