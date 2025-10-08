---
applyTo: '**'
---

# AI Assistant Memory & Preferences

## Git

- Policy: NEVER auto stage/commit or push from the assistant.
- Commit messages should include the current branch ID (e.g., `NEGISHI-111`).

To change this policy, edit this section explicitly. Example:

```
- Policy: Assistant may stage/commit when asked explicitly in chat by the user.
```

## Code Quality

- Only production-ready code should be committed; test endpoints should not be committed.

## Frontend Dev Server

- Default local UI port: 4001

## Testing

- Prefer running desktop Playwright tests; mobile projects are disabled by default.

---
applyTo: '**'
---

# AI Team System Memory

## Production System Requirements
The AI Team system must be production-ready and should NOT use mock data. The system should use real Jira integration to fetch actual story information from https://zusesystems.atlassian.net/browse/NEGISHI-165 and other Jira stories. All data should come from real sources, not mock or simulated data.

## Key Requirements
- Real Jira integration for story fetching
- Production-ready data sources
- No mock or simulated data
- Actual story information from Jira API
- Real workflow execution with actual AI agents
