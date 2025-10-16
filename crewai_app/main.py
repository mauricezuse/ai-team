from fastapi import FastAPI, Body, HTTPException, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import String
import argparse
import sys
import os
import json
import glob
import asyncio
from datetime import datetime
from crewai_app.workflows.planning_workflow import run_planning_and_design, generate_stories, gap_analysis
from crewai_app.workflows.implementation_workflow import implement_stories_with_tests
from crewai_app.workflows.story_implementation_workflow import StoryImplementationWorkflow
from crewai_app.workflows.enhanced_story_workflow import EnhancedStoryWorkflow
from crewai_app.config import settings
from crewai_app.database import get_db, init_database, Workflow, Conversation, CodeFile, Escalation, Collaboration
from crewai_app.database import LLMCall
from crewai_app.database import Execution
from crewai_app.utils.feature_flags import FeatureFlags
from crewai_app.services.workflow_status_service import workflow_status_service

app = FastAPI(title="CrewAI Orchestration Platform")
flags = FeatureFlags()

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_database()

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:3000", "http://minions.localhost:4200"],  # Angular dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API
class WorkflowCreate(BaseModel):
    jira_story_id: str
    jira_story_title: str
    jira_story_description: str
    repository_url: str = "https://github.com/mauricezuse/negishi-freelancing"
    target_branch: str = "main"

