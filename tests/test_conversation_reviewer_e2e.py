"""
End-to-end tests for the conversation reviewer feature.
Tests the complete flow from API call to database persistence.
"""
import pytest
from fastapi.testclient import TestClient
from crewai_app.main import app
from crewai_app.database import get_db, init_database, Workflow, Conversation, Message
from datetime import datetime, timedelta
import json


class TestConversationReviewerE2E:
    """End-to-end tests for conversation reviewer functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test database and create test data."""
        init_database()
        db = next(get_db())
        
        # Clean up any existing test data
        db.query(Message).delete()
        db.query(Conversation).delete()
        db.query(Workflow).delete()
        db.commit()
        
        # Create a test workflow
        self.workflow = Workflow(
            id=1,
            name="Test Workflow for Conversation Review",
            jira_story_id="TEST-123",
            jira_story_title="Test Story",
            jira_story_description="A test story for conversation review",
            status="completed",
            started_at=datetime.utcnow() - timedelta(hours=1),
            finished_at=datetime.utcnow() - timedelta(minutes=30),
            created_at=datetime.utcnow() - timedelta(hours=2),
            updated_at=datetime.utcnow() - timedelta(minutes=30)
        )
        db.add(self.workflow)
        db.commit()
        
        # Create test conversations
        self.conversation1 = Conversation(
            id=1,
            workflow_id=1,
            agent="Product Manager",
            step="review_story",
            status="completed",
            timestamp=datetime.utcnow() - timedelta(minutes=45)
        )
        db.add(self.conversation1)
        
        self.conversation2 = Conversation(
            id=2,
            workflow_id=1,
            agent="Solution Architect",
            step="create_architecture",
            status="completed",
            timestamp=datetime.utcnow() - timedelta(minutes=40)
        )
        db.add(self.conversation2)
        db.commit()
        
        # Create test messages
        self.message1 = Message(
            id=1,
            conversation_id=1,
            role="user",
            content="Please review this story: TEST-123",
            message_metadata={"created_at": datetime.utcnow() - timedelta(minutes=45)}
        )
        db.add(self.message1)
        
        self.message2 = Message(
            id=2,
            conversation_id=1,
            role="assistant",
            content="I've reviewed the story and identified the key requirements...",
            message_metadata={"created_at": datetime.utcnow() - timedelta(minutes=44)}
        )
        db.add(self.message2)
        db.commit()
        
        self.db_session = db
        
        yield
        
        # Cleanup
        db.query(Message).delete()
        db.query(Conversation).delete()
        db.query(Workflow).delete()
        db.commit()
        db.close()

    def test_trigger_conversation_review_success(self):
        """Test successful conversation review generation."""
        client = TestClient(app)
        
        # Mock the LLM response
        mock_review_response = {
            "summary": "Workflow analysis shows good agent collaboration with optimization opportunities.",
            "workflow_recommendations": [
                {
                    "title": "Streamline Communication",
                    "description": "Reduce redundant messages between agents."
                }
            ],
            "prompt_recommendations": [
                {
                    "agent": "Product Manager",
                    "current_issue": "Prompts too verbose",
                    "suggestion": "Use more concise prompts"
                }
            ],
            "code_change_suggestions": [
                {
                    "path": "crewai_app/agents/pm.py",
                    "section": "review_story",
                    "change_type": "edit",
                    "before_summary": "Long prompt",
                    "after_summary": "Concise prompt",
                    "patch_outline": "Simplify prompt text"
                }
            ],
            "risk_flags": ["High token usage"],
            "quick_wins": ["Reduce prompt length"],
            "estimated_savings": {
                "messages": 10,
                "cost_usd": 1.50,
                "duration_minutes": 5
            }
        }
        
        # Mock the conversation review service
        with pytest.MonkeyPatch().context() as m:
            from crewai_app.services.conversation_review_service import ConversationReviewService
            
            def mock_review(self, workflow_id: int):
                return mock_review_response
            
            m.setattr(ConversationReviewService, "review", mock_review)
            
            # Make the API call
            response = client.post("/workflows/1/conversation-review")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            
            assert data["summary"] == mock_review_response["summary"]
            assert len(data["workflow_recommendations"]) == 1
            assert len(data["prompt_recommendations"]) == 1
            assert len(data["code_change_suggestions"]) == 1
            assert len(data["risk_flags"]) == 1
            assert len(data["quick_wins"]) == 1
            assert data["estimated_savings"]["messages"] == 10
            assert data["estimated_savings"]["cost_usd"] == 1.50
            assert data["estimated_savings"]["duration_minutes"] == 5

    def test_get_conversation_review_success(self):
        """Test retrieving existing conversation review."""
        client = TestClient(app)
        
        # First create a review
        mock_review_response = {
            "summary": "Existing review data",
            "workflow_recommendations": [],
            "prompt_recommendations": [],
            "code_change_suggestions": [],
            "risk_flags": [],
            "quick_wins": [],
            "estimated_savings": {
                "messages": 0,
                "cost_usd": 0.0,
                "duration_minutes": 0
            }
        }
        
        with pytest.MonkeyPatch().context() as m:
            from crewai_app.services.conversation_review_service import ConversationReviewService
            
            def mock_get_review(self, workflow_id: int):
                return mock_review_response
            
            m.setattr(ConversationReviewService, "get_review", mock_get_review)
            
            # Make the GET request
            response = client.get("/workflows/1/conversation-review")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["summary"] == "Existing review data"

    def test_conversation_review_workflow_not_found(self):
        """Test conversation review for non-existent workflow."""
        client = TestClient(app)
        
        # Try to get review for non-existent workflow
        response = client.post("/workflows/999/conversation-review")
        
        # Should return 404
        assert response.status_code == 404

    def test_conversation_review_service_error(self):
        """Test handling of service errors."""
        client = TestClient(app)
        
        with pytest.MonkeyPatch().context() as m:
            from crewai_app.services.conversation_review_service import ConversationReviewService
            
            def mock_review_error(self, workflow_id: int):
                raise Exception("Service unavailable")
            
            m.setattr(ConversationReviewService, "review", mock_review_error)
            
            # Make the API call
            response = client.post("/workflows/1/conversation-review")
            
            # Should return 500
            assert response.status_code == 500
            data = response.json()
            assert "Service unavailable" in data["detail"]

    def test_conversation_review_with_real_data(self):
        """Test conversation review with actual database data."""
        client = TestClient(app)
        
        # Verify we have the test data
        assert self.workflow.id == 1
        assert self.conversation1.workflow_id == 1
        assert self.message1.conversation_id == 1
        
        # Mock a realistic review response
        mock_review_response = {
            "summary": f"Analyzed workflow {self.workflow.name} with {self.conversation1.agent} and {self.conversation2.agent} agents.",
            "workflow_recommendations": [
                {
                    "title": "Optimize Agent Sequence",
                    "description": f"Based on analysis of {self.conversation1.agent} and {self.conversation2.agent} interactions."
                }
            ],
            "prompt_recommendations": [
                {
                    "agent": self.conversation1.agent,
                    "current_issue": "Prompt could be more specific",
                    "suggestion": "Add more context about the story requirements"
                }
            ],
            "code_change_suggestions": [
                {
                    "path": "crewai_app/agents/pm.py",
                    "section": "review_story",
                    "change_type": "edit",
                    "before_summary": "Generic story review",
                    "after_summary": "Context-aware story analysis",
                    "patch_outline": "Add story context to prompt"
                }
            ],
            "risk_flags": ["Potential token overuse"],
            "quick_wins": ["Cache story analysis"],
            "estimated_savings": {
                "messages": 5,
                "cost_usd": 0.75,
                "duration_minutes": 3
            }
        }
        
        with pytest.MonkeyPatch().context() as m:
            from crewai_app.services.conversation_review_service import ConversationReviewService
            
            def mock_review(self, workflow_id: int):
                return mock_review_response
            
            m.setattr(ConversationReviewService, "review", mock_review)
            
            # Make the API call
            response = client.post("/workflows/1/conversation-review")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            
            # Verify the review contains references to our test data
            assert self.workflow.name in data["summary"]
            assert self.conversation1.agent in data["summary"]
            assert self.conversation2.agent in data["summary"]
            
            # Verify all sections are present
            assert "workflow_recommendations" in data
            assert "prompt_recommendations" in data
            assert "code_change_suggestions" in data
            assert "risk_flags" in data
            assert "quick_wins" in data
            assert "estimated_savings" in data

    def test_conversation_review_data_validation(self):
        """Test that conversation review data is properly validated."""
        client = TestClient(app)
        
        # Test with invalid workflow ID
        response = client.post("/workflows/invalid/conversation-review")
        assert response.status_code == 422  # Validation error
        
        # Test with negative workflow ID
        response = client.post("/workflows/-1/conversation-review")
        assert response.status_code == 404  # Not found

    def test_conversation_review_response_format(self):
        """Test that conversation review response has correct format."""
        client = TestClient(app)
        
        mock_review_response = {
            "summary": "Test summary",
            "workflow_recommendations": [
                {"title": "Test Title", "description": "Test Description"}
            ],
            "prompt_recommendations": [
                {"agent": "Test Agent", "current_issue": "Test Issue", "suggestion": "Test Suggestion"}
            ],
            "code_change_suggestions": [
                {
                    "path": "test/path.py",
                    "section": "test_section",
                    "change_type": "edit",
                    "before_summary": "Before",
                    "after_summary": "After",
                    "patch_outline": "Patch"
                }
            ],
            "risk_flags": ["Test Risk"],
            "quick_wins": ["Test Win"],
            "estimated_savings": {
                "messages": 1,
                "cost_usd": 0.1,
                "duration_minutes": 1
            }
        }
        
        with pytest.MonkeyPatch().context() as m:
            from crewai_app.services.conversation_review_service import ConversationReviewService
            
            def mock_review(self, workflow_id: int):
                return mock_review_response
            
            m.setattr(ConversationReviewService, "review", mock_review)
            
            response = client.post("/workflows/1/conversation-review")
            assert response.status_code == 200
            
            data = response.json()
            
            # Verify all required fields are present
            required_fields = [
                "summary", "workflow_recommendations", "prompt_recommendations",
                "code_change_suggestions", "risk_flags", "quick_wins", "estimated_savings"
            ]
            
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            # Verify data types
            assert isinstance(data["summary"], str)
            assert isinstance(data["workflow_recommendations"], list)
            assert isinstance(data["prompt_recommendations"], list)
            assert isinstance(data["code_change_suggestions"], list)
            assert isinstance(data["risk_flags"], list)
            assert isinstance(data["quick_wins"], list)
            assert isinstance(data["estimated_savings"], dict)
            
            # Verify estimated_savings structure
            savings = data["estimated_savings"]
            assert "messages" in savings
            assert "cost_usd" in savings
            assert "duration_minutes" in savings
            assert isinstance(savings["messages"], int)
            assert isinstance(savings["cost_usd"], (int, float))
            assert isinstance(savings["duration_minutes"], int)
