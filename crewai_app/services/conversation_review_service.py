"""
Conversation Review Service

Collects workflow conversations and a compact, codebase-aware guide, builds an
LLM prompt, invokes the model (via OpenAIService), and returns structured
recommendations including workflow, prompt engineering, and concrete
code-change suggestions that reference exact file paths in this repository.
"""
from __future__ import annotations

import os
import json
from typing import Dict, Any, List, Optional

from crewai_app.database import get_db, Workflow, Conversation, Message
from crewai_app.services.openai_service import OpenAIService
from crewai_app.utils.logger import logger


class ConversationReviewService:
    def __init__(self, openai_service: Optional[OpenAIService] = None) -> None:
        self.openai = openai_service or OpenAIService()

    # ---- Public API ----
    def review(self, workflow_id: int) -> Dict[str, Any]:
        conversations = self.collect_workflow_conversations(workflow_id)
        codebase_guide = self.build_codebase_guide(max_files=60, max_lines=40)
        coding_rules = self._load_coding_rules_excerpt(max_lines=150)

        prompt = self.build_review_prompt(
            workflow_id=workflow_id,
            conversations=conversations,
            codebase_guide=codebase_guide,
            coding_rules=coding_rules,
        )

        logger.info("[ConversationReviewService] Sending prompt for workflow %s", workflow_id)
        raw = self.openai.generate(
            prompt,
            step="conversation_reviewer.review"
        )
        return self._parse_review_output(raw)

    # ---- Data collection ----
    def collect_workflow_conversations(self, workflow_id: int) -> Dict[str, Any]:
        """Return normalized conversations/messages payload for the workflow."""
        db = next(get_db())
        wf = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not wf:
            return {"workflow_id": workflow_id, "conversations": []}
        rows = db.query(Conversation).filter(Conversation.workflow_id == workflow_id).all()
        out: List[Dict[str, Any]] = []
        for c in rows:
            msgs = db.query(Message).filter(Message.conversation_id == c.id).order_by(Message.id.asc()).all()
            out.append({
                "id": c.id,
                "agent": c.agent or "",
                "step": c.step or "",
                "status": c.status or "",
                "timestamp": c.timestamp.isoformat() if c.timestamp else None,
                "messages": [
                    {
                        "id": m.id,
                        "role": m.role,
                        "content": (m.content or "")[:2000],
                        "created_at": (m.message_metadata or {}).get("created_at"),
                    }
                    for m in msgs
                ],
                "total_tokens_used": c.total_tokens_used or 0,
                "total_cost": c.total_cost or "0.00",
            })
        return {"workflow": {"id": wf.id, "name": wf.name, "status": wf.status}, "conversations": out}

    # ---- Codebase awareness ----
    def build_codebase_guide(self, max_files: int = 60, max_lines: int = 40) -> Dict[str, Any]:
        """Build a compact map of key directories and file heads to give the model
        adequate context without exceeding token budgets."""
        roots = [
            "crewai_app/agents",
            "crewai_app/services",
            "crewai_app/workflows",
            "crewai_app/utils",
            "frontend/src/app",
            "tests",
        ]
        files: List[str] = []
        for root in roots:
            if not os.path.isdir(root):
                continue
            for dirpath, _dirnames, filenames in os.walk(root):
                for fn in filenames:
                    # Skip node_modules and big assets by default
                    if fn.endswith((".py", ".ts", ".html", ".scss", ".md")):
                        files.append(os.path.join(dirpath, fn))
        files = sorted(files)[:max_files]
        entries: List[Dict[str, Any]] = []
        for path in files:
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    head = "".join([next(f) for _ in range(max_lines)])
            except StopIteration:
                # File shorter than max_lines
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    head = f.read()
            except Exception:
                head = ""
            entries.append({"path": path, "head": head})
        return {"entries": entries}

    def _load_coding_rules_excerpt(self, max_lines: int = 150) -> str:
        path = "coding_rules.yaml"
        if not os.path.exists(path):
            return ""
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines: List[str] = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    lines.append(line)
                return "".join(lines)
        except Exception:
            return ""

    # ---- Prompting ----
    def build_review_prompt(
        self,
        workflow_id: int,
        conversations: Dict[str, Any],
        codebase_guide: Dict[str, Any],
        coding_rules: str,
    ) -> str:
        system = (
            "You are an expert AI workflow auditor for the AI Team project (CrewAI Orchestration).\n"
            "You know this repository layout and must provide minimal, high-impact suggestions.\n"
            "You MUST output strict JSON with keys: summary, workflow_recommendations, prompt_recommendations,\n"
            "code_change_suggestions, risk_flags, quick_wins, estimated_savings.\n"
            "All code changes must reference exact file paths and sections, and follow coding rules.\n"
        )
        guide = {
            "workflow_id": workflow_id,
            "coding_rules_excerpt": coding_rules,
            "codebase_guide": codebase_guide,
            "conversations": conversations,
        }
        prompt = (
            f"SYSTEM:\n{system}\n\n"
            "TASK: Review the following conversations and codebase context, then return JSON as specified.\n"
            "Focus on: (1) workflow optimizations (steps/agents), (2) prompt engineering, (3) code_change_suggestions.\n\n"
            f"CONTEXT:\n{json.dumps(guide)[:140000]}\n\n"
            "Return only JSON, no extra commentary."
        )
        return prompt

    # ---- Parsing ----
    def _parse_review_output(self, raw: str) -> Dict[str, Any]:
        try:
            obj = json.loads(raw)
            return self._ensure_schema(obj)
        except Exception:
            # Best-effort JSON extraction from text
            start = raw.find("{")
            end = raw.rfind("}")
            if start >= 0 and end > start:
                try:
                    obj = json.loads(raw[start : end + 1])
                    return self._ensure_schema(obj)
                except Exception:
                    pass
        # Fallback minimal structure
        return self._ensure_schema({"summary": "No structured output returned."})

    def _ensure_schema(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        def _list(val: Any) -> List[Any]:
            return val if isinstance(val, list) else []
        out = {
            "summary": obj.get("summary", ""),
            "workflow_recommendations": _list(obj.get("workflow_recommendations")),
            "prompt_recommendations": _list(obj.get("prompt_recommendations")),
            "code_change_suggestions": _list(obj.get("code_change_suggestions")),
            "risk_flags": _list(obj.get("risk_flags")),
            "quick_wins": _list(obj.get("quick_wins")),
            "estimated_savings": obj.get("estimated_savings", {"messages": 0, "cost_usd": 0.0, "duration_minutes": 0}),
        }
        return out


