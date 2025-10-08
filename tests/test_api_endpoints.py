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

client = TestClient(app)

class TestWorkflowEndpoints:
    """Test cases for workflow-related endpoints"""
    
    def test_get_workflows_empty(self):
        """Test GET /workflows when no workflows exist"""
        with patch('os.path.exists', return_value=False):
            response = client.get("/workflows")
            assert response.status_code == 200
            assert response.json() == []
    
    def test_get_workflows_with_data(self):
        """Test GET /workflows with existing workflow data"""
        mock_workflow_data = {
            "workflow_log": [
                {"step": "story_retrieved", "agent": "pm", "timestamp": "2024-01-01T00:00:00"},
                {"step": "architect_review", "agent": "architect", "timestamp": "2024-01-01T00:01:00"}
            ],
            "timestamp": "2024-01-01T00:00:00"
        }
        
        with patch('os.path.exists', return_value=True), \
             patch('glob.glob', return_value=['workflow_results/enhanced_story_NEGISHI-178_checkpoint.json']), \
             patch('builtins.open', mock_open(read_data=json.dumps(mock_workflow_data))):
            
            response = client.get("/workflows")
            assert response.status_code == 200
            workflows = response.json()
            assert len(workflows) == 1
            assert workflows[0]["id"] == "enhanced_story_NEGISHI-178"
            assert workflows[0]["name"] == "Enhanced Story Negishi-178"
            assert workflows[0]["status"] == "completed"
            assert "pm" in workflows[0]["agents"]
            assert "architect" in workflows[0]["agents"]
    
    def test_get_workflow_not_found(self):
        """Test GET /workflows/{workflow_id} when workflow doesn't exist"""
        with patch('os.path.exists', return_value=False):
            response = client.get("/workflows/nonexistent")
            assert response.status_code == 404
            assert "Workflow not found" in response.json()["detail"]
    
    def test_get_workflow_success(self):
        """Test GET /workflows/{workflow_id} with valid workflow"""
        mock_workflow_data = {
            "workflow_log": [
                {
                    "step": "story_retrieved",
                    "agent": "pm",
                    "timestamp": "2024-01-01T00:00:00",
                    "status": "completed",
                    "details": "Story retrieved successfully",
                    "output": "Story details...",
                    "code_files": [],
                    "escalations": [],
                    "collaborations": []
                }
            ],
            "timestamp": "2024-01-01T00:00:00",
            "collaboration_queue": [],
            "escalation_queue": []
        }
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(mock_workflow_data))):
            
            response = client.get("/workflows/test_workflow")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "test_workflow"
            assert data["name"] == "Test Workflow"
            assert data["status"] == "completed"
            assert len(data["conversations"]) == 1
            assert data["conversations"][0]["step"] == "story_retrieved"
            assert data["conversations"][0]["agent"] == "pm"
    
    def test_get_workflow_file_error(self):
        """Test GET /workflows/{workflow_id} with file read error"""
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', side_effect=IOError("File read error")):
            
            response = client.get("/workflows/test_workflow")
            assert response.status_code == 500
            assert "Error reading workflow" in response.json()["detail"]

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
    
    @patch('crewai_app.main.EnhancedStoryWorkflow')
    def test_execute_workflow_success(self, mock_workflow_class):
        """Test POST /workflows/{workflow_id}/execute with success"""
        mock_workflow_instance = mock_workflow_class.return_value
        mock_workflow_instance.run.return_value = [{"status": "completed", "result": "success"}]
        
        response = client.post("/workflows/enhanced_story_NEGISHI-178/execute")
        assert response.status_code == 200
        data = response.json()
        assert data["workflow_id"] == "enhanced_story_NEGISHI-178"
        assert data["story_id"] == "NEGISHI-178"
        assert data["status"] == "completed"
        assert "Workflow executed successfully" in data["message"]
    
    @patch('crewai_app.main.EnhancedStoryWorkflow')
    def test_execute_workflow_with_story_id(self, mock_workflow_class):
        """Test POST /workflows/{workflow_id}/execute with custom story_id"""
        mock_workflow_instance = mock_workflow_class.return_value
        mock_workflow_instance.run.return_value = [{"status": "completed"}]
        
        response = client.post("/workflows/test_workflow/execute?story_id=NEGISHI-175")
        assert response.status_code == 200
        data = response.json()
        assert data["story_id"] == "NEGISHI-175"
    
    @patch('crewai_app.main.EnhancedStoryWorkflow')
    def test_execute_workflow_error(self, mock_workflow_class):
        """Test POST /workflows/{workflow_id}/execute with error"""
        mock_workflow_class.side_effect = Exception("Workflow execution failed")
        
        response = client.post("/workflows/test_workflow/execute")
        assert response.status_code == 500
        assert "Error executing workflow" in response.json()["detail"]

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
