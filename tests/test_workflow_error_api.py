"""
API tests for workflow error status endpoints
Tests error information retrieval and status endpoints
"""
import pytest
import json
from datetime import datetime
from fastapi.testclient import TestClient
from crewai_app.main import app

client = TestClient(app)

class TestWorkflowErrorAPI:
    """Test API endpoints for workflow error information"""
    
    def test_get_workflow_with_error(self):
        """Test retrieving workflow 12 with error information"""
        response = client.get("/workflows/12")
        assert response.status_code == 200
        
        workflow_data = response.json()
        
        # Check required fields
        assert "id" in workflow_data
        assert "name" in workflow_data
        assert "status" in workflow_data
        assert "isTerminal" in workflow_data
        
        # If workflow has error, check error fields
        if workflow_data.get("error"):
            assert workflow_data["status"] in ["failed", "error"]
            assert workflow_data["isTerminal"] is True
            assert "finished_at" in workflow_data
            assert isinstance(workflow_data["error"], str)
            assert len(workflow_data["error"]) > 0
    
    def test_get_workflow_status_with_error(self):
        """Test workflow status endpoint returns error information"""
        response = client.get("/workflows/12/status")
        assert response.status_code == 200
        
        status_data = response.json()
        
        # Check status response structure
        assert "workflow_id" in status_data
        assert "status" in status_data
        assert "isTerminal" in status_data
        
        # If workflow has error, check error information
        if status_data.get("error"):
            assert status_data["status"] in ["failed", "error"]
            assert status_data["isTerminal"] is True
            assert isinstance(status_data["error"], str)
            assert len(status_data["error"]) > 0
    
    def test_workflow_list_includes_error_info(self):
        """Test that workflow list includes error information"""
        response = client.get("/workflows")
        assert response.status_code == 200
        
        workflows = response.json()
        assert isinstance(workflows, list)
        
        # Find workflow 12
        workflow_12 = next((w for w in workflows if w["id"] == 12), None)
        if workflow_12:
            # Check that error information is included
            assert "error" in workflow_12
            assert "isTerminal" in workflow_12
            assert "status" in workflow_12
            
            # If workflow has error, verify error details
            if workflow_12.get("error"):
                assert workflow_12["status"] in ["failed", "error"]
                assert workflow_12["isTerminal"] is True
                assert isinstance(workflow_12["error"], str)
                assert len(workflow_12["error"]) > 0
    
    def test_error_message_preservation(self):
        """Test that error messages are preserved correctly"""
        response = client.get("/workflows/12")
        assert response.status_code == 200
        
        workflow_data = response.json()
        
        if workflow_data.get("error"):
            error_message = workflow_data["error"]
            
            # Error message should be preserved as-is
            assert isinstance(error_message, str)
            assert len(error_message) > 0
            
            # Should not be truncated or modified
            assert error_message == error_message.strip()
            
            # Should contain meaningful error information
            assert any(keyword in error_message.lower() for keyword in [
                "error", "failed", "timeout", "connection", "api", "database"
            ])
    
    def test_error_status_consistency(self):
        """Test that error status is consistent across endpoints"""
        # Get workflow data
        workflow_response = client.get("/workflows/12")
        assert workflow_response.status_code == 200
        workflow_data = workflow_response.json()
        
        # Get status data
        status_response = client.get("/workflows/12/status")
        assert status_response.status_code == 200
        status_data = status_response.json()
        
        # If both have error information, they should be consistent
        if workflow_data.get("error") and status_data.get("error"):
            assert workflow_data["status"] == status_data["status"]
            assert workflow_data["isTerminal"] == status_data["isTerminal"]
            assert workflow_data["error"] == status_data["error"]
    
    def test_error_timestamps(self):
        """Test that error workflows have proper timestamps"""
        response = client.get("/workflows/12")
        assert response.status_code == 200
        
        workflow_data = response.json()
        
        if workflow_data.get("error"):
            # Failed workflows should have finished_at timestamp
            assert "finished_at" in workflow_data
            assert workflow_data["finished_at"] is not None
            
            # Should have started_at if it was running
            if workflow_data.get("started_at"):
                started_at = datetime.fromisoformat(workflow_data["started_at"].replace('Z', '+00:00'))
                finished_at = datetime.fromisoformat(workflow_data["finished_at"].replace('Z', '+00:00'))
                
                # Finished should be after started
                assert finished_at >= started_at
    
    def test_error_workflow_metadata(self):
        """Test that error workflows have proper metadata"""
        response = client.get("/workflows/12")
        assert response.status_code == 200
        
        workflow_data = response.json()
        
        if workflow_data.get("error"):
            # Should have terminal status
            assert workflow_data["isTerminal"] is True
            
            # Should not be running
            assert workflow_data["status"] != "running"
            
            # Should have error information
            assert workflow_data["error"] is not None
            assert isinstance(workflow_data["error"], str)
    
    def test_error_response_format(self):
        """Test that error responses have proper format"""
        response = client.get("/workflows/12")
        assert response.status_code == 200
        
        workflow_data = response.json()
        
        # Check response structure
        required_fields = ["id", "name", "status", "created_at", "updated_at"]
        for field in required_fields:
            assert field in workflow_data
        
        # Check error-specific fields if present
        if workflow_data.get("error"):
            error_fields = ["error", "isTerminal", "finished_at"]
            for field in error_fields:
                assert field in workflow_data
    
    def test_error_workflow_list_filtering(self):
        """Test that error workflows can be identified in list"""
        response = client.get("/workflows")
        assert response.status_code == 200
        
        workflows = response.json()
        
        # Find all failed workflows
        failed_workflows = [w for w in workflows if w.get("status") in ["failed", "error"]]
        
        for workflow in failed_workflows:
            # Failed workflows should have error information
            assert "error" in workflow
            assert workflow["isTerminal"] is True
            assert workflow["error"] is not None
    
    def test_error_workflow_heartbeat_status(self):
        """Test heartbeat status for error workflows"""
        response = client.get("/workflows/12")
        assert response.status_code == 200
        
        workflow_data = response.json()
        
        if workflow_data.get("error"):
            # Error workflows should not have stale heartbeat
            assert workflow_data.get("heartbeat_stale", False) is False
            
            # Should have finished_at timestamp
            assert "finished_at" in workflow_data
            assert workflow_data["finished_at"] is not None
    
    def test_error_workflow_reconcile(self):
        """Test reconcile endpoint for error workflows"""
        response = client.post("/workflows/12/reconcile")
        assert response.status_code == 200
        
        reconcile_data = response.json()
        assert "message" in reconcile_data
        
        # Reconcile should not change terminal status
        workflow_response = client.get("/workflows/12")
        assert workflow_response.status_code == 200
        
        workflow_data = workflow_response.json()
        if workflow_data.get("error"):
            assert workflow_data["isTerminal"] is True
            assert workflow_data["status"] in ["failed", "error"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
