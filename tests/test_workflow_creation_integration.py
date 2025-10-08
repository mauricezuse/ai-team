"""
Integration tests for workflow creation functionality.
Tests the actual API endpoints with real database operations.
"""

import pytest
import json
from fastapi.testclient import TestClient
from crewai_app.main import app
from crewai_app.database import get_db, init_database, Workflow
from sqlalchemy.orm import Session


class TestWorkflowCreationIntegration:
    """Test workflow creation functionality with real database."""
    
    def setup_method(self):
        """Set up test client and initialize database."""
        self.client = TestClient(app)
        # Initialize database for testing
        init_database()
    
    def test_create_workflow_from_jira_success(self):
        """Test successful workflow creation from Jira story."""
        # Skip this test if Jira credentials are not configured
        import os
        if not (os.getenv("NEGISHI_JIRA_API_TOKEN") and os.getenv("NEGISHI_JIRA_EMAIL") and os.getenv("NEGISHI_JIRA_BASE_URL")):
            pytest.skip("Jira credentials not configured - skipping real Jira test")
        
        # Use a real story ID that exists in your Jira instance
        story_id = "NEGISHI-178"  # Use an existing story ID
        
        # Make the API call
        response = self.client.post(f"/workflows/from-jira/{story_id}")
        
        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert "message" in response_data
        assert story_id in response_data["message"]
        assert "workflow_id" in response_data
        
        # Verify the workflow exists in the database (may already exist)
        db = next(get_db())
        workflow = db.query(Workflow).filter(Workflow.jira_story_id == story_id).first()
        assert workflow is not None
        assert workflow.jira_story_id == story_id
        # Status could be "pending" (new) or "completed" (existing)
        assert workflow.status in ["pending", "completed"]
        db.close()
    
    def test_create_workflow_from_jira_already_exists(self):
        """Test workflow creation when workflow already exists."""
        # Use a story ID that already exists
        story_id = "NEGISHI-178"
        
        # Make the API call
        response = self.client.post(f"/workflows/from-jira/{story_id}")
        
        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert "already exists" in response_data["message"]
        assert story_id in response_data["message"]
    
    def test_create_workflow_manual_success(self):
        """Test successful manual workflow creation."""
        import time
        # Use a unique story ID to avoid conflicts
        unique_id = f"NEGISHI-TEST-{int(time.time())}"
        workflow_data = {
            "jira_story_id": unique_id,
            "jira_story_title": "Test Manual Workflow",
            "jira_story_description": "This is a test workflow created manually.",
            "repository_url": "https://github.com/mauricezuse/negishi-freelancing",
            "target_branch": "main"
        }
        
        # Make the API call
        response = self.client.post("/workflows", json=workflow_data)
        
        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["jira_story_id"] == unique_id
        assert response_data["jira_story_title"] == "Test Manual Workflow"
        assert response_data["status"] == "pending"
        
        # Verify the workflow was created in the database
        db = next(get_db())
        workflow = db.query(Workflow).filter(Workflow.jira_story_id == unique_id).first()
        assert workflow is not None
        assert workflow.jira_story_id == unique_id
        assert workflow.status == "pending"
        db.close()
    
    def test_create_workflow_manual_duplicate(self):
        """Test manual workflow creation when workflow already exists."""
        workflow_data = {
            "jira_story_id": "NEGISHI-178",  # This already exists
            "jira_story_title": "Duplicate Test",
            "jira_story_description": "This should fail because it already exists.",
            "repository_url": "https://github.com/mauricezuse/negishi-freelancing",
            "target_branch": "main"
        }
        
        # Make the API call
        response = self.client.post("/workflows", json=workflow_data)
        
        # Assertions
        assert response.status_code == 400
        response_data = response.json()
        assert "already exists" in response_data["detail"]
    
    def test_get_workflows_list(self):
        """Test getting the list of workflows."""
        # Make the API call
        response = self.client.get("/workflows")
        
        # Assertions
        assert response.status_code == 200
        workflows = response.json()
        assert isinstance(workflows, list)
        assert len(workflows) > 0
        
        # Check that we have the expected workflows
        story_ids = [w["jira_story_id"] for w in workflows]
        assert "NEGISHI-178" in story_ids
        assert "NEGISHI-175" in story_ids
    
    def test_get_workflow_detail(self):
        """Test getting a specific workflow."""
        # First get the list to find a workflow ID
        response = self.client.get("/workflows")
        assert response.status_code == 200
        workflows = response.json()
        assert len(workflows) > 0
        
        workflow_id = workflows[0]["id"]
        
        # Get the specific workflow
        response = self.client.get(f"/workflows/{workflow_id}")
        
        # Assertions
        assert response.status_code == 200
        workflow = response.json()
        assert workflow["id"] == workflow_id
        assert "jira_story_id" in workflow
        assert "status" in workflow
    
    def test_get_workflow_detail_not_found(self):
        """Test getting a workflow that doesn't exist."""
        # Use a non-existent workflow ID
        workflow_id = 99999
        
        # Get the specific workflow
        response = self.client.get(f"/workflows/{workflow_id}")
        
        # Assertions
        assert response.status_code == 404
        response_data = response.json()
        assert "not found" in response_data["detail"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