class WorkflowResponse(BaseModel):
    id: int
    name: str
    jira_story_id: str
    jira_story_title: str
    jira_story_description: str
    status: str
    created_at: datetime
    updated_at: datetime
    repository_url: str
    target_branch: str
    conversations: List[Dict] = []
    code_files: List[Dict] = []
    
    # Enhanced status fields
    isTerminal: bool = False
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None
    last_heartbeat_at: Optional[datetime] = None
    heartbeat_stale: bool = False

    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    id: int
    step: str
    timestamp: datetime
    agent: str
    status: str
    details: Optional[str]
    output: Optional[str]
    prompt: Optional[str]
    code_files: List[Dict] = []
    escalations: List[Dict] = []
    collaborations: List[Dict] = []
    llm_calls: Optional[List[Dict]] = []
    total_tokens_used: Optional[int] = 0
    total_cost: Optional[str] = "0.00"

    class Config:
        from_attributes = True

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/conversations/{conversation_id}/llm-calls")
def get_conversation_llm_calls(
    conversation_id: int,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    sort_by: str = Query("timestamp"),
    sort_dir: str = Query("desc"),
    model: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    """Return LLM calls for a conversation with usage and cost, with pagination and filters."""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Prefer normalized rows if any exist
    query = db.query(LLMCall).filter(LLMCall.conversation_id == conversation_id)

    # Apply filters
    if model:
        query = query.filter(LLMCall.model == model)
    if q:
        # basic search in request/response payloads (JSON serialized cast)
        # Note: SQLite JSON search is limited; fallback to LIKE on stringified JSON
        query = query.filter(
            (LLMCall.request_data.cast(String).like(f"%{q}%")) | (LLMCall.response_data.cast(String).like(f"%{q}%"))
        )
    # Date range filters
    from datetime import datetime as _dt
    def _parse_dt(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return _dt.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return None
    df = _parse_dt(date_from)
    dt = _parse_dt(date_to)
    if df:
        query = query.filter(LLMCall.timestamp >= df)
    if dt:
        query = query.filter(LLMCall.timestamp <= dt)

    # Sorting
    sortable = {
        "timestamp": LLMCall.timestamp,
        "model": LLMCall.model,
        "total_tokens": LLMCall.total_tokens,
        "response_time_ms": LLMCall.response_time_ms,
        "cost": LLMCall.cost,
        "id": LLMCall.id,
    }
    order_col = sortable.get(sort_by, LLMCall.timestamp)
    if (sort_dir or "").lower() == "asc":
        query = query.order_by(order_col.asc())
    else:
        query = query.order_by(order_col.desc())

    # Pagination
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    if items:
        def _maybe_redact(call: Dict[str, Any]) -> Dict[str, Any]:
            if flags.is_enabled('REDACT_SENSITIVE', False):
                # Remove/obfuscate potentially sensitive payloads
                redacted = dict(call)
                if 'request_data' in redacted:
                    redacted['request_data'] = {'redacted': True}
                if 'response_data' in redacted:
                    redacted['response_data'] = {'redacted': True}
                return redacted
            return call
        return {
            "conversation_id": conversation_id,
            "total_tokens_used": conversation.total_tokens_used or 0,
            "total_cost": conversation.total_cost or "0.00",
            "page": page,
            "page_size": page_size,
            "total": total,
            "calls": [
                _maybe_redact({
                    "id": row.id,
                    "model": row.model,
                    "prompt_tokens": row.prompt_tokens,
                    "completion_tokens": row.completion_tokens,
                    "total_tokens": row.total_tokens,
                    "cost": row.cost,
                    "response_time_ms": row.response_time_ms,
                    "timestamp": row.timestamp,
                    "request_data": row.request_data,
                    "response_data": row.response_data,
                })
                for row in items
            ],
        }

    # Fallback to JSON in conversation.llm_calls
    llm_calls_data = []
    if conversation.llm_calls:
        try:
            if isinstance(conversation.llm_calls, str):
                llm_calls_data = json.loads(conversation.llm_calls)
            else:
                llm_calls_data = conversation.llm_calls
        except (json.JSONDecodeError, TypeError):
            llm_calls_data = []

    def _maybe_redact_json_list(calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not flags.is_enabled('REDACT_SENSITIVE', False):
            return calls
        out: List[Dict[str, Any]] = []
        for c in calls:
            red = dict(c)
            if 'request_data' in red:
                red['request_data'] = {'redacted': True}
            if 'response_data' in red:
                red['response_data'] = {'redacted': True}
            out.append(red)
        return out

    return {
        "conversation_id": conversation_id,
        "total_tokens_used": conversation.total_tokens_used or 0,
        "total_cost": conversation.total_cost or "0.00",
        "page": 1,
        "page_size": len(llm_calls_data),
        "total": len(llm_calls_data),
        "calls": _maybe_redact_json_list(llm_calls_data),
    }

@app.get("/workflows/{workflow_id}/compare")
def compare_workflows(workflow_id: int, with_id: int = Query(..., alias="with"), db: Session = Depends(get_db)):
    """Compare two workflow runs and return aggregate metrics and deltas."""
    def aggregate(wid: int) -> Dict[str, Any]:
        # Validate workflow exists
        wf = db.query(Workflow).filter(Workflow.id == wid).first()
        if not wf:
            raise HTTPException(status_code=404, detail=f"Workflow {wid} not found")
        # Join conversations -> llm_calls
        from sqlalchemy import func
        conv_ids = [c.id for c in db.query(Conversation.id).filter(Conversation.workflow_id == wid).all()]
        if not conv_ids:
            return {
                "workflow_id": wid,
                "total_calls": 0,
                "total_tokens": 0,
                "total_cost": "0.0000",
                "avg_latency_ms": 0,
                "models": {},
            }
        totals = db.query(
            func.count(LLMCall.id),
            func.coalesce(func.sum(LLMCall.total_tokens), 0),
            func.coalesce(func.sum(func.cast(LLMCall.cost, String)), "0.0000"),
            func.coalesce(func.avg(LLMCall.response_time_ms), 0),
        ).filter(LLMCall.conversation_id.in_(conv_ids)).one()

        # Model breakdown
        rows = db.query(LLMCall.model, func.count(LLMCall.id)).\
            filter(LLMCall.conversation_id.in_(conv_ids)).group_by(LLMCall.model).all()
        model_map: Dict[str, int] = {m or "unknown": c for m, c in rows}
        # Compute numeric cost sum from string
        try:
            cost_sum = float(totals[2]) if isinstance(totals[2], str) else float(totals[2] or 0)
        except Exception:
            cost_sum = 0.0
        return {
            "workflow_id": wid,
            "total_calls": int(totals[0] or 0),
            "total_tokens": int(totals[1] or 0),
            "total_cost": f"{cost_sum:.4f}",
            "avg_latency_ms": int(totals[3] or 0),
            "models": model_map,
        }

    left = aggregate(workflow_id)
    right = aggregate(with_id)

    def delta(a, b):
        return {k: (b.get(k) - a.get(k) if isinstance(a.get(k), (int, float)) and isinstance(b.get(k), (int, float)) else None) for k in ["total_calls", "total_tokens", "avg_latency_ms"]}

    return {
        "left": left,
        "right": right,
        "deltas": delta(left, right),
    }

# New workflow management endpoints
@app.get("/workflows")
def get_workflows(db: Session = Depends(get_db)):
    """List workflows from the database (numeric IDs)."""
    workflows = db.query(Workflow).all()
    return [
        {
            "id": w.id,
            "name": w.name,
            "jira_story_id": w.jira_story_id,
            "jira_story_title": w.jira_story_title,
            "jira_story_description": w.jira_story_description or "",
            "status": w.status,
            "created_at": w.created_at,
            "updated_at": w.updated_at,
            "repository_url": w.repository_url,
            "target_branch": w.target_branch,
            "conversations": [],
            "code_files": [],
            # Enhanced status fields
            "isTerminal": w.status in ["completed", "failed", "cancelled"],
            "started_at": w.started_at,
            "finished_at": w.finished_at,
            "error": w.error,
            "last_heartbeat_at": w.last_heartbeat_at,
            "heartbeat_stale": w.last_heartbeat_at and w.status == "running" and 
                              (datetime.utcnow() - w.last_heartbeat_at).total_seconds() > 300
        }
        for w in workflows
    ]

@app.get("/workflows/{workflow_id:int}", response_model=WorkflowResponse)
def get_workflow_db(workflow_id: int, db: Session = Depends(get_db), if_none_match: Optional[str] = None):
    """Get a specific workflow with all its data"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Get enhanced status information
    status_info = workflow_status_service.get_workflow_status_info(workflow_id)
    
    # Generate ETag for caching
    etag = f'"{workflow.updated_at.isoformat()}-{workflow.status}"'
    
    # Check if client has current version
    if if_none_match and if_none_match == etag:
        from fastapi import Response
        return Response(status_code=304)
    
    # Get conversations with related data
    conversations = db.query(Conversation).filter(Conversation.workflow_id == workflow_id).all()
    workflow_data = {
        "id": workflow.id,
        "name": workflow.name,
        "jira_story_id": workflow.jira_story_id,
        "jira_story_title": workflow.jira_story_title or "",
        "jira_story_description": workflow.jira_story_description or "",
        "status": workflow.status,
        "created_at": workflow.created_at,
        "updated_at": workflow.updated_at,
        "repository_url": workflow.repository_url or "",
        "target_branch": workflow.target_branch or "",
        "conversations": [],
        # Enhanced status fields
        "isTerminal": status_info.get("isTerminal", False),
        "started_at": workflow.started_at,
        "finished_at": workflow.finished_at,
        "error": workflow.error,
        "last_heartbeat_at": workflow.last_heartbeat_at,
        "heartbeat_stale": status_info.get("heartbeat_stale", False)
    }
    
    # Map common workflow steps to agent ids for better display when agent is missing
    step_to_agent = {
        "story_retrieved_and_analyzed": "pm",
        "story_analysis": "pm",
        "architecture_design": "architect",
        "implementation_plan_generated": "architect",
        "tasks_broken_down_with_collaboration": "architect",
        "codebase_indexed": "developer",
        "implementation": "developer",
        "tasks_executed_with_escalation": "developer",
        "frontend_implementation": "frontend",
        "final_review_and_testing_completed": "tester",
        "pr_skipped": "reviewer",
    }
    
    # Map agent IDs to proper display names
    agent_display_names = {
        "pm": "Product Manager",
        "architect": "Solution Architect", 
        "developer": "Backend Developer",
        "frontend": "Frontend Developer",
        "tester": "QA Tester",
        "reviewer": "Code Reviewer"
    }

    for conv in conversations:
        # Get code files for this conversation
        code_files = db.query(CodeFile).filter(CodeFile.conversation_id == conv.id).all()
        # Get escalations and collaborations
        escalations = db.query(Escalation).filter(Escalation.conversation_id == conv.id).all()
        collaborations = db.query(Collaboration).filter(Collaboration.conversation_id == conv.id).all()
        
        # Infer agent if missing
        inferred_agent = conv.agent or step_to_agent.get((conv.step or "").strip().lower(), "")
        # Convert agent ID to display name
        agent_display_name = agent_display_names.get(inferred_agent, inferred_agent)

        # Parse LLM calls from JSON if available
        llm_calls_data = []
        if conv.llm_calls:
            try:
                if isinstance(conv.llm_calls, str):
                    llm_calls_data = json.loads(conv.llm_calls)
                else:
                    llm_calls_data = conv.llm_calls
            except (json.JSONDecodeError, TypeError):
                llm_calls_data = []

        conv_data = {
            "id": conv.id,
            "step": conv.step or "",
            "timestamp": conv.timestamp,
            "agent": agent_display_name,
            "status": conv.status or "",
            "details": conv.details or "",
            "output": conv.output or "",
            "prompt": conv.prompt or "",
            "code_files": [{"filename": cf.filename, "file_path": cf.file_path} for cf in code_files],
            "escalations": [{"from_agent": e.from_agent, "to_agent": e.to_agent, "reason": e.reason, "status": e.status} for e in escalations],
            "collaborations": [{"from_agent": c.from_agent, "to_agent": c.to_agent, "request_type": c.request_type, "status": c.status} for c in collaborations],
            "llm_calls": llm_calls_data,
            "total_tokens_used": conv.total_tokens_used or 0,
            "total_cost": conv.total_cost or "0.00"
        }
        workflow_data["conversations"].append(conv_data)
    
    return workflow_data

@app.get("/workflows/{workflow_id}")
def get_workflow_file(workflow_id: str):
    """Legacy file-based workflow detail used in tests."""
    try:
        results_dir = "workflow_results"
        if not os.path.exists(results_dir):
            raise HTTPException(status_code=404, detail="Workflow not found")
        path = os.path.join(results_dir, f"{workflow_id}_checkpoint.json")
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Workflow not found")
        with open(path, "r") as f:
            data = json.load(f)
        # Build minimal response structure expected by tests
        workflow_data = {
            "id": workflow_id,
            "name": (workflow_id.replace("_", " ").title() if workflow_id else "Workflow"),
            "status": "completed",
            "conversations": [],
        }
        log = data.get("workflow_log", [])
        for entry in log:
            workflow_data["conversations"].append({
                "step": entry.get("step", ""),
                "agent": entry.get("agent", ""),
                "timestamp": entry.get("timestamp", ""),
                "status": entry.get("status", ""),
                "details": entry.get("details", ""),
                "output": entry.get("output", ""),
                "code_files": entry.get("code_files", []),
                "escalations": entry.get("escalations", []),
                "collaborations": entry.get("collaborations", []),
            })
        return workflow_data
    except IOError:
        raise HTTPException(status_code=500, detail="Error reading workflow file")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"Error reading workflow: {e}")

@app.post("/workflows", response_model=WorkflowResponse)
def create_workflow(workflow_data: WorkflowCreate, db: Session = Depends(get_db)):
    """Create a new workflow from a Jira story"""
    # Check if workflow already exists
    existing = db.query(Workflow).filter(Workflow.jira_story_id == workflow_data.jira_story_id).first()
    if existing:
        # Return the existing workflow to make operation idempotent for UI/tests
        return existing
    
    # Create new workflow
    workflow = Workflow(
        name=f"{workflow_data.jira_story_id}: {workflow_data.jira_story_title}",
        jira_story_id=workflow_data.jira_story_id,
        jira_story_title=workflow_data.jira_story_title,
        jira_story_description=workflow_data.jira_story_description,
        repository_url=workflow_data.repository_url,
        target_branch=workflow_data.target_branch,
        status="pending"
    )
    
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    
    return workflow

@app.post("/workflows/{workflow_id:int}/execute")
def execute_workflow(workflow_id: int, db: Session = Depends(get_db)):
    """Execute a workflow in the background (non-blocking)"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Check if workflow is already running
    if workflow.status == "running":
        return {
            "message": "Workflow is already running",
            "workflow_id": workflow_id,
            "status": "running"
        }
    
    # Start background execution
    from crewai_app.services.workflow_executor import workflow_executor
    result = workflow_executor.execute_workflow_async(workflow_id)
    
    return result

@app.post("/workflows/{workflow_id}/execute")
def execute_workflow_file(workflow_id: str, story_id: Optional[str] = Query(None)):
    """Legacy execute endpoint for string workflow ids used in tests."""
    try:
        sid = story_id or (workflow_id.split("_")[-1] if workflow_id else None)
        wf = EnhancedStoryWorkflow(story_id=sid, use_real_jira=True, use_real_github=True, codebase_root=None, user_intervention_mode=False)
        results = wf.run()
        return {
            "message": "Workflow executed successfully",
            "workflow_id": workflow_id,
            "story_id": sid,
            "status": "completed",
            "results": results,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error executing workflow")

@app.get("/workflows/{workflow_id}/status")
def get_workflow_status(workflow_id: int):
    """Get the current status of a workflow execution"""
    return workflow_status_service.get_workflow_status_info(workflow_id)

@app.get("/workflows/status/running")
def get_running_workflows():
    """Get all currently running workflows"""
    from crewai_app.services.workflow_executor import workflow_executor
    return workflow_executor.get_running_workflows()

@app.post("/workflows/{workflow_id}/reconcile")
def reconcile_workflow_status(workflow_id: int):
    """Manually reconcile workflow status based on heartbeat"""
    success = workflow_status_service.reconcile_workflow_status(workflow_id)
    if success:
        return {"message": "Workflow status reconciled", "workflow_id": workflow_id}
    else:
        raise HTTPException(status_code=404, detail="Workflow not found or reconciliation failed")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, workflow_id: int):
        await websocket.accept()
        if workflow_id not in self.active_connections:
            self.active_connections[workflow_id] = []
        self.active_connections[workflow_id].append(websocket)

    def disconnect(self, websocket: WebSocket, workflow_id: int):
        if workflow_id in self.active_connections:
            self.active_connections[workflow_id].remove(websocket)
            if not self.active_connections[workflow_id]:
                del self.active_connections[workflow_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast_to_workflow(self, message: str, workflow_id: int):
        if workflow_id in self.active_connections:
            for connection in self.active_connections[workflow_id]:
                try:
                    await connection.send_text(message)
                except:
                    # Remove dead connections
                    self.active_connections[workflow_id].remove(connection)

manager = ConnectionManager()

@app.websocket("/ws/workflows/{workflow_id}")
async def websocket_endpoint(websocket: WebSocket, workflow_id: int):
    """WebSocket endpoint for real-time workflow status updates"""
    await manager.connect(websocket, workflow_id)
    try:
        # Send initial status
        status_info = workflow_status_service.get_workflow_status_info(workflow_id)
        await manager.send_personal_message(json.dumps(status_info), websocket)
        
        # Keep connection alive and send periodic updates
        while True:
            await asyncio.sleep(5)  # Check every 5 seconds
            status_info = workflow_status_service.get_workflow_status_info(workflow_id)
            await manager.send_personal_message(json.dumps(status_info), websocket)
            
            # If terminal, send final update and close
            if status_info.get("isTerminal", False):
                await manager.send_personal_message(json.dumps(status_info), websocket)
                break
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, workflow_id)

@app.get("/events/workflows/{workflow_id}")
async def sse_endpoint(workflow_id: int):
    """Server-Sent Events endpoint for real-time workflow status updates"""
    async def event_generator():
        while True:
            status_info = workflow_status_service.get_workflow_status_info(workflow_id)
            yield f"data: {json.dumps(status_info)}\n\n"
            
            # If terminal, send final update and stop
            if status_info.get("isTerminal", False):
                yield f"data: {json.dumps(status_info)}\n\n"
                break
                
            await asyncio.sleep(5)  # Check every 5 seconds
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

# --- Executions API ---
class ExecutionResponse(BaseModel):
    id: int
    workflow_id: int
    status: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    total_calls: int = 0
    total_tokens: int = 0
    total_cost: str = "0.00"
    avg_latency_ms: int = 0
    models: List[str] = []
    meta: Dict[str, Any] = {}

    class Config:
        from_attributes = True

@app.get("/workflows/{workflow_id:int}/executions", response_model=List[ExecutionResponse])
def list_executions(workflow_id: int, db: Session = Depends(get_db)):
    wf = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    execs = db.query(Execution).filter(Execution.workflow_id == workflow_id).order_by(Execution.started_at.desc()).all()
    return execs

@app.get("/workflows/{workflow_id:int}/executions/{execution_id:int}", response_model=ExecutionResponse)
def get_execution(workflow_id: int, execution_id: int, db: Session = Depends(get_db)):
    ex = db.query(Execution).filter(Execution.id == execution_id, Execution.workflow_id == workflow_id).first()
    if not ex:
        raise HTTPException(status_code=404, detail="Execution not found")
    return ex

@app.post("/workflows/{workflow_id:int}/executions/start", response_model=ExecutionResponse)
def start_execution(workflow_id: int, db: Session = Depends(get_db)):
    wf = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    ex = Execution(workflow_id=workflow_id, status="running", started_at=datetime.utcnow())
    db.add(ex)
    db.commit()
    db.refresh(ex)
    # Kick background executor
    from crewai_app.services.workflow_executor import workflow_executor
    workflow_executor.execute_workflow_async(workflow_id, execution_id=ex.id)
    return ex

@app.get("/workflows/{workflow_id:int}/executions/compare")
def compare_executions(workflow_id: int, execA: int = Query(...), execB: int = Query(...), db: Session = Depends(get_db)):
    def get_exec(ex_id: int) -> Execution:
        ex = db.query(Execution).filter(Execution.id == ex_id, Execution.workflow_id == workflow_id).first()
        if not ex:
            raise HTTPException(status_code=404, detail=f"Execution {ex_id} not found")
        return ex
    a = get_exec(execA)
    b = get_exec(execB)
    def to_dict(e: Execution):
        return {
            "id": e.id,
            "workflow_id": e.workflow_id,
            "total_calls": e.total_calls or 0,
            "total_tokens": e.total_tokens or 0,
            "total_cost": e.total_cost or "0.00",
            "avg_latency_ms": e.avg_latency_ms or 0,
            "models": e.models or [],
        }
    left = to_dict(a)
    right = to_dict(b)
    deltas = {
        "total_calls": (right["total_calls"] - left["total_calls"]),
        "total_tokens": (right["total_tokens"] - left["total_tokens"]),
        "avg_latency_ms": (right["avg_latency_ms"] - left["avg_latency_ms"]),
    }
    return {"left": left, "right": right, "deltas": deltas}

@app.post("/workflows/from-jira/{story_id}")
def create_workflow_from_jira(story_id: str, db: Session = Depends(get_db)):
    """Create a workflow from an existing Jira story"""
    try:
        # Check if workflow already exists
        existing = db.query(Workflow).filter(Workflow.jira_story_id == story_id).first()
        if existing:
            return {"message": f"Workflow created successfully for {story_id}", "workflow_id": existing.id}
        
        # Pull story details from Jira
        from crewai_app.services.jira_service import JiraService
        
        try:
            # Production mode: always use real Jira integration
            jira_service = JiraService(use_real=True)
            story_data = jira_service.get_story(story_id)
            
            if not story_data:
                raise HTTPException(status_code=404, detail={"message": f"Could not retrieve story {story_id} from Jira"})
        except Exception as e:
            raise HTTPException(status_code=500, detail={"message": f"Could not retrieve story {story_id} from Jira"})
        
        # Extract story details
        fields = story_data.get('fields', {})
        title = fields.get('summary', f'Story {story_id}')
        description = fields.get('description', '')
        
        # Convert ADF description to plain text if needed
        if isinstance(description, dict):
            description = _extract_text_from_adf(description)
        
        # Create workflow
        workflow = Workflow(
            name=f"{story_id}: {title}",
            jira_story_id=story_id,
            jira_story_title=title,
            jira_story_description=description,
            repository_url="https://github.com/mauricezuse/negishi-freelancing",
            target_branch="main",
            status="pending"
        )
        
        db.add(workflow)
        db.commit()
        db.refresh(workflow)
        
        return {"message": f"Workflow created successfully for {story_id}", "workflow_id": workflow.id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": f"Could not retrieve story {story_id} from Jira"})

@app.delete("/workflows/{workflow_id}")
def delete_workflow(workflow_id: int, db: Session = Depends(get_db)):
    """Delete a workflow and all its related data"""
    try:
        # Find the workflow
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Get workflow name for response
        workflow_name = workflow.name
        
        # Delete related data (cascading should handle this, but let's be explicit)
        # Get conversation IDs first
        conversation_ids = db.query(Conversation.id).filter(Conversation.workflow_id == workflow_id).all()
        conversation_ids = [conv_id[0] for conv_id in conversation_ids]
        
        # Delete escalations and collaborations for these conversations
        if conversation_ids:
            db.query(Escalation).filter(Escalation.conversation_id.in_(conversation_ids)).delete()
            db.query(Collaboration).filter(Collaboration.conversation_id.in_(conversation_ids)).delete()
        
        # Delete conversations
        db.query(Conversation).filter(Conversation.workflow_id == workflow_id).delete()
        
        # Delete code files
        db.query(CodeFile).filter(CodeFile.workflow_id == workflow_id).delete()
        
        # Delete the workflow itself
        db.delete(workflow)
        db.commit()
        
        return {
            "message": f"Workflow '{workflow_name}' deleted successfully",
            "workflow_id": workflow_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting workflow: {str(e)}")

def _extract_text_from_adf(adf_doc):
    """Extract plain text from Atlassian Document Format"""
    if not isinstance(adf_doc, dict):
        return str(adf_doc)
    
    text_parts = []
    
    def extract_from_content(content):
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    if item.get('type') == 'text':
                        text_parts.append(item.get('text', ''))
                    elif 'content' in item:
                        extract_from_content(item['content'])
    
    if 'content' in adf_doc:
        extract_from_content(adf_doc['content'])
    
    return ' '.join(text_parts).strip()

## Removed earlier duplicate /agents endpoint to ensure consistency

@app.get("/")
def list_endpoints():
    return {
        "endpoints": [
            {"path": "/plan-and-design", "method": "POST", "description": "Generate architecture, component list, and diagrams from product vision."},
            {"path": "/generate-stories", "method": "POST", "description": "Generate user stories with story points from design docs."},
            {"path": "/gap-analysis", "method": "POST", "description": "Compare Jira and generated stories, return gap analysis."},
            {"path": "/implement-stories", "method": "POST", "description": "Implement user stories with tests."},
            {"path": "/workflows", "method": "GET", "description": "List all workflows."},
            {"path": "/workflows/{workflow_id}", "method": "GET", "description": "Get workflow details and conversations."},
            {"path": "/workflows/{workflow_id}/execute", "method": "POST", "description": "Execute a workflow."},
            {"path": "/agents", "method": "GET", "description": "List all agents."},
            {"path": "/agents/{agent_id}", "method": "GET", "description": "Get agent details."},
            {"path": "/health", "method": "GET", "description": "Health check."}
        ]
    }

# --- Models for API ---
class PlanningInput(BaseModel):
    product_vision: str

class DesignDocsInput(BaseModel):
    design_docs: str

class StoryGenInput(BaseModel):
    design_docs: str
    additional_context: Optional[str] = None

class GapAnalysisInput(BaseModel):
    jira_stories: List[str]
    generated_stories: List[str]

class ImplementStoriesInput(BaseModel):
    stories: List[str]

# --- Endpoints ---

@app.post("/plan-and-design")
def plan_and_design(input: PlanningInput):
    result = run_planning_and_design(input.product_vision)
    return result

@app.post("/generate-stories")
def generate_stories_endpoint(input: StoryGenInput):
    result = generate_stories(input.design_docs, input.additional_context)
    return result

@app.post("/gap-analysis")
def gap_analysis_endpoint(input: GapAnalysisInput):
    result = gap_analysis(input.jira_stories, input.generated_stories)
    return result

@app.post("/implement-stories")
def implement_stories_endpoint(input: ImplementStoriesInput):
    results = implement_stories_with_tests(input.stories)
    return {"results": results}

@app.post("/run-workflow")
def run_workflow():
    return {"message": "Workflow execution not yet implemented."}

# --- New API Endpoints for Frontend ---

## Removed legacy file-based workflow endpoints to avoid overriding DB-backed routes

@app.get("/agents")
def get_agents():
    """Get list of all available agents."""
    agents = [
        {
            "id": "pm",
            "name": "Product Manager",
            "role": "Product Management",
            "goal": "Define product requirements and user stories",
            "backstory": "Experienced product manager with deep understanding of user needs"
        },
        {
            "id": "architect",
            "name": "Solution Architect", 
            "role": "Architecture",
            "goal": "Design system architecture and technical solutions",
            "backstory": "Senior architect with expertise in scalable system design"
        },
        {
            "id": "developer",
            "name": "Backend Developer",
            "role": "Backend Development",
            "goal": "Implement backend services and APIs",
            "backstory": "Full-stack developer specializing in Python and FastAPI"
        },
        {
            "id": "frontend",
            "name": "Frontend Developer",
            "role": "Frontend Development", 
            "goal": "Implement user interfaces and frontend components",
            "backstory": "Angular specialist with expertise in modern web frameworks"
        },
        {
            "id": "tester",
            "name": "QA Tester",
            "role": "Quality Assurance",
            "goal": "Ensure code quality through comprehensive testing",
            "backstory": "QA engineer with expertise in automated testing and quality assurance"
        },
        {
            "id": "reviewer",
            "name": "Code Reviewer",
            "role": "Code Review",
            "goal": "Review code for quality, security, and best practices",
            "backstory": "Senior developer with keen eye for code quality and security"
        }
    ]
    return agents

@app.get("/agents/{agent_id}")
def get_agent(agent_id: str):
    """Get detailed information about a specific agent."""
    agents = {
        "pm": {
            "id": "pm",
            "name": "Product Manager",
            "role": "Product Management",
            "goal": "Define product requirements and user stories",
            "backstory": "Experienced product manager with deep understanding of user needs",
            "capabilities": ["Requirements analysis", "User story creation", "Stakeholder communication"]
        },
        "architect": {
            "id": "architect", 
            "name": "Solution Architect",
            "role": "Architecture",
            "goal": "Design system architecture and technical solutions",
            "backstory": "Senior architect with expertise in scalable system design",
            "capabilities": ["System design", "Technology selection", "API design", "Database design"]
        },
        "developer": {
            "id": "developer",
            "name": "Backend Developer", 
            "role": "Backend Development",
            "goal": "Implement backend services and APIs",
            "backstory": "Full-stack developer specializing in Python and FastAPI",
            "capabilities": ["Python development", "FastAPI", "Database integration", "API implementation"]
        },
        "frontend": {
            "id": "frontend",
            "name": "Frontend Developer",
            "role": "Frontend Development",
            "goal": "Implement user interfaces and frontend components", 
            "backstory": "Angular specialist with expertise in modern web frameworks",
            "capabilities": ["Angular development", "TypeScript", "HTML/CSS", "UI/UX implementation"]
        },
        "tester": {
            "id": "tester",
            "name": "QA Tester",
            "role": "Quality Assurance", 
            "goal": "Ensure code quality through comprehensive testing",
            "backstory": "QA engineer with expertise in automated testing and quality assurance",
            "capabilities": ["Unit testing", "Integration testing", "Playwright testing", "Test automation"]
        },
        "reviewer": {
            "id": "reviewer",
            "name": "Code Reviewer",
            "role": "Code Review",
            "goal": "Review code for quality, security, and best practices",
            "backstory": "Senior developer with keen eye for code quality and security",
            "capabilities": ["Code review", "Security analysis", "Performance optimization", "Best practices"]
        }
    }
    
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agents[agent_id]

def run_story_implementation_workflow(story_id: str, use_real_jira: bool = True, use_real_github: bool = True, 
                                    codebase_root: Optional[str] = None, user_intervention_mode: bool = False,
                                    enhanced: bool = False, resume: bool = False):
    """
    Run the story implementation workflow.
    
    Args:
        story_id: Jira story ID to implement
        use_real_jira: Whether to use real Jira integration
        use_real_github: Whether to use real GitHub integration
        codebase_root: Path to codebase root (optional)
        user_intervention_mode: Whether to pause for user input
        enhanced: Whether to use enhanced workflow with better collaboration
        resume: Whether to resume from checkpoint
    """
    print(f"🚀 Starting {'Enhanced' if enhanced else 'Standard'} Story Implementation Workflow")
    print(f"📋 Story ID: {story_id}")
    print(f"🔗 Jira Integration: {'Real' if use_real_jira else 'Stub'}")
    print(f"🔗 GitHub Integration: {'Real' if use_real_github else 'Stub'}")
    print(f"👤 User Intervention: {'Enabled' if user_intervention_mode else 'Disabled'}")
    print(f"🔄 Resume Mode: {'Enabled' if resume else 'Disabled'}")
    print("=" * 60)
    
    try:
        if enhanced:
            workflow = EnhancedStoryWorkflow(
                story_id=story_id,
                use_real_jira=use_real_jira,
                use_real_github=use_real_github,
                codebase_root=codebase_root,
                user_intervention_mode=user_intervention_mode
            )
        else:
            workflow = StoryImplementationWorkflow(
                story_id=story_id,
                use_real_jira=use_real_jira,
                use_real_github=use_real_github,
                codebase_root=codebase_root,
                user_intervention_mode=user_intervention_mode
            )
        
        results = workflow.run(resume=resume)
        
        print("\n" + "=" * 60)
        print("✅ Workflow completed successfully!")
        print(f"📊 Results: {len(results)} items generated")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")
        raise

def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(description="AI-Team: CrewAI Orchestration Platform")
    parser.add_argument("--workflow", choices=["story_implementation", "enhanced_story_implementation"], 
                       required=True, help="Workflow to run")
    parser.add_argument("--story", required=True, help="Jira story ID to implement")
    parser.add_argument("--use-real-jira", action="store_true", default=None, 
                       help="Use real Jira integration (default: from env)")
    parser.add_argument("--use-real-github", action="store_true", default=None, 
                       help="Use real GitHub integration (default: from env)")
    parser.add_argument("--codebase-root", help="Path to codebase root")
    parser.add_argument("--user-intervention", action="store_true", 
                       help="Enable user intervention mode")
    parser.add_argument("--resume", action="store_true", 
                       help="Resume from checkpoint")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                       default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Set log level
    import logging
    logging.basicConfig(level=getattr(logging, args.log_level))
    
    # Determine integration modes
    use_real_jira = args.use_real_jira if args.use_real_jira is not None else settings.use_real_jira
    use_real_github = args.use_real_github if args.use_real_github is not None else settings.use_real_github
    
    # Run appropriate workflow
    if args.workflow == "story_implementation":
        enhanced = False
    elif args.workflow == "enhanced_story_implementation":
        enhanced = True
    else:
        print(f"❌ Unknown workflow: {args.workflow}")
        sys.exit(1)
    
    try:
        results = run_story_implementation_workflow(
            story_id=args.story,
            use_real_jira=use_real_jira,
            use_real_github=use_real_github,
            codebase_root=args.codebase_root,
            user_intervention_mode=args.user_intervention,
            enhanced=enhanced,
            resume=args.resume
        )
        
        # Print summary
        print("\n📋 Workflow Summary:")
        print(f"   Story ID: {args.story}")
        print(f"   Workflow Type: {'Enhanced' if enhanced else 'Standard'}")
        print(f"   Results: {len(results)} items")
        
        if args.user_intervention:
            input("\nPress Enter to exit...")
            
    except KeyboardInterrupt:
        print("\n⚠️  Workflow interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 