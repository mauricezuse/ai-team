# PR Creation and Rebase Plan (MINIONS-2/3/4)

### Actual Conflicts for MINIONS-4-optimization (auto-detected)

.gitignore

## Branch Graph and Current State
- `main`
- `MINIONS-2-advanced-workflow-ui` (no upstream)
- `MINIONS-2-workflow-status` (no upstream)
- `MINIONS-3-workflow-ui` (no upstream)
- `MINIONS-4-optimization` (upstream set, pushed)
- `MINIONS-4-conversations-optimization` (no upstream; currently identical to 4-optimization at creation)

### Shared Ancestry
- `MINIONS-2-advanced-workflow-ui` and `MINIONS-2-workflow-status` share base `3dd35e5b`.
- `MINIONS-3-workflow-ui` diverges from `main` after MINIONS-2 work; histories are independent after the common base.

## Recommended PR Order (lowest divergence first)
1. `MINIONS-2-advanced-workflow-ui` → `main`
2. `MINIONS-2-workflow-status` → `main` (rebase onto updated `main` after step 1)
3. `MINIONS-3-workflow-ui` → `main` (rebase onto updated `main` after step 2)
4. `MINIONS-4-optimization` → `main` (already pushed; verify clean on updated `main`)
5. `MINIONS-4-conversations-optimization` → `main` (branch from updated 4-optimization or rebase onto `main` depending on intent)

Rationale: Keep chronological dependency across feature-lines and minimize conflicts by merging older base work first.

## Safety Backups Before Any Rebase
For each branch `B`:
- Create a backup tag and backup branch:
  - `git checkout B`
  - `git tag backup/B-$(date +%Y%m%d-%H%M%S)`
  - `git branch B-backup-$(date +%Y%m%d-%H%M%S)`
- Record commit list: `git log --oneline --decorate --graph > backups/B.log`

## Upstream Setup and Push (no PR creation yet)
- `git push -u origin MINIONS-2-advanced-workflow-ui`
- `git push -u origin MINIONS-2-workflow-status`
- `git push -u origin MINIONS-3-workflow-ui`
- `git push -u origin MINIONS-4-conversations-optimization`

> Note: Do not push rebased work until conflicts are resolved and tests pass.

## Detailed Rebase Plan Per Branch

### General Rebase Checklist
- Ensure working tree clean: `git status`
- Backup (tag + branch)
- `git fetch origin && git rebase origin/main`
- Resolve conflicts (see playbook below)
- `git add -A && git rebase --continue`
- Run tests/lint; amend if needed: `git commit --amend`
- Push after validation: `git push -u origin B --force-with-lease`

### 1) MINIONS-2-advanced-workflow-ui → main
- Backup branch/tag
- Rebase onto `origin/main`
- Likely conflicts:
  - `frontend/src/app/features/workflows/*` (components/services)
  - `tests/playwright/*` (new e2e specs)
  - Possibly backend endpoints only if touched
- Resolution strategy:
  - Prefer branch UI changes; if `main` added adjacent code, fold both.
  - Keep new tests; adapt imports/selectors to match latest `main`.
- Validate: `npx playwright test`, Python unit tests if applicable.

### 2) MINIONS-2-workflow-status → main
- Backup branch/tag
- Rebase onto updated `origin/main`
- Likely conflicts:
  - Backend: `crewai_app/main.py`, endpoints/models for workflow status
  - Frontend: status components/services/models
  - Tests: error display/status tests, screenshots
- Resolution strategy:
  - Backend: merge schemas and endpoints; prefer stricter validation and consistent API responses. Unify model fields; add migration if needed.
  - Frontend: unify service URLs/interfaces; ensure stable `data-testid` attributes.
  - Tests: keep stable selectors; update renamed routes.
- Validate: run backend, Playwright tests.

