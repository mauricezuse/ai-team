# AI-Team Integration & Testing Plan

## 1. Integration Testing
- Ensure real integrations work as expected with actual GitHub repo and Jira project.
- Use test branch and test Jira project if possible.
- Set `USE_REAL_GITHUB=true` and `USE_REAL_JIRA=true` in `.env`.
- Run workflows that trigger PR and ticket creation.
- Check that PRs and tickets are created, and error handling/logging works.

## 2. Workflow Refactoring
- Make sure all workflows use the new service classes, not the old stubs.
- Replace any direct calls to stub functions in workflows with service methods.
- Pass the config flag to the service constructor (e.g., `GitHubService(settings.use_real_github)`).

## 3. Error Handling & Logging
- Ensure all API errors are logged clearly.
- Optionally, raise exceptions or return error objects for workflow-level handling.

## 4. Documentation & Onboarding
- Document config flags and required environment variables in README.
- Add a section on how to test integrations safely (using stubs vs. real).

## 5. Optional: Expand Integrations
- For GitHub: Add methods for branch creation, commit pushing, PR commenting, etc.
- For Jira: Add methods for updating tickets, querying issues, etc.

## 6. (Optional) Add Integration Tests
- Use pytest or similar to run tests with the real/stub flags toggled.
- Mock API responses for unit tests, use real API for integration tests (with test accounts).

---

**Top Recommendation:**
- Start with integration testing and workflow refactoring.
- Once confirmed, expand integrations and add more tests/documentation as needed. 