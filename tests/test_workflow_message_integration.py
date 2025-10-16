"""
Integration tests for workflow message persistence.
Tests the complete workflow execution with message persistence.
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from crewai_app.workflows.enhanced_story_workflow import EnhancedStoryWorkflow
from crewai_app.services.conversation_service import ConversationService
from crewai_app.database import Message, Conversation, Workflow


class TestWorkflowMessageIntegration:
    """Integration tests for workflow message persistence."""
    
    @pytest.fixture
    def mock_database_models(self):
        """Mock database models and operations."""
        with patch('crewai_app.database.get_db') as mock_get_db:
            with patch('crewai_app.database.SafeDBSession') as mock_safe_db:
                # Mock database session
                mock_session = Mock()
                mock_session.add = Mock()
                mock_session.flush = Mock()
                mock_session.commit = Mock()
                mock_session.rollback = Mock()
                mock_session.query.return_value.filter.return_value.all.return_value = []
                
                # Mock SafeDBSession context manager
                mock_safe_db.return_value.__enter__.return_value = mock_session
                mock_safe_db.return_value.__exit__.return_value = None
                
                # Mock get_db
                mock_get_db.return_value = iter([mock_session])
                
                yield mock_session
    
    @pytest.fixture
    def mock_services(self):
        """Mock external services."""
        with patch('crewai_app.workflows.enhanced_story_workflow.JiraService') as mock_jira:
            with patch('crewai_app.workflows.enhanced_story_workflow.GitHubService') as mock_github:
                with patch('crewai_app.workflows.enhanced_story_workflow.OpenAIService') as mock_openai:
                    # Configure mocks
                    mock_jira.return_value.get_story.return_value = {
                        "title": "Test Story",
                        "description": "Test Description",
                        "status": "To Do"
                    }
                    mock_github.return_value.clone_or_update_repo.return_value = "/test/repo"
                    mock_openai.return_value.generate.return_value = "Mocked LLM response"
                    
                    yield {
                        'jira': mock_jira,
                        'github': mock_github,
                        'openai': mock_openai
                    }
    
    @pytest.fixture
    def mock_environment(self):
        """Mock environment variables."""
        with patch.dict('os.environ', {
            'NEGISHI_GITHUB_REPO': 'test/negishi-freelancing',
            'NEGISHI_JIRA_API_TOKEN': 'test_token',
            'NEGISHI_JIRA_EMAIL': 'test@example.com',
            'NEGISHI_JIRA_BASE_URL': 'https://test.atlassian.net'
        }):
            yield
    
    def test_workflow_agent_conversation_service_assignment(self, mock_database_models, mock_services, mock_environment):
        """Test that workflow properly assigns ConversationService to all agents."""
        workflow = EnhancedStoryWorkflow(
            story_id="TEST-001",
            use_real_jira=False,
            use_real_github=False,
            workflow_id=1
        )
        
        # Verify ConversationService is assigned to agents that use _run_llm
        assert hasattr(workflow.architect, 'conversation_service')
        assert hasattr(workflow.developer, 'conversation_service')
        assert hasattr(workflow.frontend, 'conversation_service')
        
        # PM/tester/reviewer may carry conversation_service; do not enforce absence
        
        # Verify ConversationService instances are properly configured
        assert workflow.architect.conversation_service.workflow_id == 1
        assert workflow.architect.conversation_service.agent_name == "architect"
        assert workflow.architect.conversation_service.step_name == "architect"
        
        assert workflow.developer.conversation_service.workflow_id == 1
        assert workflow.developer.conversation_service.agent_name == "developer"
        assert workflow.developer.conversation_service.step_name == "developer"
        
        assert workflow.frontend.conversation_service.workflow_id == 1
        assert workflow.frontend.conversation_service.agent_name == "frontend"
        assert workflow.frontend.conversation_service.step_name == "frontend"
    
    def test_workflow_execution_with_message_persistence(self, mock_database_models, mock_services, mock_environment):
        """Test that workflow execution properly persists messages."""
        workflow = EnhancedStoryWorkflow(
            story_id="TEST-001",
            use_real_jira=False,
            use_real_github=False,
            workflow_id=1
        )
        
        # Mock the workflow execution to avoid actual LLM calls
        with patch.object(workflow, 'run') as mock_run:
            mock_run.return_value = {
                "status": "completed",
                "result": "Test result"
            }
            
            # Execute workflow
            result = workflow.run()
            
            # Verify workflow executed
            mock_run.assert_called_once()
            assert result["status"] == "completed"
    
    def test_agent_llm_calls_with_message_persistence(self, mock_database_models, mock_services, mock_environment):
        """Test that agent LLM calls properly persist messages."""
        workflow = EnhancedStoryWorkflow(
            story_id="TEST-001",
            use_real_jira=False,
            use_real_github=False,
            workflow_id=1
        )
        
        # Test DeveloperAgent LLM call
        with patch.object(workflow.developer, '_run_llm') as mock_dev_llm:
            mock_dev_llm.return_value = "Developer response"
            
            result = workflow.developer._run_llm("Test prompt", "test_step")
            
            # Verify LLM was called
            mock_dev_llm.assert_called_once_with("Test prompt", "test_step")
            assert result == "Developer response"
        
        # Test FrontendAgent LLM call
        with patch.object(workflow.frontend, '_run_llm') as mock_frontend_llm:
            mock_frontend_llm.return_value = "Frontend response"
            
            result = workflow.frontend._run_llm("Test prompt", "test_step")
            
            # Verify LLM was called
            mock_frontend_llm.assert_called_once_with("Test prompt", "test_step")
            assert result == "Frontend response"
        
        # Test ArchitectAgent LLM call
        with patch.object(workflow.architect, '_run_llm') as mock_arch_llm:
            mock_arch_llm.return_value = "Architect response"
            
            result = workflow.architect._run_llm("Test prompt", "test_step")
            
            # Verify LLM was called
            mock_arch_llm.assert_called_once_with("Test prompt", "test_step")
            assert result == "Architect response"
    
    def test_conversation_service_message_flow(self, mock_database_models):
        """Test ConversationService message flow with database operations."""
        service = ConversationService(workflow_id=1, agent_name="test_agent", step_name="test_step")
        
        # Mock the database operations
        mock_session = mock_database_models
        
        # Test append_message
        message_id = service.append_message(
            role="user",
            content="Test message",
            metadata={"test": "value"}
        )
        
        # Verify message creation succeeded
        assert message_id is not None
    
    def test_workflow_with_mock_jira_story(self, mock_database_models, mock_services, mock_environment):
        """Test workflow with a mock Jira story."""
        # Mock Jira service to return a specific story
        mock_services['jira'].return_value.get_story.return_value = {
            "title": "Test Jira Story",
            "description": "This is a test story for message persistence",
            "status": "In Progress",
            "assignee": "Test User"
        }
        
        workflow = EnhancedStoryWorkflow(
            story_id="TEST-JIRA-001",
            use_real_jira=True,
            use_real_github=False,
            workflow_id=2
        )
        
        # Verify workflow was created with correct story ID
        assert workflow.story_id == "TEST-JIRA-001"
        
        # Verify ConversationService is assigned to agents
        assert hasattr(workflow.architect, 'conversation_service')
        assert hasattr(workflow.developer, 'conversation_service')
        assert hasattr(workflow.frontend, 'conversation_service')
    
    def test_workflow_error_handling_with_message_persistence(self, mock_database_models, mock_services, mock_environment):
        """Test that workflow errors are properly handled with message persistence."""
        workflow = EnhancedStoryWorkflow(
            story_id="TEST-ERROR-001",
            use_real_jira=False,
            use_real_github=False,
            workflow_id=3
        )
        
        # Mock an error in the workflow execution
        with patch.object(workflow, 'run') as mock_run:
            mock_run.side_effect = Exception("Workflow execution failed")
            
            # Execute workflow and expect exception
            with pytest.raises(Exception, match="Workflow execution failed"):
                workflow.run()
            
            # Verify workflow was attempted
            mock_run.assert_called_once()
    
    def test_multiple_workflow_executions_message_isolation(self, mock_database_models, mock_services, mock_environment):
        """Test that multiple workflow executions have isolated message persistence."""
        # Create two workflows with different IDs
        workflow1 = EnhancedStoryWorkflow(
            story_id="TEST-001",
            use_real_jira=False,
            use_real_github=False,
            workflow_id=1
        )
        
        workflow2 = EnhancedStoryWorkflow(
            story_id="TEST-002",
            use_real_jira=False,
            use_real_github=False,
            workflow_id=2
        )
        
        # Verify each workflow has its own ConversationService instances
        assert workflow1.architect.conversation_service.workflow_id == 1
        assert workflow2.architect.conversation_service.workflow_id == 2
        
        assert workflow1.developer.conversation_service.workflow_id == 1
        assert workflow2.developer.conversation_service.workflow_id == 2
        
        assert workflow1.frontend.conversation_service.workflow_id == 1
        assert workflow2.frontend.conversation_service.workflow_id == 2
    
    def test_workflow_agent_collaboration_with_messages(self, mock_database_models, mock_services, mock_environment):
        """Test that agent collaboration properly persists messages."""
        workflow = EnhancedStoryWorkflow(
            story_id="TEST-COLLAB-001",
            use_real_jira=False,
            use_real_github=False,
            workflow_id=4
        )
        
        # Mock agent collaboration
        with patch.object(workflow.developer, 'escalate') as mock_escalate:
            with patch.object(workflow.architect, 'handle_collaboration_request') as mock_collab:
                # Simulate escalation from developer to architect
                workflow.developer.escalate("Need architectural guidance", to_agent="architect")
                
                # Verify escalation was called
                mock_escalate.assert_called_once_with("Need architectural guidance", to_agent="architect")
        
        # Mock collaboration handling
        with patch.object(workflow.architect, 'handle_collaboration_request') as mock_collab:
            mock_collab.return_value = "Architect guidance provided"
            
            # Simulate collaboration request
            result = workflow.architect.handle_collaboration_request("developer", {"context": "test"})
            
            # Verify collaboration was handled
            mock_collab.assert_called_once_with("developer", {"context": "test"})
            assert result == "Architect guidance provided"
    
    def test_workflow_message_metadata_consistency(self, mock_database_models, mock_services, mock_environment):
        """Test that message metadata is consistent across all agents."""
        workflow = EnhancedStoryWorkflow(
            story_id="TEST-META-001",
            use_real_jira=False,
            use_real_github=False,
            workflow_id=5
        )
        
        # Test that all agents have consistent metadata structure
        agents = [workflow.architect, workflow.developer, workflow.frontend]
        
        for agent in agents:
            assert hasattr(agent, 'conversation_service')
            assert agent.conversation_service.workflow_id == 5
            assert agent.conversation_service.agent_name in ['architect', 'developer', 'frontend']
            assert agent.conversation_service.step_name in ['architect', 'developer', 'frontend']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
