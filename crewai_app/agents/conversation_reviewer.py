"""
Conversation Reviewer Agent

Thin wrapper around OpenAIService to request a conversation/codebase review
and return structured recommendations.
"""
from __future__ import annotations

from typing import Dict, Any
from crewai_app.services.conversation_review_service import ConversationReviewService


class ConversationReviewerAgent:
    def __init__(self, review_service: ConversationReviewService | None = None) -> None:
        self.service = review_service or ConversationReviewService()

    def analyze_workflow(self, workflow_id: int) -> Dict[str, Any]:
        return self.service.review(workflow_id)



