from fastapi import FastAPI, Body
from pydantic import BaseModel
from typing import List, Optional
import argparse
import sys
import os
from crewai_app.workflows.planning_workflow import run_planning_and_design, generate_stories, gap_analysis
from crewai_app.workflows.implementation_workflow import implement_stories_with_tests
from crewai_app.workflows.story_implementation_workflow import StoryImplementationWorkflow
from crewai_app.workflows.enhanced_story_workflow import EnhancedStoryWorkflow
from crewai_app.config import settings

app = FastAPI(title="CrewAI Orchestration Platform")

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