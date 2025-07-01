from fastapi import FastAPI, Body
from pydantic import BaseModel
from typing import List, Optional
from crewai_app.workflows.planning_workflow import run_planning_and_design, generate_stories, gap_analysis
from crewai_app.workflows.implementation_workflow import implement_stories_with_tests

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

# Placeholder for workflow execution endpoint
@app.post("/run-workflow")
def run_workflow():
    return {"message": "Workflow execution not yet implemented."} 