### 3) MINIONS-3-workflow-ui → main
- Backup branch/tag
- Rebase onto updated `origin/main`
- Likely conflicts:
  - Frontend: conversation display, persistence UI, SSE/heartbeat
  - Backend: SSE endpoints or message persistence if touched
  - Tests: conversation persistence, UI assertions
- Resolution strategy:
  - Preserve SSE/heartbeat improvements; reconcile with `main` SSE.
  - Ensure persistence API aligns with status changes; update models/interfaces.
- Validate: Playwright tests; verify SSE stream live.

### 4) MINIONS-4-optimization → main
- Already pushed; still backup.
- Rebase onto `origin/main`
- Likely conflicts:
  - `crewai_app/utils/*` (new optimizer modules)
  - `crewai_app/workflows/*` (orchestrator/streamlined)
  - `tests/*`, docs/ and READMEs
- Resolution strategy:
  - Keep new optimizer modules; resolve name clashes by namespacing.
  - Orchestrator should be the entry point; keep additive and avoid duplication.
- Validate: `python3 test_optimization_standalone.py`, `pytest`, Playwright if UI, lint.

### 5) MINIONS-4-conversations-optimization → main
- If building on 4-optimization:
  - Rebase onto `origin/MINIONS-4-optimization` first, validate, then rebase onto `origin/main` after 4-optimization merges.
- If independent target to `main`:
  - Rebase directly onto updated `origin/main` after step 4.
- Validate: tests as appropriate.

## Per-File Conflict Resolution Playbook

- Backend API (`crewai_app/main.py`, `crewai_app/services/*`, `crewai_app/models/*`):
  - Keep shared interfaces consistent; prefer typed schemas and stricter validation.
  - For breaking changes, update backend and frontend models in one pass.

- Workflows (`crewai_app/workflows/*`):
  - Ensure a single orchestrator entry point (`WorkflowOrchestrator`).
  - Keep existing workflows intact; orchestrator handles routing.
  - Extract common helpers into `utils` if duplication appears.

- Utils (`crewai_app/utils/*`):
  - Keep new optimization files (`task_complexity_assessor.py`, `cost_monitor.py`, `efficiency_reporting.py`).
  - Resolve naming by explicit namespacing (e.g., `optimization_*`).

- Frontend (`frontend/src/app/**`):
  - Align interfaces with backend responses (status, conversation, workflow).
  - Use consistent `data-testid` for test reliability.
  - Merge styles cautiously; preserve accessibility and test hooks.

- Tests (`tests/playwright/**`, `tests/test_*.py`):
  - Preserve all new tests; update selectors and expectations to final API.
  - Consolidate overlapping tests with descriptive names; ensure isolation.

- Documentation (`README.md`, `docs/**`):
  - Merge content; ensure updated architecture and routes.
  - Verify environment variable docs reflect final state.

## Commands Cheat Sheet Per Branch
- Backup:
  - `git checkout <branch>`
  - `git tag backup/<branch>-$(date +%Y%m%d-%H%M%S)`
  - `git branch <branch>-backup-$(date +%Y%m%d-%H%M%S)`
  - `git log --oneline --decorate --graph > backups/<branch>.log`
- Rebase:
  - `git fetch origin`
  - `git rebase origin/main`
  - Resolve conflicts, then `git add -A`
  - `git rebase --continue`
- Validate:
  - `npx playwright test`
  - `python3 -m pytest`
  - Lint as applicable
- Push:
  - `git push -u origin <branch> --force-with-lease`

## Rollback Plan
- Restore a branch to pre-rebase:
  - `git reset --hard <branch>-backup-<timestamp>`
  - or: `git reset --hard backup/<branch>-<timestamp>`
- If already pushed:
  - `git push --force-with-lease origin <branch>`

## PR Creation Guidance
- Titles: `MINIONS-x: <short description>`
- Body:
  - Context (scope, dependencies)
  - Changes summary
  - Testing steps
  - Risk and rollback plan
- Labels: feature, backend, frontend, tests, docs as applicable
- Reviewers: component owners

