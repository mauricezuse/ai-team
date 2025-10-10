# Workflow UI Improvement Plan

## Goals

- Unify all workflow visibility into a single tabbed detail page (no separate “advanced” area).
- Provide real-time status, PR checks, code diffs, LLM calls (with filters), execution history + comparison, escalations, and artifacts.
- Improve performance (lazy loading, virtualization), accessibility, testability, and maintainability.

## Branching Strategy & Phase Branch Names

- Branch naming convention: `MINIONS-{phaseNumber}-{short-desc}` (kebab-case), one branch per phase.
- Commit message convention: `MINIONS-xxx: Message` (e.g., `MINIONS-3: Add LLM Calls tab`).
- PR target: `main` (or `develop` if used), with required checks enabled and Playwright E2E.
- Note: MINIONS-1 and MINIONS-2 are already used and MUST NOT be reused.
- Phase-to-branch mapping:
- MINIONS-3-workflow-ui (this plan)
- MINIONS-4-guardrails (diff-first, schema checks, citations)
- MINIONS-5-token-context (budgets, summaries, retrieval)
- MINIONS-6-observability (OTel traces/metrics/logs)
- MINIONS-7-ci-templates (PR checks templates + branch protection docs)
- MINIONS-8-tests (coverage for new behaviors)
- MINIONS-9-rollout (staged rollout, flags)

Current phase branch to create now: `MINIONS-3-workflow-ui`.

## Scope & IA

- Workflows List (`frontend/src/app/features/workflows/workflows-list.*`):
- Add filter bar (search, status, date range), better status chips, and live indicators.
- Workflow Detail (`frontend/src/app/features/workflows/workflow-detail.*`):
- Header: title, status chip(s), action buttons (Execute, Refresh, Start Execution, Reconcile), PR link and branch (when available).
- KPIs: status, created/started/finished, last heartbeat, total tokens/cost/calls, avg latency.
- Tabs:
1) Overview: Jira story summary, AC mapping, architect plan summary.
2) Conversations: searchable, agent/status filters, expand/collapse, prompt/output viewer with copy + redaction toggle.
3) Code Diffs: per-file diff view (monaco-diff or lightweight diff), with link to repo.
4) PR & Checks: PR URL, branch, required checks with statuses, timestamps, and re-run links.
5) LLM Calls: paginated table, model/date/text filters, detail drawer, token/cost charts.
6) Executions: history table (id, status, tokens, cost, latency), compare two executions (backend `/executions/compare`).
7) Escalations: list with severity, reason, status, resolution; acknowledge/resolve actions (future backend endpoints).
8) Artifacts: download links for test reports, logs, trace bundles, Playwright HTML report.
- Advanced Module Deprecation:
- Replace features from `workflows-advanced` (LLM calls table, run comparison, code artifacts, collaboration) with the tabs above.
- Migrate tests off `/workflows/:id/advanced/*` routes, then remove the module and route.

## Componentization

- New components under `frontend/src/app/features/workflows/`:
- `workflow-header/`, `workflow-kpis/`, `workflow-tabs/`
- `workflow-overview-tab/`
- `workflow-conversations-tab/`
- `workflow-code-diffs-tab/`
- `workflow-pr-checks-tab/`
- `workflow-llm-calls-tab/`
- `workflow-executions-tab/`
- `workflow-escalations-tab/`
- `workflow-artifacts-tab/`
- Services
- Extend `WorkflowAdvancedService` or introduce `WorkflowInsightsService` to fetch PR checks, diffs metadata, artifacts, executions compare, and LLM calls with pagination.
- Keep `WorkflowStatusChannelService` for SSE/WS.

## API Dependencies (Backend alignment)

- Existing (keep): `/conversations/{id}/llm-calls`, `/workflows/{id}/executions`, `/workflows/{id}/executions/compare`, status SSE/WS, ETag on workflow detail.

