# AI-Team: Recommended Next Steps & Ideas

## 1. Expand Agent Capabilities
- Add more agent roles (Architect, QA, Release Manager, etc.)
- Enhance workflow logic with multi-step, cross-agent processes
- Enable cross-agent communication and coordination

## 2. Improve Error Handling & Observability
- Integrate centralized logging/monitoring (e.g., Sentry, Datadog)
- Add alerting for integration failures (Slack, email, etc.)
- Implement retry and recovery logic for agent actions

## 3. Security & Compliance
- Integrate with a secret manager (Azure Key Vault, AWS Secrets Manager, etc.)
- Add audit logging for all agent actions

## 4. Scalability & Deployment
- Harden Dockerfile for production
- Automate CI/CD deployment to cloud (Azure, AWS, etc.)
- Prepare for horizontal scaling (multiple agent instances)

## 5. User Experience (for AI agents)
- Implement agent feedback loops (learning from past actions)
- (Optional) Build a dashboard for agent/workflow configuration

## 6. Testing & Quality
- Add end-to-end workflow tests
- Implement mocked/replayable tests for CI
- Increase test coverage for all code paths

## 7. Documentation & Onboarding
- Expand README with usage, architecture, and troubleshooting
- Document each agent and workflow
- Provide onboarding scripts for new environments/contributors

## 8. Feature Ideas
- Dynamic workflow generation by agents
- Integrate with more tools (Slack, Teams, Confluence, Trello, etc.)
- Enable natural language command interpretation for agents

## Advanced Improvement Ideas

### 1. Prompt Optimization & Robustness
- Move all LLM prompts to versioned, editable templates (YAML or Markdown) for easier tuning and A/B testing.
- Use stricter parsing and validation of LLM outputs (e.g., with Pydantic models or JSON schema) to catch hallucinations or format errors early.
- Add retry/correction loops: if the LLM output is invalid, automatically re-prompt with a correction hint.
- **[NEW] Implement LLM output caching:** Architect agent now caches LLM outputs to reduce rate limits. Extend to other agents for further improvement.

### 2. Codebase Indexing & Context
- Implement incremental indexing: only re-index files that have changed since the last run (using git diff or file timestamps).
- Use semantic search/embeddings to select files by similarity to the story/task, not just by name.
- Summarize large files or only include function/class signatures in the index, not full code or docstrings.

### 3. Agent Collaboration & Feedback
- Allow reviewer/tester agents to provide feedback that can trigger a re-implementation or refinement loop by the developer.
- Add optional human-in-the-loop approval/feedback steps for each agent's output before proceeding.

### 4. Performance & Cost
- Batch LLM calls where possible (e.g., generate tests for multiple files in one call).
- Use smaller/cheaper models for file selection, and larger models for planning/implementation.
- Log and analyze token usage per step to optimize the most expensive calls.

### 5. Workflow & Traceability
- Add structured logs for every agent step, including prompt, output, and token usage.
- Allow resuming from any step, not just the last checkpoint, for faster recovery and debugging.
- Auto-generate detailed PR descriptions summarizing all tasks, code changes, and tests.

### 6. Testing & Quality
- Require a minimum test coverage delta for each PR (integrate with coverage tools).
- Automatically run Playwright and backend tests after generation, and report results in the PR.

### 7. User Experience
- Build a simple dashboard to visualize workflow progress, agent outputs, and logs.
- Allow users to customize which agents/steps are run for each story.

### 8. Security & Safety
- Ensure no secrets or sensitive data are included in LLM prompts or logs.
- Run generated code/tests in a sandboxed environment before committing.

# Recent Updates: Enhanced Workflow with PR/Test Automation

## ✅ Completed Features
- **Enhanced Workflow**: Now persists generated code to `repos/negishi-freelancing` on feature branches
- **Automatic PR Creation**: Creates pull requests with detailed descriptions of changes and tests
- **Comprehensive Testing**: Tester agent generates unit, integration, and Playwright tests automatically
- **Git Operations**: Commits changes incrementally and pushes branches automatically
- **SSH Configuration**: Fixed SSL issues by switching submodule to SSH remote

## Current Status
- Enhanced workflow is fully functional with real Jira/GitHub integration
- All agents (PM, Architect, Developer, Frontend, Reviewer, Tester) are actively engaged
- Generated code and tests are automatically committed and pushed
- Pull requests are created with comprehensive change descriptions

# Next Steps: Modular Developer/Frontend Agent Architecture

## 1. Design a Robust BaseAgent Class
- **Location:** `crewai_app/agents/base.py`
- **Responsibilities:**
  - Common LLM interaction logic (prompting, retries, caching, logging)
  - Output parsing/validation utilities (e.g., code fence stripping, list extraction)
  - Error handling and fallback strategies
  - Collaboration hooks (escalate/route tasks to other agents: frontend, backend, architect, PM)
  - Shared context management (API contracts, UI specs)
- **Extensibility:** Both `DeveloperAgent` (backend) and `FrontendAgent` (Angular) will inherit from this class.

## 2. Implement Specialized Agents
- **Backend (`DeveloperAgent`):**
  - Inherits from `BaseAgent`.
  - Focuses on Python/FastAPI code, backend tests, and API contracts.
- **Frontend (`FrontendAgent`):**
  - Inherits from `BaseAgent`.
  - Focuses on Angular (with Native Federation), TypeScript, HTML, SCSS, and Playwright/Jasmine tests.
  - **Prompt must include:**
    - Angular Native Federation is used.
    - Do **not** upgrade or modify core files (Angular, Native Federation, etc).
    - The shell is in `/shell`; the only module to use is `/freelancer/profile`.
    - `/freelancer/profile` contains components for both freelancer and client.
    - UI components must follow strict design rules for consistent look and feel (see below).
  - **UI Consistency Rules:**
    - Use shared styles/components from a designated shared module.
    - Follow a design system (color palette, spacing, typography).
    - All new components must use the same layout, button, and form field styles as existing ones.
    - Responsive and accessible by default.

