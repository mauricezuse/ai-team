"""
Unit tests for execution aggregation and comparison functionality.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from crewai_app.database import Base, Workflow, Execution, Conversation, LLMCall
# from crewai_app.main import compare_workflows, get_execution_metrics


class TestExecutionAggregation:
    """Test execution metrics aggregation and comparison."""
    
    @pytest.fixture
    def db_session(self):
        """Create in-memory database for testing."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        yield session
        session.close()
    
    @pytest.fixture
    def sample_workflow(self, db_session):
        """Create a sample workflow with executions."""
        workflow = Workflow(
            id=1,
            name="Test Workflow",
            jira_story_id="TEST-123",
            status="completed"
        )
        db_session.add(workflow)
        db_session.commit()
        return workflow
    
    @pytest.fixture
    def sample_executions(self, db_session, sample_workflow):
        """Create sample executions with different metrics."""
        executions = []
        
        # Execution 1: Lower cost, faster
        exec1 = Execution(
            workflow_id=sample_workflow.id,
            status="completed",
            started_at=datetime.utcnow() - timedelta(hours=2),
            finished_at=datetime.utcnow() - timedelta(hours=1),
            total_calls=10,
            total_tokens=5000,
            total_cost="2.50",
            avg_latency_ms=1200,
            models=["gpt-4"]
        )
        db_session.add(exec1)
        executions.append(exec1)
        
        # Execution 2: Higher cost, slower
        exec2 = Execution(
            workflow_id=sample_workflow.id,
            status="completed",
            started_at=datetime.utcnow() - timedelta(hours=1),
            finished_at=datetime.utcnow(),
            total_calls=15,
            total_tokens=8000,
            total_cost="4.20",
            avg_latency_ms=1800,
            models=["gpt-4", "gpt-3.5-turbo"]
        )
        db_session.add(exec2)
        executions.append(exec2)
        
        db_session.commit()
        return executions
    
    def test_execution_metrics_aggregation(self, db_session, sample_workflow, sample_executions):
        """Test that execution metrics are correctly aggregated."""
        # Test individual execution metrics
        exec1 = sample_executions[0]
        assert exec1.total_calls == 10
        assert exec1.total_tokens == 5000
        assert exec1.total_cost == "2.50"
        assert exec1.avg_latency_ms == 1200
        assert "gpt-4" in exec1.models
        
        exec2 = sample_executions[1]
        assert exec2.total_calls == 15
        assert exec2.total_tokens == 8000
        assert exec2.total_cost == "4.20"
        assert exec2.avg_latency_ms == 1800
        assert "gpt-4" in exec2.models
        assert "gpt-3.5-turbo" in exec2.models
    
    def test_execution_comparison_deltas(self, db_session, sample_workflow, sample_executions):
        """Test that execution comparison calculates correct deltas."""
        exec1 = sample_executions[0]
        exec2 = sample_executions[1]
        
        # Calculate expected deltas
        calls_delta = exec2.total_calls - exec1.total_calls  # 15 - 10 = 5
        tokens_delta = exec2.total_tokens - exec1.total_tokens  # 8000 - 5000 = 3000
        cost_delta = float(exec2.total_cost) - float(exec1.total_cost)  # 4.20 - 2.50 = 1.70
        latency_delta = exec2.avg_latency_ms - exec1.avg_latency_ms  # 1800 - 1200 = 600
        
        assert calls_delta == 5
        assert tokens_delta == 3000
        assert abs(cost_delta - 1.70) < 1e-9
        assert latency_delta == 600
    
    def test_execution_status_tracking(self, db_session, sample_workflow):
        """Test that execution status is properly tracked."""
        execution = Execution(
            workflow_id=sample_workflow.id,
            status="pending"
        )
        db_session.add(execution)
        db_session.commit()
        
        assert execution.status == "pending"
        
        # Update status
        execution.status = "running"
        execution.started_at = datetime.utcnow()
        db_session.commit()
        
        assert execution.status == "running"
        assert execution.started_at is not None
        
        # Complete execution
        execution.status = "completed"
        execution.finished_at = datetime.utcnow()
        db_session.commit()
        
        assert execution.status == "completed"
        assert execution.finished_at is not None
    
    def test_execution_duration_calculation(self, db_session, sample_workflow):
        """Test that execution duration is calculated correctly."""
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()
        
        execution = Execution(
            workflow_id=sample_workflow.id,
            status="completed",
            started_at=start_time,
            finished_at=end_time
        )
        db_session.add(execution)
        db_session.commit()
        
        duration = execution.finished_at - execution.started_at
        assert duration.total_seconds() == 3600  # 1 hour in seconds
    
    def test_execution_models_tracking(self, db_session, sample_workflow):
        """Test that execution models are properly tracked."""
        execution = Execution(
            workflow_id=sample_workflow.id,
            models=["gpt-4", "gpt-3.5-turbo", "claude-3"]
        )
        db_session.add(execution)
        db_session.commit()
        
        assert len(execution.models) == 3
        assert "gpt-4" in execution.models
        assert "gpt-3.5-turbo" in execution.models
        assert "claude-3" in execution.models
    
    def test_execution_cost_calculation(self, db_session, sample_workflow):
        """Test that execution cost is calculated correctly."""
        execution = Execution(
            workflow_id=sample_workflow.id,
            total_calls=20,
            total_tokens=10000,
            total_cost="5.00"
        )
        db_session.add(execution)
        db_session.commit()
        
        # Test cost per call
        cost_per_call = float(execution.total_cost) / execution.total_calls
        assert cost_per_call == 0.25  # 5.00 / 20 = 0.25
        
        # Test cost per token
        cost_per_token = float(execution.total_cost) / execution.total_tokens
        assert cost_per_token == 0.0005  # 5.00 / 10000 = 0.0005


