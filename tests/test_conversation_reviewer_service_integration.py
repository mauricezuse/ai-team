"""
Integration tests for ConversationReviewService with real database interactions.
Tests the service layer with actual database operations.
"""
import pytest
from unittest.mock import Mock, patch
from crewai_app.services.conversation_review_service import ConversationReviewService
from crewai_app.database import get_db, init_database, Workflow, Conversation, Message
from datetime import datetime, timedelta
import json


class TestConversationReviewServiceIntegration:
    """Integration tests for ConversationReviewService."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test database and create comprehensive test data."""
        init_database()
        db = next(get_db())
        
        # Clean up any existing test data
        db.query(Message).delete()
        db.query(Conversation).delete()
        db.query(Workflow).delete()
        db.commit()
        
        # Create a comprehensive test workflow
        self.workflow = Workflow(
            id=1,
            name="Integration Test Workflow",
            jira_story_id="INTEGRATION-001",
            jira_story_title="Test Integration Story",
            jira_story_description="A comprehensive test story for integration testing",
            status="completed",
            started_at=datetime.utcnow() - timedelta(hours=2),
            finished_at=datetime.utcnow() - timedelta(minutes=30),
            created_at=datetime.utcnow() - timedelta(hours=3),
            updated_at=datetime.utcnow() - timedelta(minutes=30)
        )
        db.add(self.workflow)
        db.commit()
        
        # Create multiple conversations with different agents
        self.conversations = []
        agents = ["Product Manager", "Solution Architect", "Backend Developer", "Frontend Developer", "QA Tester"]
        steps = ["review_story", "create_architecture", "implement_backend", "implement_frontend", "run_tests"]
        
        for i, (agent, step) in enumerate(zip(agents, steps)):
            conversation = Conversation(
                id=i + 1,
                workflow_id=1,
                agent=agent,
                step=step,
                status="completed",
                timestamp=datetime.utcnow() - timedelta(minutes=90 - (i * 10))
            )
            db.add(conversation)
            self.conversations.append(conversation)
        
        db.commit()
        
        # Create messages for each conversation
        self.messages = []
        for i, conversation in enumerate(self.conversations):
            # User message
            user_msg = Message(
                id=i * 2 + 1,
                conversation_id=conversation.id,
                role="user",
                content=f"Please {conversation.step} for story {self.workflow.jira_story_id}",
                message_metadata={"created_at": conversation.timestamp}
            )
            db.add(user_msg)
            self.messages.append(user_msg)
            
            # Assistant message
            assistant_msg = Message(
                id=i * 2 + 2,
                conversation_id=conversation.id,
                role="assistant",
                content=f"I have completed {conversation.step}. Here are the results...",
                message_metadata={"created_at": conversation.timestamp + timedelta(minutes=1)}
            )
            db.add(assistant_msg)
            self.messages.append(assistant_msg)
        
        db.commit()
        self.db_session = db
        
        yield
        
        # Cleanup
        db.query(Message).delete()
        db.query(Conversation).delete()
        db.query(Workflow).delete()
        db.commit()
        db.close()

    def test_build_review_prompt_with_real_data(self):
        """Test building review prompt with actual database data."""
        service = ConversationReviewService()
        
        # Get real workflow data
        workflow_data = {
            "workflow": {
                "id": self.workflow.id,
                "name": self.workflow.name,
                "status": self.workflow.status,
                "jira_story_id": self.workflow.jira_story_id,
                "jira_story_title": self.workflow.jira_story_title,
                "jira_story_description": self.workflow.jira_story_description
            },
            "conversations": []
        }
        
        # Get real conversation data
        for conversation in self.conversations:
            conv_data = {
                "id": conversation.id,
                "agent": conversation.agent,
                "step": conversation.step,
                "status": conversation.status,
                "timestamp": conversation.timestamp.isoformat(),
                "messages": []
            }
            
            # Get messages for this conversation
            for message in self.messages:
                if message.conversation_id == conversation.id:
                    msg_data = {
                        "role": message.role,
                        "content": message.content,
                        "metadata": message.message_metadata
                    }
                    conv_data["messages"].append(msg_data)
            
            workflow_data["conversations"].append(conv_data)
        
        # Mock codebase guide
        codebase_guide = {
            "entries": [
                {
                    "path": "crewai_app/agents/pm.py",
                    "summary": "Product Manager agent implementation",
                    "content": "class PMAgent: ..."
                },
                {
                    "path": "crewai_app/workflows/story_implementation_workflow.py",
                    "summary": "Main workflow implementation",
                    "content": "class StoryImplementationWorkflow: ..."
                }
            ]
        }
        
        # Build the prompt
        prompt = service.build_review_prompt(
            workflow_id=1,
            conversations=workflow_data,
            codebase_guide=codebase_guide,
            coding_rules="Follow PEP 8 style guidelines"
        )
        
        # Verify prompt contains expected elements
        assert "SYSTEM" in prompt
        assert "Integration Test Workflow" in prompt
        assert "INTEGRATION-001" in prompt
        assert "Product Manager" in prompt
        assert "Solution Architect" in prompt
        assert "Backend Developer" in prompt
        assert "Frontend Developer" in prompt
        assert "QA Tester" in prompt
        assert "crewai_app/agents/pm.py" in prompt
        assert "crewai_app/workflows/story_implementation_workflow.py" in prompt
        assert "Follow PEP 8 style guidelines" in prompt

    def test_parse_review_output_with_comprehensive_data(self):
        """Test parsing LLM output with comprehensive review data."""
        service = ConversationReviewService()
        
        # Mock comprehensive LLM response
        mock_llm_response = {
            "summary": "Comprehensive analysis of Integration Test Workflow shows multiple optimization opportunities across all agent interactions.",
            "workflow_recommendations": [
                {
                    "title": "Implement Parallel Processing",
                    "description": "Backend and Frontend development can be parallelized to reduce overall execution time."
                },
                {
                    "title": "Add Caching Layer",
                    "description": "Implement caching for frequently accessed story data to reduce redundant API calls."
                }
            ],
            "prompt_recommendations": [
                {
                    "agent": "Product Manager",
                    "current_issue": "Story analysis prompts are too generic",
                    "suggestion": "Add specific context about story complexity and acceptance criteria"
                },
                {
                    "agent": "Solution Architect",
                    "current_issue": "Architecture prompts lack technical constraints",
                    "suggestion": "Include performance and scalability requirements in architecture prompts"
                },
                {
                    "agent": "Backend Developer",
                    "current_issue": "Implementation prompts don't specify testing requirements",
                    "suggestion": "Add unit test and integration test requirements to implementation prompts"
                }
            ],
            "code_change_suggestions": [
                {
                    "path": "crewai_app/agents/pm.py",
                    "section": "review_story method",
                    "change_type": "edit",
                    "before_summary": "Generic story review without complexity analysis",
                    "after_summary": "Enhanced story review with complexity assessment and acceptance criteria extraction",
                    "patch_outline": "Add complexity analysis logic and acceptance criteria parsing"
                },
                {
                    "path": "crewai_app/workflows/story_implementation_workflow.py",
                    "section": "execute method",
                    "change_type": "add",
                    "before_summary": "Sequential execution only",
                    "after_summary": "Parallel execution for independent tasks",
                    "patch_outline": "Implement asyncio-based parallel execution for independent agent tasks"
                }
            ],
            "risk_flags": [
                "High token usage detected in Product Manager agent",
                "Potential memory leaks in long-running workflows",
                "Insufficient error handling in Backend Developer agent"
            ],
            "quick_wins": [
                "Reduce prompt length by 25% across all agents",
                "Implement response caching for repeated queries",
                "Add input validation to prevent malformed requests"
            ],
            "estimated_savings": {
                "messages": 35,
                "cost_usd": 5.75,
                "duration_minutes": 18
            }
        }
        
        # Parse the response
        parsed = service._parse_review_output(json.dumps(mock_llm_response))
        
        # Verify all sections are parsed correctly
        assert parsed["summary"] == mock_llm_response["summary"]
        assert len(parsed["workflow_recommendations"]) == 2
        assert len(parsed["prompt_recommendations"]) == 3
        assert len(parsed["code_change_suggestions"]) == 2
        assert len(parsed["risk_flags"]) == 3
        assert len(parsed["quick_wins"]) == 3
        
        # Verify specific content
        assert parsed["workflow_recommendations"][0]["title"] == "Implement Parallel Processing"
        assert parsed["prompt_recommendations"][0]["agent"] == "Product Manager"
        assert parsed["code_change_suggestions"][0]["path"] == "crewai_app/agents/pm.py"
        assert parsed["risk_flags"][0] == "High token usage detected in Product Manager agent"
        assert parsed["quick_wins"][0] == "Reduce prompt length by 25% across all agents"
        
        # Verify estimated savings
        savings = parsed["estimated_savings"]
        assert savings["messages"] == 35
        assert savings["cost_usd"] == 5.75
        assert savings["duration_minutes"] == 18

    @patch('crewai_app.services.conversation_review_service.ConversationReviewService._run_llm')
    def test_review_with_real_workflow_data(self, mock_run_llm):
        """Test complete review process with real workflow data."""
        # Mock LLM response
        mock_llm_response = {
            "summary": "Real workflow analysis completed successfully.",
            "workflow_recommendations": [
                {
                    "title": "Optimize Agent Communication",
                    "description": "Based on real conversation data, implement shared context system."
                }
            ],
            "prompt_recommendations": [
                {
                    "agent": "Product Manager",
                    "current_issue": "Real conversation analysis shows verbose prompts",
                    "suggestion": "Streamline prompts based on actual usage patterns"
                }
            ],
            "code_change_suggestions": [
                {
                    "path": "crewai_app/agents/pm.py",
                    "section": "review_story",
                    "change_type": "edit",
                    "before_summary": "Based on real data analysis",
                    "after_summary": "Optimized based on actual conversation patterns",
                    "patch_outline": "Implement data-driven prompt optimization"
                }
            ],
            "risk_flags": ["Real data shows high token usage"],
            "quick_wins": ["Real optimization opportunities identified"],
            "estimated_savings": {
                "messages": 20,
                "cost_usd": 3.25,
                "duration_minutes": 10
            }
        }
        
        mock_run_llm.return_value = json.dumps(mock_llm_response)
        
        service = ConversationReviewService()
        
        # Mock the database queries
        with patch('crewai_app.services.conversation_review_service.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = iter([mock_db])
            
            # Mock workflow query
            mock_db.query.return_value.filter.return_value.first.return_value = self.workflow
            
            # Mock conversations query
            mock_db.query.return_value.filter.return_value.all.return_value = self.conversations
            
            # Mock messages query
            mock_db.query.return_value.filter.return_value.all.return_value = self.messages
            
            # Call the review method
            result = service.review(workflow_id=1)
            
            # Verify the result
            assert result["summary"] == "Real workflow analysis completed successfully."
            assert len(result["workflow_recommendations"]) == 1
            assert len(result["prompt_recommendations"]) == 1
            assert len(result["code_change_suggestions"]) == 1
            assert len(result["risk_flags"]) == 1
            assert len(result["quick_wins"]) == 1
            assert result["estimated_savings"]["messages"] == 20
            assert result["estimated_savings"]["cost_usd"] == 3.25
            assert result["estimated_savings"]["duration_minutes"] == 10

    def test_review_with_empty_conversations(self):
        """Test review with workflow that has no conversations."""
        service = ConversationReviewService()
        
        # Mock empty conversation data
        empty_workflow_data = {
            "workflow": {
                "id": 1,
                "name": "Empty Workflow",
                "status": "pending"
            },
            "conversations": []
        }
        
        empty_codebase_guide = {"entries": []}
        
        # Build prompt with empty data
        prompt = service.build_review_prompt(
            workflow_id=1,
            conversations=empty_workflow_data,
            codebase_guide=empty_codebase_guide,
            coding_rules=""
        )
        
        # Verify prompt handles empty data gracefully
        assert "SYSTEM" in prompt
        assert "Empty Workflow" in prompt
        assert "No conversations available" in prompt or "conversations" in prompt.lower()

    def test_review_with_malformed_llm_response(self):
        """Test handling of malformed LLM response."""
        service = ConversationReviewService()
        
        # Test with invalid JSON
        with pytest.raises(Exception):
            service._parse_review_output("invalid json")
        
        # Test with missing required fields
        incomplete_response = {
            "summary": "Incomplete response"
            # Missing other required fields
        }
        
        with pytest.raises(Exception):
            service._parse_review_output(json.dumps(incomplete_response))

    def test_review_with_partial_data(self):
        """Test review with partial conversation data."""
        service = ConversationReviewService()
        
        # Mock partial workflow data (only some conversations have messages)
        partial_workflow_data = {
            "workflow": {
                "id": 1,
                "name": "Partial Workflow",
                "status": "running"
            },
            "conversations": [
                {
                    "id": 1,
                    "agent": "Product Manager",
                    "step": "review_story",
                    "status": "completed",
                    "timestamp": datetime.utcnow().isoformat(),
                    "messages": [
                        {
                            "role": "user",
                            "content": "Review this story",
                            "metadata": {}
                        }
                    ]
                },
                {
                    "id": 2,
                    "agent": "Solution Architect",
                    "step": "create_architecture",
                    "status": "running",
                    "timestamp": datetime.utcnow().isoformat(),
                    "messages": []  # No messages yet
                }
            ]
        }
        
        codebase_guide = {"entries": []}
        
        # Build prompt with partial data
        prompt = service.build_review_prompt(
            workflow_id=1,
            conversations=partial_workflow_data,
            codebase_guide=codebase_guide,
            coding_rules=""
        )
        
        # Verify prompt handles partial data
        assert "SYSTEM" in prompt
        assert "Partial Workflow" in prompt
        assert "Product Manager" in prompt
        assert "Solution Architect" in prompt