- New (READ-first, robust contracts):
  - GET `/workflows/{workflow_id}/pr` → PR summary for the workflow
    - { number, url, title, state, headBranch, baseBranch, headSha, createdAt, mergedAt? }
  - GET `/workflows/{workflow_id}/pr/checks` → Required checks with latest statuses (paginated)
    - [ { name, status, conclusion, startedAt, completedAt, url } ]
  - GET `/workflows/{workflow_id}/diffs` → Unified diffs between base and head (paginated, optional path filter)
    - [ { path, patch, headSha, baseSha } ]
  - GET `/workflows/{workflow_id}/artifacts` → List execution/workflow artifacts (paginated, optional kind filter)
    - [ { id, kind, uri, checksum, sizeBytes?, createdAt } ]
  - (Optional) POST `/workflows/{workflow_id}/pr/checks/{check_suite_id}/rerun` → Trigger re-run of a check suite

- Endpoint behavior guidelines:
  - All list endpoints paginated: `page`, `page_size`, `sort_by`, `sort_dir`.
  - Cache-friendly responses with short-lived caching where applicable and ETag support on detail endpoints.
  - Consistent error taxonomy (4xx for client/data errors, 5xx for server/transient). Map rate limits explicitly.

## Backend Data Model (Production-ready)

- PR:
  - `id`, `workflow_id`, `pr_number`, `url`, `title`, `state`, `head_branch`, `base_branch`, `head_sha`, `created_at`, `closed_at?`, `merged_at?`
- CheckRun:
  - `id`, `workflow_id`, `pr_id`, `name`, `status`, `conclusion`, `external_id`, `html_url`, `started_at`, `completed_at`
- Artifact:
  - `id`, `workflow_id`, `execution_id?`, `kind` ("test-report","trace","lint","coverage"), `uri`, `checksum`, `size_bytes?`, `created_at`
- Diff:
  - `id`, `workflow_id`, `path`, `patch` (unified), `head_sha`, `base_sha`, `created_at`

Notes:
- Keep normalized `LLMCall` (already present) and roll up execution stats if needed.
- Store only metadata and pointers for artifacts; binaries go to object storage with signed URLs.

## Background Processing & Webhooks

- Job runner:
  - Use a durable background worker (Celery/RQ/Dramatiq/Arq) for GitHub/Jira calls, diff computation, artifact ingestion.
  - Idempotent jobs keyed by `<workflow_id, head_sha>` for diffs; backoff and retry on rate limits/timeouts.
- GitHub webhooks (long-term):
  - Ingest `pull_request`, `check_suite`, `check_run`, `workflow_run`, `status` events.
  - Map to PR/CheckRun rows and broadcast deltas over SSE/WS keyed by `workflow_id`.
- Diff computation:
  - Compute via libgit or CLI between `base_sha` and `head_sha`; cache results, paginate large diffs.
- Artifact management:
  - Upload artifacts to object storage; persist metadata. Expose via GET `/artifacts` and serve with signed URLs.

## Observability & Caching

- Tracing:
  - OpenTelemetry for FastAPI and HTTP clients (Jira/GitHub/OpenAI). Spans per agent step, LLM call, GitHub/Jira request, diff job.
- Metrics:
  - API latency (p95), workflow cycle time, PR checks pass rate, token/cost usage, retries/error taxonomy.
- Logs:
  - Structured with `workflow_id`, `execution_id`, `request_id`; secrets redaction enabled by default.
- Caching:
  - Short-lived cache for PR/check summaries (30–60s). ETag/If-None-Match on detail endpoints to minimize payloads.

## Security & Compliance

- Secrets management:
  - Use Azure Key Vault/Secrets Manager in prod; rotate tokens quarterly; alerts before expiry; never log secrets.
- GitHub integration:
  - Short-term PAT with least privileges; long-term migrate to GitHub App (granular permissions, signed webhooks).
- RBAC:
  - Protect backend endpoints with simple auth in prod (even if behind a proxy), especially artifacts and diffs.
- Data retention:
  - Define and enforce retention windows for logs, LLM prompts/outputs, diffs and artifacts (e.g., 90 days).

