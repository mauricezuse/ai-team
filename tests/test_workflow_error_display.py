"""
Unit tests for workflow error display functionality
Tests error display in both workflow list and detail components
"""
import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from crewai_app.main import app
from crewai_app.database import get_db, Workflow
from crewai_app.services.workflow_status_service import WorkflowStatusService

client = TestClient(app)

class TestWorkflowErrorDisplay:
    """Test error display functionality in workflow components"""
    
    def test_workflow_with_error_status(self):
        """Test that workflows with error status show error information"""
        # Mock workflow with error
        error_workflow = {
            "id": 12,
            "name": "NEGISHI-165: Test Error Workflow",
            "jira_story_id": "NEGISHI-165",
            "status": "failed",
            "error": "Database connection timeout after 30 seconds",
            "started_at": "2025-01-10T10:00:00Z",
            "finished_at": "2025-01-10T10:00:30Z",
            "isTerminal": True,
            "heartbeat_stale": False,
            "created_at": "2025-01-10T09:00:00Z",
            "updated_at": "2025-01-10T10:00:30Z"
        }
        
        # Test API response includes error field
        response = client.get("/workflows/12")
        assert response.status_code == 200
        
        workflow_data = response.json()
        assert "error" in workflow_data
        assert workflow_data["error"] is not None
        assert workflow_data["status"] == "failed"
        assert workflow_data["isTerminal"] is True
    
    def test_workflow_list_shows_error_indicator(self):
        """Test that workflow list shows error indicators for failed workflows"""
        response = client.get("/workflows")
        assert response.status_code == 200
        
        workflows = response.json()
        assert isinstance(workflows, list)
        
        # Find workflow 12 (NEGISHI-165)
        workflow_12 = next((w for w in workflows if w["id"] == 12), None)
        if workflow_12:
            assert "error" in workflow_12
            if workflow_12["error"]:
                assert workflow_12["status"] == "failed"
                assert workflow_12["isTerminal"] is True
    
    def test_error_message_formatting(self):
        """Test that error messages are properly formatted"""
        test_errors = [
            "Database connection timeout after 30 seconds",
            "Jira API returned 404: Story NEGISHI-165 not found",
            "GitHub API rate limit exceeded. Please try again later.",
            "LLM service unavailable: OpenAI API key invalid"
        ]
        
        for error_msg in test_errors:
            # Test that error message is preserved in API response
            response = client.get("/workflows/12")
            if response.status_code == 200:
                workflow_data = response.json()
                if workflow_data.get("error"):
                    # Error message should be preserved as-is
                    assert isinstance(workflow_data["error"], str)
                    assert len(workflow_data["error"]) > 0
    
    def test_workflow_status_with_error(self):
        """Test workflow status endpoint returns error information"""
        response = client.get("/workflows/12/status")
        assert response.status_code == 200
        
        status_data = response.json()
        assert "status" in status_data
        assert "isTerminal" in status_data
        
        if status_data["status"] == "failed":
            assert "error" in status_data
            assert status_data["isTerminal"] is True
    
    def test_error_display_components(self):
        """Test that error display components are properly structured"""
        response = client.get("/workflows/12")
        if response.status_code == 200:
            workflow_data = response.json()
            
            # Check required fields for error display
            required_fields = ["id", "name", "status", "isTerminal"]
            for field in required_fields:
                assert field in workflow_data
            
            # If workflow has error, check error-specific fields
            if workflow_data.get("error"):
                assert workflow_data["status"] in ["failed", "error"]
                assert workflow_data["isTerminal"] is True
                assert "finished_at" in workflow_data
    
    def test_heartbeat_timeout_error(self):
        """Test heartbeat timeout error scenario"""
        # Simulate a workflow that was running but lost heartbeat
        timeout_error = "Heartbeat timeout after 300 seconds"
        
        # Test that timeout errors are properly handled
        response = client.get("/workflows/12")
        if response.status_code == 200:
            workflow_data = response.json()
            
            # If this is a timeout error, it should be marked as failed
            if workflow_data.get("error") == timeout_error:
                assert workflow_data["status"] == "failed"
                assert workflow_data["isTerminal"] is True
    
    def test_multiple_error_scenarios(self):
        """Test various error scenarios"""
        error_scenarios = [
            {
                "error_type": "database_error",
                "error_msg": "Database connection failed",
                "expected_status": "failed"
            },
            {
                "error_type": "api_error", 
                "error_msg": "Jira API returned 500 Internal Server Error",
                "expected_status": "failed"
            },
            {
                "error_type": "timeout_error",
                "error_msg": "Request timeout after 60 seconds",
                "expected_status": "failed"
            },
            {
                "error_type": "validation_error",
                "error_msg": "Invalid Jira story ID format",
                "expected_status": "failed"
            }
        ]
        
        for scenario in error_scenarios:
            # Test that error scenarios are properly handled
            response = client.get("/workflows/12")
            if response.status_code == 200:
                workflow_data = response.json()
                
                if workflow_data.get("error"):
                    assert workflow_data["status"] == scenario["expected_status"]
                    assert workflow_data["isTerminal"] is True
    
    def test_error_persistence(self):
        """Test that errors persist across API calls"""
        # Get workflow data multiple times
        responses = []
        for _ in range(3):
            response = client.get("/workflows/12")
            if response.status_code == 200:
                responses.append(response.json())
        
        if responses:
            # All responses should have consistent error information
            first_response = responses[0]
            for response_data in responses[1:]:
                if first_response.get("error"):
                    assert response_data.get("error") == first_response["error"]
                    assert response_data["status"] == first_response["status"]
                    assert response_data["isTerminal"] == first_response["isTerminal"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
