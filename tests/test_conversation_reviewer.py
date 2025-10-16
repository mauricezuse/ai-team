import json
from typing import Any, Dict

from crewai_app.services.conversation_review_service import ConversationReviewService


class DummyOpenAI:
    def generate(self, prompt: str, step: str = "") -> str:
        # Return deterministic JSON for testing
        obj: Dict[str, Any] = {
            "summary": "Test summary",
            "workflow_recommendations": [{"title": "Join steps", "description": "Merge planner + architect."}],
            "prompt_recommendations": [{"agent": "developer", "current_issue": "Too verbose", "suggestion": "Tighten prompts"}],
            "code_change_suggestions": [{
                "path": "crewai_app/agents/developer.py",
                "section": "function break_down_story",
                "change_type": "edit",
                "before_summary": "No guard",
                "after_summary": "Guard for empty plan",
                "patch_outline": "Add early return if plan is empty"
            }],
            "risk_flags": ["token usage high"],
            "quick_wins": ["reduce retries"],
            "estimated_savings": {"messages": 10, "cost_usd": 1.2, "duration_minutes": 5}
        }
        return json.dumps(obj)


def test_review_service_parses_json(monkeypatch):
    svc = ConversationReviewService()
    # Inject dummy openai
    svc.openai = DummyOpenAI()

    # Minimal fake: build prompt and parse
    conversations = {"workflow": {"id": 1, "name": "WF", "status": "completed"}, "conversations": []}
    codebase_guide = {"entries": []}
    prompt = svc.build_review_prompt(1, conversations, codebase_guide, coding_rules="")
    assert "SYSTEM" in prompt

    out = svc._parse_review_output(svc.openai.generate(prompt))
    assert out["summary"] == "Test summary"
    assert out["code_change_suggestions"][0]["path"].startswith("crewai_app/")


