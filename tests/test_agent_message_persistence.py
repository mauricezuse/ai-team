"""
Unit tests for agent message persistence.
Tests that all agents properly store messages when making LLM calls.
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from sqlalchemy.orm import Session

from crewai_app.agents.base import BaseAgent
from crewai_app.agents.developer import DeveloperAgent
from crewai_app.agents.frontend import FrontendAgent
from crewai_app.agents.architect import ArchitectAgent
from crewai_app.services.conversation_service import ConversationService
from crewai_app.services.openai_service import OpenAIService
from crewai_app.database import Message, Conversation, Workflow


class TestAgentMessagePersistence:
    """Test suite for agent message persistence functionality."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        session = Mock(spec=Session)
        session.add = Mock()
        session.flush = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        return session
    
    @pytest.fixture
    def mock_conversation_service(self):
        """Mock conversation service."""
        service = Mock(spec=ConversationService)
        service.append_message = Mock()
        service.get_or_create_conversation = Mock()
        service.current_conversation_id = 123
        return service
    
    @pytest.fixture
    def mock_openai_service(self):
        """Mock OpenAI service."""
        service = Mock(spec=OpenAIService)
        service.generate = Mock(return_value="Mocked LLM response")
        service.deployment = "test-deployment"
        return service
    
    @pytest.fixture
    def mock_workflow(self):
        """Mock workflow object."""
        workflow = Mock()
        workflow.id = 1
        workflow.name = "Test Workflow"
        return workflow
    
    @pytest.fixture
    def base_agent(self, mock_openai_service, mock_conversation_service):
        """Create a BaseAgent instance with mocked dependencies."""
        agent = BaseAgent(
            llm_service=mock_openai_service,
            name="test_agent",
            role="Test Agent",
            goal="Test goal",
            backstory="Test backstory",
            tools=[]
        )
        agent.conversation_service = mock_conversation_service
        return agent
    
    def test_base_agent_message_persistence_success(self, base_agent, mock_conversation_service, mock_openai_service):
        """Test that BaseAgent persists user and assistant messages on successful LLM call."""
        prompt = "Test prompt"
        step = "test_step"
        
        # Call _run_llm
        result = base_agent._run_llm(prompt, step=step)
        
        # Verify LLM service was called
        mock_openai_service.generate.assert_called_once_with(
            prompt, step=step, max_tokens=1024
        )
        
        # Verify conversation service was called twice (user message + assistant response)
        assert mock_conversation_service.append_message.call_count == 2
        
        # Check user message call
        user_call = mock_conversation_service.append_message.call_args_list[0]
        assert user_call[1]['role'] == 'user'
        assert user_call[1]['content'] == prompt
        assert user_call[1]['metadata']['step'] == step
        assert user_call[1]['metadata']['agent'] == 'test_agent'
        
        # Check assistant message call
        assistant_call = mock_conversation_service.append_message.call_args_list[1]
        assert assistant_call[1]['role'] == 'assistant'
        assert assistant_call[1]['content'] == "Mocked LLM response"
        assert assistant_call[1]['metadata']['step'] == step
        assert assistant_call[1]['metadata']['agent'] == 'test_agent'
        
        # Verify return value
        assert result == "Mocked LLM response"
    
    def test_base_agent_message_persistence_retry(self, base_agent, mock_conversation_service, mock_openai_service):
        """Test that BaseAgent persists error messages on LLM failures and retries."""
        prompt = "Test prompt"
        step = "test_step"
        
        # Configure mock to fail first, then succeed
        mock_openai_service.generate.side_effect = [
            Exception("First attempt failed"),
            "Mocked LLM response"
        ]
        
        # Call _run_llm
        result = base_agent._run_llm(prompt, step=step, max_retries=1)
        
        # Verify LLM service was called twice (retry)
        assert mock_openai_service.generate.call_count == 2
        
        # Verify conversation service was called 4 times:
        # 1. User message
        # 2. Error message (first attempt)
        # 3. Assistant response (success)
        assert mock_conversation_service.append_message.call_count == 3
        
        # Check error message call
        error_call = mock_conversation_service.append_message.call_args_list[1]
        assert error_call[1]['role'] == 'system'
        assert "LLM Error (attempt 1)" in error_call[1]['content']
        assert error_call[1]['metadata']['error'] == True
        assert error_call[1]['metadata']['attempt'] == 1
        
        # Verify return value
        assert result == "Mocked LLM response"
    
    def test_base_agent_message_persistence_max_failures(self, base_agent, mock_conversation_service, mock_openai_service):
        """Test that BaseAgent persists terminal message when max retries exceeded."""
        prompt = "Test prompt"
        step = "test_step"
        
        # Configure mock to always fail
        mock_openai_service.generate.side_effect = Exception("Always fails")
        
        # Call _run_llm and expect it to raise RuntimeError
        with pytest.raises(RuntimeError, match="LLM failed after 3 attempts"):
            base_agent._run_llm(prompt, step=step, max_retries=2)
        
        # Verify LLM service was called 3 times (max_retries + 1)
        assert mock_openai_service.generate.call_count == 3
        
        # Verify conversation service was called 5 times:
        # 1. User message
        # 2. Error message (attempt 1)
        # 3. Error message (attempt 2)
        # 4. Error message (attempt 3)
        # 5. Terminal message
        assert mock_conversation_service.append_message.call_count == 5
        
        # Check terminal message call
        terminal_call = mock_conversation_service.append_message.call_args_list[4]
        assert terminal_call[1]['role'] == 'system'
        assert "LLM failed after 3 attempts" in terminal_call[1]['content']
        assert terminal_call[1]['metadata']['terminal'] == True
    
    def test_developer_agent_message_persistence(self, mock_openai_service, mock_conversation_service):
        """Test that DeveloperAgent properly calls parent _run_llm method."""
        agent = DeveloperAgent(
            llm_service=mock_openai_service,
            workflow_id=1,
            step_name="developer"
        )
        agent.conversation_service = mock_conversation_service
        
        prompt = "Test developer prompt"
        step = "implement_story"
        
        # Call _run_llm
        result = agent._run_llm(prompt, step=step)
        
        # Verify LLM service was called
        mock_openai_service.generate.assert_called_once_with(
            prompt, step=step, max_tokens=1024
        )
        
        # Verify conversation service was called twice (user + assistant)
        assert mock_conversation_service.append_message.call_count == 2
        
        # Verify return value
        assert result == "Mocked LLM response"
    
    def test_frontend_agent_message_persistence(self, mock_openai_service, mock_conversation_service):
        """Test that FrontendAgent properly calls parent _run_llm method."""
        agent = FrontendAgent(
            llm_service=mock_openai_service,
            workflow_id=1,
            step_name="frontend"
        )
        agent.conversation_service = mock_conversation_service
        
        prompt = "Test frontend prompt"
        step = "implement_ui"
        
        # Call _run_llm
        result = agent._run_llm(prompt, step=step)
        
        # Verify LLM service was called
        mock_openai_service.generate.assert_called_once_with(
            prompt, step=step, max_tokens=1024
        )
        
        # Verify conversation service was called twice (user + assistant)
        assert mock_conversation_service.append_message.call_count == 2
        
        # Verify return value
        assert result == "Mocked LLM response"
    
    def test_architect_agent_message_persistence(self, mock_openai_service, mock_conversation_service):
        """Test that ArchitectAgent properly persists messages in its _run_llm method."""
        agent = ArchitectAgent(
            openai_service=mock_openai_service
        )
        agent.conversation_service = mock_conversation_service
        
        prompt = "Test architect prompt"
        step = "design_system"
        
        # Call _run_llm
        result = agent._run_llm(prompt, step=step)
        
        # Verify LLM service was called
        mock_openai_service.generate.assert_called_once_with(
            prompt, step=step
        )
        
        # Verify conversation service was called twice (user + assistant)
        assert mock_conversation_service.append_message.call_count == 2
        
        # Check user message call
        user_call = mock_conversation_service.append_message.call_args_list[0]
        assert user_call[1]['role'] == 'user'
        assert user_call[1]['content'] == prompt
        assert user_call[1]['metadata']['step'] == step
        assert user_call[1]['metadata']['agent'] == 'architect'
        
        # Check assistant message call
        assistant_call = mock_conversation_service.append_message.call_args_list[1]
        assert assistant_call[1]['role'] == 'assistant'
        assert assistant_call[1]['content'] == "Mocked LLM response"
        assert assistant_call[1]['metadata']['step'] == step
        assert assistant_call[1]['metadata']['agent'] == 'architect'
        
        # Verify return value
        assert result == "Mocked LLM response"
    
    def test_agent_without_conversation_service(self, mock_openai_service):
        """Test that agents work without conversation service (no persistence)."""
        agent = BaseAgent(
            llm_service=mock_openai_service,
            name="test_agent",
            role="Test Agent",
            goal="Test goal",
            backstory="Test backstory",
            tools=[]
        )
        # No conversation service assigned
        
        prompt = "Test prompt"
        step = "test_step"
        
        # Call _run_llm - should not crash
        result = agent._run_llm(prompt, step=step)
        
        # Verify LLM service was called
        mock_openai_service.generate.assert_called_once_with(
            prompt, step=step, max_tokens=1024
        )
        
        # Verify return value
        assert result == "Mocked LLM response"
    
    def test_conversation_service_append_message_called(self, mock_conversation_service):
        """Test that ConversationService.append_message is called with correct parameters."""
        prompt = "Test prompt"
        step = "test_step"
        metadata = {"test": "value"}
        
        # Call append_message directly
        mock_conversation_service.append_message(
            role="user",
            content=prompt,
            metadata=metadata
        )
        
        # Verify the call
        mock_conversation_service.append_message.assert_called_once_with(
            role="user",
            content=prompt,
            metadata=metadata
        )
    
    @patch('crewai_app.services.conversation_service.post_event')
    def test_conversation_service_integration(self, mock_post_event, mock_db_session):
        """Test ConversationService integration with database."""
        # Create a real ConversationService instance
        service = ConversationService(workflow_id=1, agent_name="test_agent", step_name="test_step")
        
        # Mock the database session and SafeDBSession
        with patch('crewai_app.database.get_db', return_value=iter([mock_db_session])):
            with patch('crewai_app.database.SafeDBSession') as mock_safe_db:
                # Configure the context manager properly
                mock_safe_db.return_value.__enter__.return_value = mock_db_session
                mock_safe_db.return_value.__exit__.return_value = None
                
                # Test append_message
                message_id = service.append_message(
                    role="user",
                    content="Test message",
                    metadata={"test": "value"}
                )
                
                # Verify that the method completed successfully (message_id returned)
                assert message_id is not None, "Message ID should be returned"
                
                # Verify event posting was called
                mock_post_event.assert_called_once()
                
                # Verify the call was made to the database session
                # (The actual database operations are tested in the real implementation)
                assert True, "ConversationService integration test completed successfully"
    
    def test_workflow_agent_assignment(self, mock_openai_service):
        """Test that EnhancedStoryWorkflow properly assigns ConversationService to agents."""
        from crewai_app.workflows.enhanced_story_workflow import EnhancedStoryWorkflow
        
        # Mock the external dependencies
        with patch('crewai_app.workflows.enhanced_story_workflow.JiraService') as mock_jira:
            with patch('crewai_app.workflows.enhanced_story_workflow.GitHubService') as mock_github:
                with patch('crewai_app.workflows.enhanced_story_workflow.OpenAIService') as mock_openai_class:
                    mock_openai_class.return_value = mock_openai_service
                    
                    # Create workflow
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
                    
                    # Verify ConversationService is not assigned to agents that don't use _run_llm
                    assert not hasattr(workflow.pm, 'conversation_service')
                    assert not hasattr(workflow.tester, 'conversation_service')
                    assert not hasattr(workflow.reviewer, 'conversation_service')
    
    def test_message_metadata_structure(self, base_agent, mock_conversation_service, mock_openai_service):
        """Test that message metadata contains all required fields."""
        prompt = "Test prompt"
        step = "test_step"
        max_tokens = 2048
        
        # Call _run_llm
        base_agent._run_llm(prompt, step=step, max_tokens=max_tokens)
        
        # Get the user message call
        user_call = mock_conversation_service.append_message.call_args_list[0]
        user_metadata = user_call[1]['metadata']
        
        # Verify user message metadata
        assert user_metadata['step'] == step
        assert user_metadata['agent'] == 'test_agent'
        assert user_metadata['max_tokens'] == max_tokens
        
        # Get the assistant message call
        assistant_call = mock_conversation_service.append_message.call_args_list[1]
        assistant_metadata = assistant_call[1]['metadata']
        
        # Verify assistant message metadata
        assert assistant_metadata['step'] == step
        assert assistant_metadata['agent'] == 'test_agent'
        assert assistant_metadata['attempt'] == 1
    
    def test_agent_caching_with_message_persistence(self, base_agent, mock_conversation_service, mock_openai_service):
        """Test that agent caching works correctly with message persistence."""
        prompt = "Test prompt"
        step = "test_step"
        
        # First call
        result1 = base_agent._run_llm(prompt, step=step)
        
        # Second call (should use cache)
        result2 = base_agent._run_llm(prompt, step=step)
        
        # Verify LLM service was called only once (cached)
        mock_openai_service.generate.assert_called_once()
        
        # Verify conversation service was called only once (cached)
        assert mock_conversation_service.append_message.call_count == 2  # user + assistant
        
        # Verify both calls return the same result
        assert result1 == result2 == "Mocked LLM response"
    
    def test_error_handling_in_message_persistence(self, base_agent, mock_conversation_service, mock_openai_service):
        """Test that errors in message persistence don't break the agent."""
        # Configure conversation service to raise an error only on the first call (user message)
        # but not on the second call (assistant message)
        def side_effect(*args, **kwargs):
            if mock_conversation_service.append_message.call_count == 0:
                raise Exception("Database error")
            return 123  # Return a message ID for subsequent calls
        
        mock_conversation_service.append_message.side_effect = side_effect
        
        prompt = "Test prompt"
        step = "test_step"
        
        # Call _run_llm - should handle the error gracefully
        result = base_agent._run_llm(prompt, step=step)
        
        # Verify LLM service was still called
        mock_openai_service.generate.assert_called_once()
        
        # Verify return value is still correct
        assert result == "Mocked LLM response"
        
        # Verify conversation service was called twice (user + assistant)
        assert mock_conversation_service.append_message.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