## Performance & A11y

- Change detection: OnPush, async pipe, `trackBy` for lists.
- Virtual scroll for conversations and LLM calls; server-side pagination/filters for LLM calls.
- Lazy-load heavy tabs (diff viewer, charts) only when selected.
- Keyboard navigation for tabs; aria-labels, focus indicators; high-contrast chips.
- Skeleton loaders for initial and tab loads.

## Testing (Playwright)

- Workflows list: filters, navigation, start/delete, error states.
- Detail tabs: tab switching, status updates, KPIs, conversations filters/expand, diffs render, PR checks visible, LLM calls pagination/filters, execution comparison, artifacts links.
- Accessibility checks (basic keyboard navigation and focus outline assertions).
- Migrate advanced-route tests to the new tabs, then remove advanced module.

## Deprecation Strategy for Advanced Module

1) Implement new tabs and achieve feature parity.
2) Add Playwright tests for new tabs (same assertions as advanced screens).
3) Update any links (e.g., remove “Advanced View” link), and re-point tests.
4) Remove route `:id/advanced` from `workflows.module.ts` and delete `workflows-advanced/` directory.

## Acceptance Criteria

- All key insights available within the main workflow detail tabs.
- Near real-time updates for status; visible KPIs with token/cost metrics.
- Playwright tests pass reliably; no references to `/advanced` remain.

## Risks & Mitigations

- Heavy data loads → lazy loading, pagination, and virtualization.
- Large diff viewer bundle → lazy-load or use a lightweight viewer.
- Backend gaps → stage UI behind feature flags until endpoints are ready.

## To-dos

- [ ] Create branch `MINIONS-3-workflow-ui`
- [ ] Introduce tabbed layout in workflow detail with header and KPIs
- [ ] Add Overview tab (Jira summary, AC mapping, plan summary)
- [ ] Implement Conversations tab with filters and virtualization
- [ ] Implement Code Diffs tab with lazy-loaded diff viewer
- [ ] Implement PR & Checks tab (PR URL, required checks statuses)
- [ ] Implement LLM Calls tab with pagination, filters, charts
- [ ] Implement Executions tab with history and comparison
- [ ] Implement Escalations tab (read-only first)
- [ ] Implement Artifacts tab (test reports, logs, traces)
- [ ] Extend service(s) to fetch PR checks, diffs meta, artifacts
- [ ] Add Playwright E2E covering all tabs and interactions
- [ ] Migrate advanced route tests to new tabs and remove links
- [ ] Remove `:id/advanced` route and `workflows-advanced` directory

### To-dos

- [ ] Define env vars and PAT scopes; add .env placeholders and secret management docs
- [ ] Implement Jira and GitHub services with PAT auth, retries, and error handling
- [ ] Define CrewAI agents, prompts, and orchestrator workflow with persistence
- [ ] Add FastAPI endpoints for workflow start/detail/resume and health
- [ ] Implement Angular UI for workflows, conversations, diffs, PR status, escalations
- [ ] Add OpenTelemetry tracing, structured logs, metrics, and redaction
- [ ] Add/extend pytest and Playwright coverage, fixtures, and deterministic data
- [ ] Author GitHub Actions templates for lint/type/tests/e2e and doc required checks
- [ ] Create all documentation files with practical runbooks and ADRs
- [ ] Stage rollout across repos with branch protection and SLOs
- [ ] Add DB models/tables: PR, CheckRun, Artifact, Diff
- [ ] Add endpoints: GET /workflows/{id}/pr, /pr/checks, /diffs, /artifacts (and optional re-run)
- [ ] Implement background jobs for PR checks fetch, diff computation, artifact ingestion
- [ ] Add GitHub webhook ingestion and mapping to PR/CheckRun
- [ ] Wire PR & Checks and Artifacts tabs to new endpoints
- [ ] Add contract tests for new endpoints (pagination, filters, ETag)
- [ ] Add OpenTelemetry spans for PR/checks, diffs, artifacts flows
