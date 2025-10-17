"""
Specific tests for workflow 12 (NEGISHI-165) error scenarios
Tests error display and handling for this specific workflow
"""
import pytest
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from crewai_app.main import app
from crewai_app.database import get_db, Workflow
from crewai_app.services.workflow_status_service import WorkflowStatusService

client = TestClient(app)

class TestWorkflow12ErrorSimulation:
    """Test error scenarios specifically for workflow 12 (NEGISHI-165)"""
    
    def setup_method(self):
        """Create a mock workflow with ID 12 for these tests"""
        from crewai_app.database import get_db, init_database
        init_database()
        
        db = next(get_db())
        
        # Clean up any existing workflow with ID 12 or jira_story_id NEGISHI-165
        db.query(Workflow).filter(
            (Workflow.id == 12) | (Workflow.jira_story_id == "NEGISHI-165")
        ).delete()
        db.commit()
        
        workflow = Workflow(
            id=12,
            name="NEGISHI-165: Test Error Workflow",
            jira_story_id="NEGISHI-165",
            jira_story_title="Test Error Workflow",
            jira_story_description="This is a test workflow designed to simulate an error.",
            status="failed",
            error="Simulated error: Database connection timeout.",
            started_at=datetime.utcnow() - timedelta(minutes=10),
            finished_at=datetime.utcnow() - timedelta(minutes=5),
            created_at=datetime.utcnow() - timedelta(minutes=15),
            updated_at=datetime.utcnow() - timedelta(minutes=5)
        )
        db.add(workflow)
        db.commit()
        self.workflow_id = workflow.id
        self.db_session = db
    
    def test_workflow_12_exists(self):
        """Test that workflow 12 exists and can be retrieved"""
        response = client.get("/workflows/12")
        assert response.status_code == 200
        
        workflow_data = response.json()
        assert workflow_data["id"] == 12
        assert "NEGISHI-165" in workflow_data["name"]
    
    def test_simulate_workflow_12_error(self):
        """Simulate an error scenario for workflow 12"""
        # Get current workflow state
        response = client.get("/workflows/12")
        assert response.status_code == 200
        
        workflow_data = response.json()
        original_status = workflow_data.get("status")
        
        # If workflow is not already failed, simulate an error
        if original_status != "failed":
            # Simulate error by calling reconcile endpoint
            reconcile_response = client.post("/workflows/12/reconcile")
            assert reconcile_response.status_code == 200
            
            # Check if status changed to failed
            updated_response = client.get("/workflows/12")
            assert updated_response.status_code == 200
            
            updated_data = updated_response.json()
            
            # If status changed to failed, check error information
            if updated_data.get("status") == "failed":
                assert updated_data["isTerminal"] is True
                assert "error" in updated_data
                assert updated_data["error"] is not None
                assert isinstance(updated_data["error"], str)
                assert len(updated_data["error"]) > 0
    
    def test_workflow_12_error_display_in_list(self):
        """Test error display for workflow 12 in workflows list"""
        response = client.get("/workflows")
        assert response.status_code == 200
        
        workflows = response.json()
        
        # Find workflow 12
        workflow_12 = next((w for w in workflows if w["id"] == 12), None)
        assert workflow_12 is not None
        
        # Check error information
        if workflow_12.get("error"):
            assert workflow_12["status"] in ["failed", "error"]
            assert workflow_12["isTerminal"] is True
            assert isinstance(workflow_12["error"], str)
            assert len(workflow_12["error"]) > 0
    
    def test_workflow_12_error_display_in_detail(self):
        """Test error display for workflow 12 in detail view"""
        response = client.get("/workflows/12")
        assert response.status_code == 200
        
        workflow_data = response.json()
        
        # Check error information in detail view
        if workflow_data.get("error"):
            assert workflow_data["status"] in ["failed", "error"]
            assert workflow_data["isTerminal"] is True
            assert "error" in workflow_data
            assert workflow_data["error"] is not None
            assert isinstance(workflow_data["error"], str)
            assert len(workflow_data["error"]) > 0
            
            # Check timestamps
            if workflow_data.get("finished_at"):
                assert workflow_data["finished_at"] is not None
                
                # Finished should be after created
                if workflow_data.get("created_at"):
                    created_at = datetime.fromisoformat(workflow_data["created_at"].replace('Z', '+00:00'))
                    finished_at = datetime.fromisoformat(workflow_data["finished_at"].replace('Z', '+00:00'))
                    assert finished_at >= created_at
    
    def test_workflow_12_error_message_content(self):
        """Test the content of error message for workflow 12"""
        response = client.get("/workflows/12")
        assert response.status_code == 200
        
        workflow_data = response.json()
        
        if workflow_data.get("error"):
            error_message = workflow_data["error"]
            
            # Error message should be meaningful
            assert isinstance(error_message, str)
            assert len(error_message) > 0
            
            # Should contain error-related keywords
            error_keywords = [
                "error", "failed", "timeout", "connection", "api", 
                "database", "exception", "unavailable", "invalid"
            ]
            
            error_lower = error_message.lower()
            has_error_keyword = any(keyword in error_lower for keyword in error_keywords)
            assert has_error_keyword, f"Error message should contain error-related keywords: {error_message}"
    
    def test_workflow_12_error_status_consistency(self):
        """Test status consistency for workflow 12 across endpoints"""
        # Get workflow data
        workflow_response = client.get("/workflows/12")
        assert workflow_response.status_code == 200
        workflow_data = workflow_response.json()
        
        # Get status data
        status_response = client.get("/workflows/12/status")
        assert status_response.status_code == 200
        status_data = status_response.json()
        
        # Check consistency
        assert workflow_data["status"] == status_data["status"]
        assert workflow_data["isTerminal"] == status_data["isTerminal"]
        
        if workflow_data.get("error") and status_data.get("error"):
            assert workflow_data["error"] == status_data["error"]
    
    def test_workflow_12_error_persistence(self):
        """Test that error information persists for workflow 12"""
        # Get workflow data multiple times
        responses = []
        for _ in range(3):
            response = client.get("/workflows/12")
            assert response.status_code == 200
            responses.append(response.json())
        
        # All responses should have consistent error information
        first_response = responses[0]
        for response_data in responses[1:]:
            assert response_data["status"] == first_response["status"]
            assert response_data["isTerminal"] == first_response["isTerminal"]
            
            if first_response.get("error"):
                assert response_data.get("error") == first_response["error"]
    
    def test_workflow_12_error_metadata(self):
        """Test metadata for workflow 12 error scenario"""
        response = client.get("/workflows/12")
        assert response.status_code == 200
        
        workflow_data = response.json()
        
        # Basic workflow information
        assert workflow_data["id"] == 12
        assert "NEGISHI-165" in workflow_data["name"]
        assert workflow_data["jira_story_id"] == "NEGISHI-165"
        
        # Error-specific information
        if workflow_data.get("error"):
            assert workflow_data["status"] in ["failed", "error"]
            assert workflow_data["isTerminal"] is True
            assert workflow_data["error"] is not None
            
            # Should have finished timestamp
            if workflow_data.get("finished_at"):
                assert workflow_data["finished_at"] is not None
    
    def test_workflow_12_error_reconcile_behavior(self):
        """Test reconcile behavior for workflow 12 with error"""
        response = client.post("/workflows/12/reconcile")
        assert response.status_code == 200
        
        reconcile_data = response.json()
        assert "message" in reconcile_data
        
        # Reconcile should not change terminal status
        workflow_response = client.get("/workflows/12")
        assert workflow_response.status_code == 200
        
        workflow_data = workflow_response.json()
        
        # If workflow has error, reconcile should not change it
        if workflow_data.get("error"):
            assert workflow_data["isTerminal"] is True
            assert workflow_data["status"] in ["failed", "error"]
    
    def test_workflow_12_error_workflow_execution(self):
        """Test workflow execution behavior for workflow 12 with error"""
        # Try to execute workflow 12
        response = client.post("/workflows/12/execute")
        
        # Should either succeed (if not terminal) or return appropriate error
        if response.status_code == 200:
            execution_data = response.json()
            assert "message" in execution_data
        else:
            # If workflow is terminal, should return appropriate error
            assert response.status_code in [400, 409, 422]
    
    def test_workflow_12_error_display_requirements(self):
        """Test that workflow 12 meets error display requirements"""
        response = client.get("/workflows/12")
        assert response.status_code == 200
        
        workflow_data = response.json()
        
        # Required fields for error display
        required_fields = ["id", "name", "status", "isTerminal"]
        for field in required_fields:
            assert field in workflow_data
        
        # Error-specific fields if present
        if workflow_data.get("error"):
            error_fields = ["error", "finished_at"]
            for field in error_fields:
                assert field in workflow_data
                assert workflow_data[field] is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
