# Conversation Reviewer Feature (MINIONS-4-conversation-reviewer)

## Goals
- Analyze all conversations for a given workflow.
- Use an LLM to review inter-agent interactions and prompts.
- Suggest actionable optimizations for workflow design and prompt engineering.
- Introduce a dedicated Reviewer Agent with full understanding of the AI Team system and codebase.

## Deliverables
- Agent: `ConversationReviewerAgent`
- Service: `ConversationReviewService`
- API: `GET/POST /workflows/{id}/conversation-review`
- Schemas: Pydantic response model
- Tests: Unit + integration tests
- Docs: `crewai_app/README.md` update and API docs

## Codebase Awareness
- Build a compact "Codebase Guide" on-the-fly:
  - High-level docs from `docs/` and `crewai_app/README.md`
  - Directory map of `crewai_app/{agents,services,workflows,utils}`, `frontend/src/app/**`, `tests/**`
  - Key file summaries: first lines and exported classes/functions (bounded)
- Include `coding_rules.yaml` excerpt
- Provide this context to the agent as part of the system/context messages

## Review Output Schema
```json
{
  "summary": "string",
  "workflow_recommendations": [
    {"title": "...", "description": "...", "priority": "high|medium|low", "impact": "high|medium|low", "effort": "high|medium|low", "example_change": "..."}
  ],
  "prompt_recommendations": [
    {"agent": "developer|frontend|...", "current_issue": "...", "suggestion": "...", "example_before": "...", "example_after": "..."}
  ],
  "code_change_suggestions": [
    {"path": "crewai_app/agents/developer.py", "section": "function break_down_story", "change_type": "edit|add|remove", "before_summary": "...", "after_summary": "...", "patch_outline": "..."}
  ],
  "risk_flags": ["..."],
  "quick_wins": ["..."],
  "estimated_savings": {"messages": 0, "cost_usd": 0.0, "duration_minutes": 0}
}
```

## Prompt Construction
- System prompt: expertise in AI orchestration and this repository, strict about file paths and minimal edits, follow coding_rules.yaml.
- Provide: conversation timeline (summarized), agent roles, workflow structure, codebase guide, token/cost summaries.
- Ask for: workflow/prompt improvements + explicit code_change_suggestions with file paths.

## Components
### ConversationReviewService
- `collect_workflow_conversations(workflow_id)`
- `build_codebase_guide()`
- `build_review_prompt(workflow_id)`
- `review(workflow_id)` -> structured JSON

### ConversationReviewerAgent
- Uses `OpenAIService.generate()` with robust step name and tracking
- Validates/parses JSON; tolerant to non-JSON returns

### API Endpoints (FastAPI)
- `POST /workflows/{id}/conversation-review`: trigger review, return JSON
- `GET /workflows/{id}/conversation-review`: return last generated review (optional cache; initially stateless)

## Tests
- Unit: prompt builder, codebase guide builder, JSON parsing
- Integration: end-to-end with mock OpenAIService returning deterministic JSON; verify endpoints
- Edge: no conversations; token truncation path; non-JSON model output

## Execution Plan
1) Implement service + agent
2) Wire endpoints in `crewai_app/main.py`
3) Add tests (unit + integration)
4) Update `crewai_app/README.md`
5) Commit in small batches and open PR
