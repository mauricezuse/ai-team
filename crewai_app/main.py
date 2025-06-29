from fastapi import FastAPI

app = FastAPI(title="CrewAI Orchestration Platform")

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Placeholder for workflow execution endpoint
@app.post("/run-workflow")
def run_workflow():
    return {"message": "Workflow execution not yet implemented."} 