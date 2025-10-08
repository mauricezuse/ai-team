"""
Unit tests for workflow creation functionality.
Tests the backend API endpoints and frontend service calls.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from crewai_app.main import app
from crewai_app.database import Workflow, get_db
from crewai_app.services.jira_service import JiraService


class TestWorkflowCreation:
    """Test workflow creation functionality."""
    
    def setup_method(self):
        """Set up test client and mock database."""
        self.client = TestClient(app)
        self.mock_db = Mock(spec=Session)
        
    def test_create_workflow_from_jira_success(self):
        """Test successful workflow creation from Jira story."""
        # Mock Jira service to return mock data
        mock_story_data = {
            "key": "NEGISHI-167",
            "fields": {
                "summary": "Optimize database performance",
                "description": "Analyze and optimize database queries, add proper indexing, and implement caching strategies."
            }
        }
        
        with patch('crewai_app.services.jira_service.JiraService') as mock_jira_service:
            mock_jira_instance = Mock()
            mock_jira_instance.get_story.return_value = mock_story_data
            mock_jira_service.return_value = mock_jira_instance
            
            # Mock database operations
            with patch('crewai_app.main.get_db') as mock_get_db:
                mock_get_db.return_value = self.mock_db
                
                # Mock database query to return no existing workflow
                self.mock_db.query.return_value.filter.return_value.first.return_value = None
                
                # Mock database add and commit
                self.mock_db.add = Mock()
                self.mock_db.commit = Mock()
                self.mock_db.refresh = Mock()
                
                # Create a mock workflow object
                mock_workflow = Mock()
                mock_workflow.id = 6
                mock_workflow.name = "NEGISHI-167: Optimize database performance"
                mock_workflow.jira_story_id = "NEGISHI-167"
                mock_workflow.jira_story_title = "Optimize database performance"
                mock_workflow.jira_story_description = "Analyze and optimize database queries, add proper indexing, and implement caching strategies."
                mock_workflow.status = "pending"
                mock_workflow.repository_url = "https://github.com/mauricezuse/negishi-freelancing"
                mock_workflow.target_branch = "main"
                
                self.mock_db.refresh.return_value = mock_workflow
                
                # Make the API call
                response = self.client.post("/workflows/from-jira/NEGISHI-167")
                
                # Assertions
                assert response.status_code == 200
                response_data = response.json()
                assert "message" in response_data
                assert "NEGISHI-167" in response_data["message"]
                
                # Verify database operations
                self.mock_db.add.assert_called_once()
                self.mock_db.commit.assert_called_once()
                self.mock_db.refresh.assert_called_once()
    
    def test_create_workflow_from_jira_story_not_found(self):
        """Test workflow creation when Jira story is not found."""
        with patch('crewai_app.services.jira_service.JiraService') as mock_jira_service:
            mock_jira_instance = Mock()
            mock_jira_instance.get_story.return_value = None
            mock_jira_service.return_value = mock_jira_instance
            
            # Mock database operations
            with patch('crewai_app.main.get_db') as mock_get_db:
                mock_get_db.return_value = self.mock_db
                
                # Mock database query to return no existing workflow
                self.mock_db.query.return_value.filter.return_value.first.return_value = None
                
                # Make the API call
                response = self.client.post("/workflows/from-jira/NEGISHI-999")
                
                # Assertions
                assert response.status_code == 404
                response_data = response.json()
                assert "Could not retrieve story NEGISHI-999 from Jira" in response_data["detail"]
    
    def test_create_workflow_from_jira_already_exists(self):
        """Test workflow creation when workflow already exists."""
        # Mock existing workflow
        mock_existing_workflow = Mock()
        mock_existing_workflow.id = 1
        mock_existing_workflow.jira_story_id = "NEGISHI-165"
        
        with patch('crewai_app.main.get_db') as mock_get_db:
            mock_get_db.return_value = self.mock_db
            
            # Mock database query to return existing workflow
            self.mock_db.query.return_value.filter.return_value.first.return_value = mock_existing_workflow
            
            # Make the API call
            response = self.client.post("/workflows/from-jira/NEGISHI-165")
            
            # Assertions
            assert response.status_code == 200
            response_data = response.json()
            assert "already exists" in response_data["message"]
            assert "NEGISHI-165" in response_data["message"]
    
    def test_create_workflow_manual_success(self):
        """Test successful manual workflow creation."""
        workflow_data = {
            "jira_story_id": "NEGISHI-166",
            "jira_story_title": "Add real-time notifications feature",
            "jira_story_description": "Implement WebSocket-based real-time notifications for user interactions and system events.",
            "repository_url": "https://github.com/mauricezuse/negishi-freelancing",
            "target_branch": "main"
        }
        
        with patch('crewai_app.main.get_db') as mock_get_db:
            mock_get_db.return_value = self.mock_db
            
            # Mock database query to return no existing workflow
            self.mock_db.query.return_value.filter.return_value.first.return_value = None
            
            # Mock database add and commit
            self.mock_db.add = Mock()
            self.mock_db.commit = Mock()
            self.mock_db.refresh = Mock()
            
            # Create a mock workflow object
            mock_workflow = Mock()
            mock_workflow.id = 1
            mock_workflow.name = "NEGISHI-166: Add real-time notifications feature"
            mock_workflow.jira_story_id = "NEGISHI-166"
            mock_workflow.jira_story_title = "Add real-time notifications feature"
            mock_workflow.jira_story_description = "Implement WebSocket-based real-time notifications for user interactions and system events."
            mock_workflow.status = "pending"
            mock_workflow.repository_url = "https://github.com/mauricezuse/negishi-freelancing"
            mock_workflow.target_branch = "main"
            
            self.mock_db.refresh.return_value = mock_workflow
            
            # Make the API call
            response = self.client.post("/workflows", json=workflow_data)
            
            # Assertions
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["jira_story_id"] == "NEGISHI-166"
            assert response_data["jira_story_title"] == "Add real-time notifications feature"
            assert response_data["status"] == "pending"
            
            # Verify database operations
            self.mock_db.add.assert_called_once()
            self.mock_db.commit.assert_called_once()
            self.mock_db.refresh.assert_called_once()
    
    def test_create_workflow_manual_duplicate(self):
        """Test manual workflow creation when workflow already exists."""
        workflow_data = {
            "jira_story_id": "NEGISHI-165",
            "jira_story_title": "Implement advanced user authentication system",
            "jira_story_description": "Create a comprehensive authentication system with multi-factor authentication, role-based access control, and secure session management.",
            "repository_url": "https://github.com/mauricezuse/negishi-freelancing",
            "target_branch": "main"
        }
        
        # Mock existing workflow
        mock_existing_workflow = Mock()
        mock_existing_workflow.id = 1
        mock_existing_workflow.jira_story_id = "NEGISHI-165"
        
        with patch('crewai_app.main.get_db') as mock_get_db:
            mock_get_db.return_value = self.mock_db
            
            # Mock database query to return existing workflow
            self.mock_db.query.return_value.filter.return_value.first.return_value = mock_existing_workflow
            
            # Make the API call
            response = self.client.post("/workflows", json=workflow_data)
            
            # Assertions
            assert response.status_code == 400
            response_data = response.json()
            assert "already exists" in response_data["detail"]
    
    def test_jira_service_mock_data(self):
        """Test that Jira service returns proper mock data when credentials are not configured."""
        # Test with no credentials (should use mock data)
        with patch.dict('os.environ', {}, clear=True):
            jira_service = JiraService(use_real=False)
            story_data = jira_service.get_story("NEGISHI-165")
            
            assert story_data is not None
            assert story_data["key"] == "NEGISHI-165"
            assert "summary" in story_data["fields"]
            assert "description" in story_data["fields"]
            assert story_data["fields"]["summary"] == "Implement advanced user authentication system"
    
    def test_jira_service_unknown_story(self):
        """Test that Jira service returns default mock data for unknown stories."""
        jira_service = JiraService(use_real=False)
        story_data = jira_service.get_story("NEGISHI-999")
        
        assert story_data is not None
        assert story_data["key"] == "NEGISHI-999"
        assert "summary" in story_data["fields"]
        assert "description" in story_data["fields"]
        assert "Mock story: NEGISHI-999" in story_data["fields"]["summary"]


class TestWorkflowServiceIntegration:
    """Test workflow service integration with frontend."""
    
    def test_workflow_service_create_from_jira(self):
        """Test that WorkflowService.createWorkflowFromJira works correctly."""
        from frontend.src.app.core.services.workflow.service import WorkflowService
        from unittest.mock import Mock, patch
        
        # Mock HTTP client
        mock_http = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "message": "Workflow created successfully for NEGISHI-165",
            "workflow_id": 1,
            "story_id": "NEGISHI-165",
            "title": "Implement advanced user authentication system"
        }
        mock_http.post.return_value = mock_response
        
        # Create service instance
        service = WorkflowService()
        service.http = mock_http
        
        # Test the method
        result = service.createWorkflowFromJira("NEGISHI-165")
        
        # Verify the HTTP call was made correctly
        mock_http.post.assert_called_once_with(
            "/api/workflows/from-jira/NEGISHI-165",
            json={}
        )
        
        # Verify the result
        assert result == mock_response


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
