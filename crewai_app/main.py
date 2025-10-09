from fastapi import FastAPI, Body, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import argparse
import sys
import os
import json
import glob
from datetime import datetime
from crewai_app.workflows.planning_workflow import run_planning_and_design, generate_stories, gap_analysis
from crewai_app.workflows.implementation_workflow import implement_stories_with_tests
from crewai_app.workflows.story_implementation_workflow import StoryImplementationWorkflow
from crewai_app.workflows.enhanced_story_workflow import EnhancedStoryWorkflow
from crewai_app.config import settings
from crewai_app.database import get_db, init_database, Workflow, Conversation, CodeFile, Escalation, Collaboration
from crewai_app.database import LLMCall

app = FastAPI(title="CrewAI Orchestration Platform")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_database()

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:3000"],  # Angular dev server
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
def get_conversation_llm_calls(conversation_id: int, db: Session = Depends(get_db)):
    """Return LLM calls for a conversation with usage and cost."""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Prefer normalized rows if any exist
    llm_rows = db.query(LLMCall).filter(LLMCall.conversation_id == conversation_id).all()
    if llm_rows:
        return {
            "conversation_id": conversation_id,
            "total_tokens_used": conversation.total_tokens_used or 0,
            "total_cost": conversation.total_cost or "0.00",
            "calls": [
                {
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
                }
                for row in llm_rows
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

    return {
        "conversation_id": conversation_id,
        "total_tokens_used": conversation.total_tokens_used or 0,
        "total_cost": conversation.total_cost or "0.00",
        "calls": llm_calls_data,
    }

# New workflow management endpoints
@app.get("/workflows", response_model=List[WorkflowResponse])
def get_workflows(db: Session = Depends(get_db)):
    """Get all workflows"""
    workflows = db.query(Workflow).all()
    
    # Convert SQLAlchemy models to dictionaries
    workflow_list = []
    for workflow in workflows:
        workflow_data = {
            "id": workflow.id,
            "name": workflow.name,
            "jira_story_id": workflow.jira_story_id,
            "jira_story_title": workflow.jira_story_title,
            "jira_story_description": workflow.jira_story_description or "",
            "status": workflow.status,
            "created_at": workflow.created_at,
            "updated_at": workflow.updated_at,
            "repository_url": workflow.repository_url,
            "target_branch": workflow.target_branch,
            "conversations": [],
            "code_files": []
        }
        workflow_list.append(workflow_data)
    
    return workflow_list

@app.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(workflow_id: int, db: Session = Depends(get_db)):
    """Get a specific workflow with all its data"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
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
        "conversations": []
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

@app.post("/workflows/{workflow_id}/execute")
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

@app.get("/workflows/{workflow_id}/status")
def get_workflow_status(workflow_id: int):
    """Get the current status of a workflow execution"""
    from crewai_app.services.workflow_executor import workflow_executor
    return workflow_executor.get_workflow_status(workflow_id)

@app.get("/workflows/status/running")
def get_running_workflows():
    """Get all currently running workflows"""
    from crewai_app.services.workflow_executor import workflow_executor
    return workflow_executor.get_running_workflows()

@app.post("/workflows/from-jira/{story_id}")
def create_workflow_from_jira(story_id: str, db: Session = Depends(get_db)):
    """Create a workflow from an existing Jira story"""
    try:
        # Check if workflow already exists
        existing = db.query(Workflow).filter(Workflow.jira_story_id == story_id).first()
        if existing:
            return {"message": f"Workflow for {story_id} already exists", "workflow_id": existing.id}
        
        # Pull story details from Jira
        from crewai_app.services.jira_service import JiraService
        
        try:
            # Production mode: always use real Jira integration
            jira_service = JiraService(use_real=True)
            story_data = jira_service.get_story(story_id)
            
            if not story_data:
                return {"message": f"Could not retrieve story {story_id} from Jira", "workflow_id": None}, 404
        except Exception as e:
            return {"message": f"Could not retrieve story {story_id} from Jira", "error": str(e)}, 500
        
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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating workflow from Jira: {str(e)}")

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

@app.get("/agents")
def get_agents():
    """Get available agents"""
    return [
        {"id": "pm", "name": "Product Manager", "role": "Requirements analysis and user story creation"},
        {"id": "architect", "name": "System Architect", "role": "System design and architecture"},
        {"id": "developer", "name": "Backend Developer", "role": "Backend implementation and APIs"},
        {"id": "frontend", "name": "Frontend Developer", "role": "Frontend implementation and UI"},
        {"id": "tester", "name": "QA Tester", "role": "Testing and quality assurance"},
        {"id": "reviewer", "name": "Code Reviewer", "role": "Code review and quality standards"}
    ]

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