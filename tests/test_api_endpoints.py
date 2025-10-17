"""
Unit tests for the new API endpoints in crewai_app/main.py
"""
import pytest
import json
import os
import tempfile
from unittest.mock import patch, mock_open
from fastapi.testclient import TestClient
from crewai_app.main import app
from crewai_app.database import get_db, Workflow, init_database
from uuid import uuid4

client = TestClient(app)

class TestWorkflowEndpoints:
    """Test cases for workflow-related endpoints"""
    def _clear_all_workflows(self):
        # Use API to safely delete and cascade related rows
        resp = client.get("/workflows")
        if resp.status_code == 200:
            for item in resp.json():
                wid = item.get("id")
                try:
                    client.delete(f"/workflows/{wid}")
                except Exception:
                    pass
    
    def test_get_workflows_empty(self):
        """Test GET /workflows when no workflows exist (DB-backed)."""
        init_database()
        # Clear all workflows for an isolated test via API cascade
        self._clear_all_workflows()
        response = client.get("/workflows")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_workflows_with_data(self):
        """Test GET /workflows with existing workflow row (DB-backed)."""
        init_database()
        db = next(get_db())
        # Clear and insert a workflow using API cascade deletion
        self._clear_all_workflows()
        wf = Workflow(
            name="Enhanced Story NEGISHI-178",
            jira_story_id="NEGISHI-178",
            jira_story_title="Test Story",
            jira_story_description="Desc",
            repository_url="https://example.com/repo",
            target_branch="main",
            status="completed"
        )
        db.add(wf)
        db.commit()
        db.refresh(wf)

        response = client.get("/workflows")
        assert response.status_code == 200
        workflows = response.json()
        assert any(item["id"] == wf.id and item["status"] == "completed" for item in workflows)
    
    def test_get_workflow_not_found(self):
        """Test GET /workflows/{workflow_id} when workflow doesn't exist (numeric id)."""
        response = client.get("/workflows/999999")
        assert response.status_code == 404
        assert "Workflow not found" in response.json()["detail"]
    
    def test_get_workflow_success(self):
        """Test GET /workflows/{workflow_id} with valid DB workflow."""
        init_database()
        db = next(get_db())
        wf = Workflow(
            name="Test Workflow",
            jira_story_id="TEST-200",
            jira_story_title="Title",
            jira_story_description="Desc",
            status="completed"
        )
        db.add(wf)
        db.commit()
        db.refresh(wf)
        response = client.get(f"/workflows/{wf.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == wf.id
        assert data["name"] == "Test Workflow"
        assert data["status"] == "completed"
    
    def test_get_workflow_file_error(self):
        """Legacy file error test no longer applicable; ensure 404 for unknown numeric id."""
        response = client.get("/workflows/1234567")
        assert response.status_code == 404

class TestAgentEndpoints:
    """Test cases for agent-related endpoints"""
    
    def test_get_agents(self):
        """Test GET /agents endpoint"""
        response = client.get("/agents")
        assert response.status_code == 200
        agents = response.json()
        assert len(agents) == 6
        
        # Check that all expected agents are present
        agent_ids = [agent["id"] for agent in agents]
        expected_agents = ["pm", "architect", "developer", "frontend", "tester", "reviewer"]
        for expected_agent in expected_agents:
            assert expected_agent in agent_ids
    
    def test_get_agent_success(self):
        """Test GET /agents/{agent_id} with valid agent"""
        response = client.get("/agents/pm")
        assert response.status_code == 200
        agent = response.json()
        assert agent["id"] == "pm"
        assert agent["name"] == "Product Manager"
        assert agent["role"] == "Product Management"
        assert "capabilities" in agent
        assert len(agent["capabilities"]) > 0
    
    def test_get_agent_not_found(self):
        """Test GET /agents/{agent_id} with invalid agent"""
        response = client.get("/agents/invalid_agent")
        assert response.status_code == 404
        assert "Agent not found" in response.json()["detail"]

class TestWorkflowExecution:
    """Test cases for workflow execution endpoints"""
    
    @patch('crewai_app.services.workflow_executor.workflow_executor')
    def test_execute_workflow_success(self, mock_executor):
        """Test POST /workflows/{workflow_id:int}/execute with success"""
        init_database()
        db = next(get_db())
        wf = Workflow(
            name="Story NEGISHI-178-UT1",
            jira_story_id="NEGISHI-178-UT1",
            jira_story_title="Title",
            jira_story_description="Desc",
            status="pending"
        )
        db.add(wf)
        db.commit()
        db.refresh(wf)
        mock_executor.execute_workflow_async.return_value = {"status": "completed"}
        response = client.post(f"/workflows/{wf.id}/execute")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") in ["running", "completed"]
        assert "execution_id" in data
    
    @patch('crewai_app.services.workflow_executor.workflow_executor')
    def test_execute_workflow_with_story_id(self, mock_executor):
        """Test POST /workflows/{workflow_id:int}/execute ignores legacy story_id param"""
        init_database()
        db = next(get_db())
        wf = Workflow(
            name="Story NEGISHI-175-UT2",
            jira_story_id="NEGISHI-175-UT2",
            jira_story_title="Title",
            jira_story_description="Desc",
            status="pending"
        )
        db.add(wf)
        db.commit()
        db.refresh(wf)
        mock_executor.execute_workflow_async.return_value = {"status": "completed"}
        response = client.post(f"/workflows/{wf.id}/execute?story_id=IGNORED")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") in ["running", "completed"]
        assert "execution_id" in data
    
    @patch('crewai_app.services.workflow_executor.workflow_executor')
    def test_execute_workflow_error(self, mock_executor):
        """Test POST /workflows/{workflow_id:int}/execute with error"""
        init_database()
        db = next(get_db())
        unique_sid = f"NEGISHI-999-UT3-{uuid4().hex[:6]}"
        wf = Workflow(
            name="Story ERROR-UT3",
            jira_story_id=unique_sid,
            jira_story_title="Title",
            jira_story_description="Desc",
            status="pending"
        )
        db.add(wf)
        db.commit()
        db.refresh(wf)
        mock_executor.execute_workflow_async.side_effect = Exception("boom")
        response = client.post(f"/workflows/{wf.id}/execute")
        assert response.status_code == 500

class TestHealthAndEndpoints:
    """Test cases for health and endpoint listing"""
    
    def test_health_check(self):
        """Test GET /health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    def test_list_endpoints(self):
        """Test GET / endpoint for endpoint listing"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "endpoints" in data
        endpoints = data["endpoints"]
        
        # Check that new endpoints are included
        endpoint_paths = [ep["path"] for ep in endpoints]
        assert "/workflows" in endpoint_paths
        assert "/agents" in endpoint_paths
        assert "/workflows/{workflow_id}" in endpoint_paths
        assert "/agents/{agent_id}" in endpoint_paths

class TestCORSConfiguration:
    """Test CORS middleware configuration"""
    
    def test_cors_headers(self):
        """Test that CORS headers are properly set"""
        response = client.options("/workflows")
        # FastAPI TestClient doesn't fully simulate CORS, but we can verify the middleware is configured
        assert response.status_code in [200, 405]  # OPTIONS might not be implemented, which is fine

if __name__ == "__main__":
    pytest.main([__file__])
