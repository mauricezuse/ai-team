## Advanced Workflow UI Implementation Plan

### Goals
- Provide AI engineers with rich, actionable visibility into agent-driven workflows.
- Enable review, analysis, debugging, and iterative improvement of prompts, tasks, and collaboration.
- Maintain production reliability; do not weaken business flows or tests.

### Core Capabilities
- Workflow Timeline and Step Visualization
  - Collapsible timeline of workflow steps with status badges (pending/running/completed/failed).
  - Per-step details: agent, start/end timestamps, runtime, outputs, escalations, collaborations.
  - Filters (by agent, status, time window, keyword).
- Prompt and Output Inspection
  - Full prompt payloads and responses per agent call with token counts and cost estimations.
  - Redaction controls for sensitive content.
  - Diff view for prompt revisions across runs.
- LLM Calls Explorer
  - Tabular list of LLM calls with sortable columns: model, prompt tokens, completion tokens, total tokens, cost, latency.
  - Drill-down to request/response JSON and raw content.
  - Export selected calls as JSON for offline analysis.
- Collaboration & Escalations Map
  - Visualization of inter-agent escalations and collaboration requests.
  - Quick links from nodes to related conversations and code diffs.
- Code Artifact Viewer
  - List of code files generated/modified by each step and conversation.
  - Lightweight embedded code viewer with syntax highlighting and diff against previous versions.
- Error & Retry Diagnostics
  - Consolidated error panel with stack traces, failing prompts, and retry metadata.
  - Suggestion panel for likely fixes (prompt trims, schema validation, chunking strategies).
- Run Comparisons
  - Select multiple runs of the same story to compare prompts, outputs, token usage, cost, latency, and outcomes.
  - Present deltas and regression indicators.
- Workflow Controls (safe)
  - Re-run from step, resume, skip step (if safe), escalate to human review.
  - Guardrails to avoid destructive operations in production by default.

### Data Model & API Enhancements
- Ensure `Conversation` exposes: `prompt`, `output`, `details`, `total_tokens_used`, `total_cost`, `llm_calls`.
- Ensure `LLMCall` endpoint returns: id, model, prompt/completion/total tokens, response time, cost, request/response data, timestamp.
- Add pagination and filters for `/conversations/{id}/llm-calls`.
- Add endpoint for workflow run comparison: `/workflows/{id}/compare?with=<id2>` returning aggregate stats and key diffs.

### Frontend Architecture
- Feature module: `features/workflows-advanced/`
  - Components:
    - `workflow-timeline` (timeline + filters)
    - `llm-calls-table` (sortable, pageable, export)
    - `prompt-output-viewer` (detail drawer with redact toggle)
    - `collaboration-graph` (agent network visualization)
    - `code-artifacts` (file list + diff viewer)
    - `run-comparison` (metrics and diffs)
    - `error-diagnostics` (errors, retries, suggestions)
  - Services:
    - `workflow-advanced.service.ts` for new endpoints
    - `export.service.ts` for CSV/JSON export
  - Shared:
    - Reusable `data-testid` hooks; PrimeNG tables, dialogs, toasts.

### UX Notes
- Keep consistent with existing styling: PrimeNG + PrimeFlex.
- Ensure accessibility: keyboard navigation, ARIA labels, focus traps in dialogs.
- Keep toasts visible long enough when actions succeed/fail.
- Avoid full-page reloads; use drawers/dialogs for deep inspection.

### Performance & Reliability
- Use lightweight virtualized tables for large LLM call lists.
- Lazy-load heavy components (diff viewer, graphs).
- Debounce filter inputs; memoize computed rows.
- Paginate all large API responses.

### Security & Privacy
- Redact secrets (tokens, endpoints) by default in prompt/request displays.
- Add a “Show sensitive” toggle gated by permission.
- Avoid logging sensitive content client-side.

### Telemetry & Metrics
- Capture UI interactions to identify pain points.
- Display per-run aggregates: total tokens, total cost, average latency, error rate.

### Testing Strategy
- Playwright E2E:
  - Timeline renders, filters work, step details expand.
  - LLM calls table sorts/filters/paginates and exports JSON.
  - Prompt viewer opens, redaction toggle works.
  - Code diff viewer loads and highlights changes.
  - Error diagnostics shows expected messages.
  - Run comparison view renders deltas.
- Unit tests for services and selectors.

### Incremental Delivery Plan
1) Backend API support
   - Add pagination/filters to LLM calls endpoint; add run compare endpoint.
   - Update OpenAPI docs.
2) Frontend scaffolding
   - Create `workflows-advanced` module with routes under `/workflows/:id/advanced`.
   - Implement timeline component with step details drawer.
3) LLM Calls Explorer
   - Table with sorting/filtering/pagination; detail drawer with request/response.
4) Prompt/Output Viewer
   - Token/cost display and redaction toggle.
5) Collaboration Graph
   - Visualize agent interactions; link to conversations.
6) Code Artifacts
   - File list per conversation; diff viewer integration.
7) Error Diagnostics
   - Consolidated errors with suggestions panel.
8) Run Comparison
   - Compare two runs; summarize metrics and deltas.
9) E2E Tests
   - Add Playwright specs for each feature; ensure stability.

### Dependencies
- PrimeNG Table, Dialog, Toast; Chart/Graph lib (e.g., ngx-charts or vis-network) for collaboration graph.
- Code diff: Monaco diff or jsdiff-based component.

### Risks/Mitigations
- Large payloads: paginate and lazy-load details.
- Sensitive data exposure: redact by default; add secure toggle.
- Performance: virtualize lists; memoize filters; chunk heavy views.

### Acceptance Criteria
- Engineers can visualize full workflow timeline with per-step details.
- Inspect LLM calls with token/cost metrics and raw payloads (redacted by default).
- View and diff generated code artifacts per step.
- See errors, retries, and suggestions in one pane.
- Compare two runs and identify regressions.