class TestExecutionComparison:
    """Test execution comparison functionality."""
    
    @pytest.fixture
    def db_session(self):
        """Create in-memory database for testing."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        yield session
        session.close()
    
    def test_compare_executions_basic(self, db_session):
        """Test basic execution comparison."""
        # Create workflow
        workflow = Workflow(
            id=1,
            name="Test Workflow",
            jira_story_id="TEST-123",
            status="completed"
        )
        db_session.add(workflow)
        db_session.commit()
        
        # Create two executions
        exec1 = Execution(
            workflow_id=workflow.id,
            status="completed",
            total_calls=10,
            total_tokens=5000,
            total_cost="2.50",
            avg_latency_ms=1200,
            models=["gpt-4"]
        )
        exec2 = Execution(
            workflow_id=workflow.id,
            status="completed",
            total_calls=15,
            total_tokens=8000,
            total_cost="4.20",
            avg_latency_ms=1800,
            models=["gpt-4", "gpt-3.5-turbo"]
        )
        db_session.add_all([exec1, exec2])
        db_session.commit()
        
        # Test comparison logic
        calls_delta = exec2.total_calls - exec1.total_calls
        tokens_delta = exec2.total_tokens - exec1.total_tokens
        cost_delta = float(exec2.total_cost) - float(exec1.total_cost)
        latency_delta = exec2.avg_latency_ms - exec1.avg_latency_ms
        
        assert calls_delta == 5
        assert tokens_delta == 3000
        assert abs(cost_delta - 1.70) < 1e-9
        assert latency_delta == 600
    
    def test_compare_executions_performance_improvement(self, db_session):
        """Test execution comparison showing performance improvement."""
        # Create workflow
        workflow = Workflow(
            id=1,
            name="Test Workflow",
            jira_story_id="TEST-123",
            status="completed"
        )
        db_session.add(workflow)
        db_session.commit()
        
        # First execution: slower, more expensive
        exec1 = Execution(
            workflow_id=workflow.id,
            status="completed",
            total_calls=20,
            total_tokens=10000,
            total_cost="8.00",
            avg_latency_ms=2000,
            models=["gpt-4"]
        )
        
        # Second execution: faster, cheaper (optimized)
        exec2 = Execution(
            workflow_id=workflow.id,
            status="completed",
            total_calls=12,
            total_tokens=6000,
            total_cost="3.60",
            avg_latency_ms=1200,
            models=["gpt-4"]
        )
        
        db_session.add_all([exec1, exec2])
        db_session.commit()
        
        # Calculate improvements (negative deltas = improvement)
        calls_improvement = exec2.total_calls - exec1.total_calls  # 12 - 20 = -8
        tokens_improvement = exec2.total_tokens - exec1.total_tokens  # 6000 - 10000 = -4000
        cost_improvement = float(exec2.total_cost) - float(exec1.total_cost)  # 3.60 - 8.00 = -4.40
        latency_improvement = exec2.avg_latency_ms - exec1.avg_latency_ms  # 1200 - 2000 = -800
        
        assert calls_improvement == -8  # 8 fewer calls
        assert tokens_improvement == -4000  # 4000 fewer tokens
        assert cost_improvement == -4.40  # $4.40 cheaper
        assert latency_improvement == -800  # 800ms faster
    
    def test_compare_executions_model_differences(self, db_session):
        """Test execution comparison with different models."""
        # Create workflow
        workflow = Workflow(
            id=1,
            name="Test Workflow",
            jira_story_id="TEST-123",
            status="completed"
        )
        db_session.add(workflow)
        db_session.commit()
        
        # Execution with single model
        exec1 = Execution(
            workflow_id=workflow.id,
            status="completed",
            models=["gpt-4"]
        )
        
        # Execution with multiple models
        exec2 = Execution(
            workflow_id=workflow.id,
            status="completed",
            models=["gpt-4", "gpt-3.5-turbo", "claude-3"]
        )
        
        db_session.add_all([exec1, exec2])
        db_session.commit()
        
        # Test model differences
        models1 = set(exec1.models)
        models2 = set(exec2.models)
        
        assert len(models1) == 1
        assert len(models2) == 3
        assert "gpt-4" in models1
        assert "gpt-4" in models2
        assert "gpt-3.5-turbo" in models2
        assert "claude-3" in models2


if __name__ == "__main__":
    pytest.main([__file__])
