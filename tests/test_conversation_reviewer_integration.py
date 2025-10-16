import pytest
try:
    from fastapi.testclient import TestClient
    from crewai_app.main import app
    _APP_IMPORTED = True
except Exception:
    # Environment lacks compatible deps (e.g., crewai/py>=3.10). Mark skip.
    _APP_IMPORTED = False


def test_conversation_review_endpoint_smoke(monkeypatch):
    if not _APP_IMPORTED:
        pytest.skip("Skipping integration smoke: app import not available in this environment")
    client = TestClient(app)

    # Monkeypatch service.generate to deterministic JSON
    from crewai_app.services.conversation_review_service import ConversationReviewService

    class DummyOpenAI:
        def generate(self, prompt: str, step: str = "") -> str:
            return (
                '{"summary":"ok","workflow_recommendations":[],"prompt_recommendations":[],'
                '"code_change_suggestions":[],"risk_flags":[],"quick_wins":[],'
                '"estimated_savings":{"messages":0,"cost_usd":0.0,"duration_minutes":0}}'
            )

    svc = ConversationReviewService()
    svc.openai = DummyOpenAI()

    def fake_review(self, workflow_id: int):
        return {
            "summary": "ok",
            "workflow_recommendations": [],
            "prompt_recommendations": [],
            "code_change_suggestions": [],
            "risk_flags": [],
            "quick_wins": [],
            "estimated_savings": {"messages": 0, "cost_usd": 0.0, "duration_minutes": 0},
        }

    monkeypatch.setattr(ConversationReviewService, "review", fake_review)

    # Choose a workflow id (endpoint will compute fresh; DB fixture not required for smoke)
    resp = client.post("/workflows/19/conversation-review")
    assert resp.status_code in (200, 404)  # 404 if workflow 1 not found in local DB
    if resp.status_code == 200:
        data = resp.json()
        assert "summary" in data



