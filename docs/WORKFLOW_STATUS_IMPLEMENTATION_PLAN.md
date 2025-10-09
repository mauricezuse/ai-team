## Workflow Status Accuracy – Implementation Plan

### Goal
Ensure the UI always reflects the true workflow status, immediately transitioning to a terminal state when the backend process ends, and preventing “stuck in running” displays (e.g., workflow 12).

### Root Causes To Address
- **Backend terminalization gaps**: Process end does not always persist final status (success/failed/cancelled).
- **UI reliance on coarse polling**: One-shot fetches or slow polling miss the final transition.
- **No heartbeat/real-time signal**: Abrupt executor termination leaves status stale.
- **Race conditions**: Worker completion vs. UI refresh order can cause regressions.

### High-Level Strategy
- Make the backend the source of truth with idempotent finalize semantics and a heartbeat.
- Push real-time status updates (WebSocket/SSE) and keep a robust polling fallback with ETag.
- Update Angular services to auto-reconcile status and stop updates when terminal.
- Add tests covering normal completion, exceptions, and abrupt termination.

---

## Backend Changes (FastAPI + CrewAI)

### Strong Terminalization
- Introduce a single idempotent entry point: `finalize_workflow_status(workflow_id, terminal_status, finished_at, error)` called on:
  - Normal completion
  - Exceptions
  - Cancellation
  - Shutdown hooks
- Enforce invariant: once a workflow is terminal, status cannot regress.
- Persist `finished_at` and optional `error` details.

### Heartbeat and Zombie Detection
- Executor writes `last_heartbeat_at` every N seconds while `running`.
- Background audit task scans `running` workflows; if `now - last_heartbeat_at > threshold`, mark as `failed` with reason `heartbeat timeout` via `finalize_workflow_status`.

### Real-Time Updates and API Enhancements
- WebSocket endpoint: `/ws/workflows/{id}` broadcasts status diffs and final terminal event.
- Fallback SSE endpoint: `/events/workflows/{id}` mirrors WS events.
- Enhance `GET /workflows/{id}`:
  - Add `isTerminal` boolean, `finished_at`, `error`, `last_heartbeat_at`.
  - Support `ETag` and `Last-Modified` for cache-aware polling.
- Optional: `POST /workflows/{id}/reconcile` to immediately correct stale `running` based on heartbeat.

### Logging and Metrics
- Structured logging for each transition with previous → next state and reason.
- Counters for heartbeat timeouts and abrupt exits.

### Data/Schema
- Ensure model fields exist: `status` (enum), `started_at`, `finished_at`, `error`, `last_heartbeat_at`.
- Provide migration to add/backfill fields where missing.

---

## Frontend Changes (Angular)

### Workflow Status Channel (Service)
- Implement `WorkflowStatusChannel` that attempts in order:
  1. WebSocket subscription to `/ws/workflows/{id}`
  2. Fallback to SSE `/events/workflows/{id}`
  3. Fallback to HTTP polling `GET /workflows/{id}` with exponential backoff and ETag/If-None-Match
- Auto-stop when `isTerminal === true`.
- Debounce rapid updates and enforce last-message-wins semantics.
- Reduce polling when tab is hidden; force refresh on focus.

### UI Components
- Update `workflow-detail` and `workflows-list` to subscribe to `WorkflowStatusChannel` instead of one-shot fetches.
- Display a subtle warning if status is `running` but heartbeat is stale beyond threshold.
- Normalize status mapping and visuals (colors/labels) across components.

### Data Contracts
- Extend TypeScript models with `isTerminal`, `finished_at`, `error`, `last_heartbeat_at`.

### Error and Retry Handling
- Graceful retry ladder: WS → SSE → Polling with bounded backoff.
- Handle reconnects and network blips without duplicating terminal events.

---

## Testing Plan

### Backend Unit/Integration
- Normal completion calls `finalize_workflow_status` and persists terminal state.
- Exceptions persist `failed` with `error` and `finished_at`.
- Heartbeat audit transitions stale `running` to `failed`.
- WS/SSE emit final event once; no regressions to non-terminal.
- `ETag`/`Last-Modified` respected by status endpoint.

### Frontend Unit
- Service falls back WS → SSE → Polling correctly.
- Polling stops automatically on terminal state.
- Stale heartbeat renders a warning while status is `running`.
- Debounced updates preserve last-message-wins behavior.

### Playwright E2E
- Start workflow, observe `running`, simulate completion; UI transitions to terminal promptly.
- Simulate executor crash (no finalize); audit/heartbeat timeout marks `failed`, UI updates accordingly.
- Refresh mid-run; reconnection resumes status streams and remains consistent.
- Verify no terminal → non-terminal regression and no flicker.

### Performance and Resilience
- Confirm minimal API load via ETag and backoff.
- Exercise intermittent WS disconnects and fallback correctness.

---

## Observability and Ops
- Dashboards: counts for `running` vs terminal; stale heartbeat count.
- Alerts for workflows `running` beyond threshold without heartbeats.

---

## Rollout and Backward Compatibility
- Guard WS/SSE behind a feature flag while retaining polling.
- Deploy backend first (new fields/endpoints), then frontend.
- Maintain correctness even if WS is unavailable; SSE/polling ensure accuracy.

---

## Acceptance Criteria
- UI never shows `running` once backend process ends.
- Terminal status appears within seconds of completion, or within heartbeat timeout after crashes.
- Polling halts on terminal; reconnection restores streams on refresh.
- E2E tests cover normal and abrupt termination paths and pass reliably.
- Observability shows zero stuck `running` beyond thresholds.

---

## Minimal Incremental Milestones
1. Backend: finalize routine, heartbeat, audit job, model fields/migration.
2. API: enhanced status `GET` with `isTerminal`, timestamps, ETag.
3. Frontend: status channel with polling fallback; wire to detail and list.
4. Real-time: add WS/SSE and switch channel order to WS-first.
5. Tests: unit, integration, Playwright E2E; add observability.
6. Rollout: feature flags; monitor and tune thresholds.