## 3. Prompt Engineering
- **Frontend Prompt Additions:**
  - "This project uses Angular Native Federation. Do not upgrade or modify any core Angular or federation files."
  - "The shell is located in `/shell`; only use the `/freelancer/profile` module for new components."
  - "Ensure all UI components follow the shared design system for look and feel consistency."
  - "If backend changes are required, collaborate with the backend agent. If architectural or requirements clarification is needed, escalate to the architect or PM agent."
- **Backend Prompt Additions:**
  - "If frontend changes are required, collaborate with the frontend agent. If requirements are unclear, escalate to the architect or PM agent."

## 4. Collaboration and Escalation
- **Agent Collaboration:**
  - Agents can pass context, API contracts, or UI specs to each other.
  - If a task requires changes outside their domain, they can "escalate" or "handoff" to the appropriate agent (frontend, backend, architect, PM).
  - Collaboration is logged and tracked for traceability.
- **Escalation Triggers:**
  - Unclear requirements, missing API contracts, or design ambiguities.
  - Need for new endpoints or UI elements not covered in the plan.

## 5. Workflow Integration
- **Task Routing:**
  - The workflow routes tasks to the appropriate agent based on file type, directory, or explicit task type.
  - Collaboration/escalation is supported mid-task if needed.
- **Shared Context:**
  - Agents can access and update a shared context object (API contracts, UI specs, design tokens).

## 6. Testing and Documentation
- **Unit and integration tests** for both agents and the base class.
- **Documentation** for:
  - Agent responsibilities and collaboration patterns.
  - UI design system and component structure rules.
  - How to escalate or collaborate between agents.

---

## Deliverables
- `crewai_app/agents/base.py`: BaseAgent class with shared logic and collaboration hooks.
- `crewai_app/agents/developer.py`: Refactored DeveloperAgent (backend) inheriting from BaseAgent.
- `crewai_app/agents/frontend.py`: New FrontendAgent (Angular) inheriting from BaseAgent, with strict prompt and UI rules.
- Updated workflow logic for agent routing and collaboration.
- Tests and documentation.

---

# Implementation Progress Checklist

- [x] Scaffold `BaseAgent` class in `crewai_app/agents/base.py`
- [x] Refactor `DeveloperAgent` to inherit from `BaseAgent`
- [x] Create `FrontendAgent` inheriting from `BaseAgent`
- [x] Implement prompt engineering for frontend/backend agents
- [x] Add UI consistency rules to frontend prompts
- [x] Add agent collaboration and escalation logic
- [ ] Update workflow for agent routing and collaboration (**in progress**)
- [ ] Add unit/integration tests for agents and base class
- [ ] Document agent responsibilities, UI rules, and collaboration patterns

---

# Documentation: Agent Responsibilities, UI Rules, and Collaboration Patterns

## Agent Responsibilities
- **BaseAgent:** Provides LLM interaction, output parsing, error handling, escalation, and shared context utilities for all agents.
- **DeveloperAgent:** Handles backend (Python/FastAPI) code generation, backend test creation, and collaborates/escalates to frontend or architect/PM as needed.
- **FrontendAgent:** Handles Angular (Native Federation) code generation, UI/UX implementation, Playwright/Jasmine test creation, and collaborates/escalates to backend or architect/PM as needed.

## UI Consistency Rules (FrontendAgent)
- Use only the `/freelancer/profile` module for new components.
- Do **not** upgrade or modify core Angular or federation files.
- All UI components must:
  - Use shared styles/components from the shared module.
  - Follow the design system (color palette, spacing, typography).
  - Use the same layout, button, and form field styles as existing components.
  - Be responsive and accessible by default.

## Collaboration & Escalation Patterns
- Agents can escalate tasks to each other (e.g., backend to frontend, frontend to backend, either to architect/PM) using `escalate_to_*` methods.
- All escalations and collaboration requests are logged for traceability.
- Shared context is used to pass API contracts, UI specs, or requirements between agents.
- If requirements or design are unclear, escalate to architect/PM for clarification.

---

## Running the Workflow

To run the workflow, use the following command from the project root:

```
python3 -m crewai_app.main --workflow story_implementation --story <STORY_ID> --log-level INFO
```

This ensures Python treats `crewai_app` as a package and avoids `ModuleNotFoundError: No module named 'crewai_app'`. 

## Next Priority: Integrate Frontend Agent into Workflow

### Improved Plan: Explicit Backend/Frontend Task Breakdown and Routing

1. **Architect/PM Plan:**
   - Architect/PM should structure the implementation plan with explicit sections for backend and frontend work.
   - Update the architect/PM prompt to encourage this separation.
2. **Agent-Specific Task Breakdown:**
   - After the plan, call `DeveloperAgent.break_down_story` for backend tasks and `FrontendAgent.break_down_story` for frontend tasks, each using the relevant section of the plan.
   - Store two separate task lists: `backend_tasks` and `frontend_tasks`.
3. **Parallel Implementation:**
   - For each backend task, call `DeveloperAgent.implement_task` and commit files.
   - For each frontend task, call `FrontendAgent.implement_task` and commit files.
   - Handle testing/review as appropriate for each.
4. **Logging/Debugging:**
   - Ensure logs/prints confirm agent execution and LLM usage for both backend and frontend.

--- 