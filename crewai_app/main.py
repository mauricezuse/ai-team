from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
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

app = FastAPI(title="CrewAI Orchestration Platform")

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:3000"],  # Angular dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

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

@app.get("/workflows")
def get_workflows():
    """Get list of all workflows from checkpoint files."""
    workflows = []
    checkpoint_dir = "workflow_results"
    
    if os.path.exists(checkpoint_dir):
        for file_path in glob.glob(os.path.join(checkpoint_dir, "*.json")):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                workflow_id = os.path.basename(file_path).replace('.json', '').replace('_checkpoint', '')
                workflow_name = workflow_id.replace('_', ' ').title()
                
                # Handle different data structures - some files might have lists instead of dicts
                workflow_log = data.get('workflow_log', [])
                if isinstance(workflow_log, list) and len(workflow_log) > 0:
                    # Check if it's a list of dicts or just a list
                    if isinstance(workflow_log[0], dict):
                        status = "completed" if len(workflow_log) > 0 else "pending"
                    else:
                        status = "completed" if len(workflow_log) > 0 else "pending"
                else:
                    status = "pending"
                
                # Extract agents from workflow log
                agents = []
                if isinstance(workflow_log, list) and len(workflow_log) > 0:
                    for entry in workflow_log:
                        if isinstance(entry, dict) and 'agent' in entry:
                            agents.append(entry['agent'])
                
                workflows.append({
                    "id": workflow_id,
                    "name": workflow_name,
                    "status": status,
                    "agents": list(set(agents)),
                    "created_at": data.get('timestamp', ''),
                    "last_step": workflow_log[-1].get('step', '') if isinstance(workflow_log, list) and len(workflow_log) > 0 and isinstance(workflow_log[-1], dict) else ''
                })
            except Exception as e:
                print(f"Error reading workflow file {file_path}: {e}")
    
    return workflows

@app.get("/workflows/{workflow_id}")
def get_workflow(workflow_id: str):
    """Get detailed workflow information including agent conversations."""
    checkpoint_file = f"workflow_results/{workflow_id}_checkpoint.json"
    
    if not os.path.exists(checkpoint_file):
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    try:
        with open(checkpoint_file, 'r') as f:
            data = json.load(f)
        
        # Extract agent conversations from workflow log
        conversations = []
        workflow_log = data.get('workflow_log', [])
        if isinstance(workflow_log, list):
            for entry in workflow_log:
                if isinstance(entry, dict):
                    conversation = {
                        "step": entry.get('step', ''),
                        "timestamp": entry.get('timestamp', ''),
                        "agent": entry.get('agent', ''),
                        "status": entry.get('status', ''),
                        "details": entry.get('details', ''),
                        "output": entry.get('output', ''),
                        "code_files": entry.get('code_files', []),
                        "escalations": entry.get('escalations', []),
                        "collaborations": entry.get('collaborations', [])
                    }
                    conversations.append(conversation)
        
        return {
            "id": workflow_id,
            "name": workflow_id.replace('_', ' ').title(),
            "status": "completed" if conversations else "pending",
            "conversations": conversations,
            "created_at": data.get('timestamp', ''),
            "collaboration_queue": data.get('collaboration_queue', []),
            "escalation_queue": data.get('escalation_queue', [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading workflow: {str(e)}")

@app.post("/workflows/{workflow_id}/execute")
def execute_workflow(workflow_id: str, story_id: Optional[str] = None):
    """Execute a workflow (enhanced story workflow)."""
    try:
        # Use the story_id from the workflow_id or provided parameter
        if not story_id:
            # Extract story ID from workflow_id (e.g., "enhanced_story_NEGISHI-178" -> "NEGISHI-178")
            if "NEGISHI-" in workflow_id:
                story_id = workflow_id.split("NEGISHI-")[1].split("_")[0]
                story_id = f"NEGISHI-{story_id}"
            else:
                story_id = "NEGISHI-178"  # Default fallback
        
        # Create and run enhanced workflow
        workflow = EnhancedStoryWorkflow(
            story_id=story_id,
            use_real_jira=True,
            use_real_github=True
        )
        
        results = workflow.run()
        
        return {
            "workflow_id": workflow_id,
            "story_id": story_id,
            "status": "completed",
            "results": results,
            "message": f"Workflow executed successfully for story {story_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing workflow: {str(e)}")

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