from crewai_app.workflows.mvp_workflow import run_mvp_workflow

def test_run_mvp_workflow():
    result = run_mvp_workflow("User signup")
    assert "feature" in result 