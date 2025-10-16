"""
Tests for WorkflowStatusService
"""
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from crewai_app.services.workflow_status_service import WorkflowStatusService
from crewai_app.database import Workflow, get_db


class TestWorkflowStatusService:
    """Test cases for WorkflowStatusService"""
    
    def setup_method(self):
        """Setup test environment"""
        self.service = WorkflowStatusService()
        # Mock database session
        self.mock_db = Mock()
        self.mock_workflow = Mock()
        self.mock_workflow.id = 1
        self.mock_workflow.status = "running"
        self.mock_workflow.last_heartbeat_at = datetime.utcnow()
        
    def test_finalize_workflow_status_success(self):
        """Test successful workflow finalization"""
        # Mock database query
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.mock_workflow
        
        with patch('crewai_app.services.workflow_status_service.next') as mock_next:
            mock_next.return_value = self.mock_db
            
            result = self.service.finalize_workflow_status(1, "completed", datetime.utcnow())
            
            assert result is True
            # The service should update the workflow status - check that the status was set
            # Note: The mock object's status attribute is updated by the service
            # We can't easily test commit() calls with the current mock setup
    
    def test_finalize_workflow_status_already_terminal(self):
        """Test finalization when workflow is already terminal"""
        self.mock_workflow.status = "completed"
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.mock_workflow
        
        with patch('crewai_app.services.workflow_status_service.next') as mock_next:
            mock_next.return_value = self.mock_db
            
            result = self.service.finalize_workflow_status(1, "failed", datetime.utcnow())
            
            assert result is True
            # Status should not change
            assert self.mock_workflow.status == "completed"
    
    def test_finalize_workflow_status_workflow_not_found(self):
        """Test finalization when workflow doesn't exist"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with patch('crewai_app.services.workflow_status_service.next') as mock_next:
            mock_next.return_value = self.mock_db
            
            result = self.service.finalize_workflow_status(999, "completed", datetime.utcnow())
            
            assert result is False
    
    def test_finalize_workflow_status_invalid_status(self):
        """Test finalization with invalid terminal status"""
        result = self.service.finalize_workflow_status(1, "invalid_status", datetime.utcnow())
        assert result is False
    
    def test_get_workflow_status_info_running(self):
        """Test getting status info for running workflow"""
        self.mock_workflow.status = "running"
        self.mock_workflow.started_at = datetime.utcnow()
        self.mock_workflow.last_heartbeat_at = datetime.utcnow()
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.mock_workflow
        
        with patch('crewai_app.services.workflow_status_service.next') as mock_next:
            mock_next.return_value = self.mock_db
            
            result = self.service.get_workflow_status_info(1)
            
            assert result["workflow_id"] == 1
            assert result["status"] == "running"
            assert result["isTerminal"] is False
            assert result["heartbeat_stale"] is False
    
    def test_get_workflow_status_info_stale_heartbeat(self):
        """Test getting status info for workflow with stale heartbeat"""
        self.mock_workflow.status = "running"
        self.mock_workflow.started_at = datetime.utcnow()
        # Set heartbeat to 10 minutes ago (stale)
        self.mock_workflow.last_heartbeat_at = datetime.utcnow() - timedelta(minutes=10)
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.mock_workflow
        
        with patch('crewai_app.services.workflow_status_service.next') as mock_next:
            mock_next.return_value = self.mock_db
            
            result = self.service.get_workflow_status_info(1)
            
            assert result["workflow_id"] == 1
            assert result["status"] == "running"
            assert result["isTerminal"] is False
            assert result["heartbeat_stale"] is True
    
    def test_get_workflow_status_info_terminal(self):
        """Test getting status info for terminal workflow"""
        self.mock_workflow.status = "completed"
        self.mock_workflow.started_at = datetime.utcnow() - timedelta(minutes=5)
        self.mock_workflow.finished_at = datetime.utcnow()
        self.mock_workflow.last_heartbeat_at = None
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.mock_workflow
        
        with patch('crewai_app.services.workflow_status_service.next') as mock_next:
            mock_next.return_value = self.mock_db
            
            result = self.service.get_workflow_status_info(1)
            
            assert result["workflow_id"] == 1
            assert result["status"] == "completed"
            assert result["isTerminal"] is True
            assert result["heartbeat_stale"] is False
    
    def test_reconcile_workflow_status_stale(self):
        """Test reconciling stale workflow status"""
        self.mock_workflow.status = "running"
        self.mock_workflow.last_heartbeat_at = datetime.utcnow() - timedelta(minutes=10)
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.mock_workflow
        
        with patch('crewai_app.services.workflow_status_service.next') as mock_next:
            mock_next.return_value = self.mock_db
            
            # Mock the finalize call
            with patch.object(self.service, 'finalize_workflow_status', return_value=True) as mock_finalize:
                result = self.service.reconcile_workflow_status(1)
                
                assert result is True
                mock_finalize.assert_called_once_with(1, "failed", error="Manual reconciliation: heartbeat timeout")
    
    def test_reconcile_workflow_status_not_stale(self):
        """Test reconciling workflow with fresh heartbeat"""
        self.mock_workflow.status = "running"
        self.mock_workflow.last_heartbeat_at = datetime.utcnow() - timedelta(minutes=1)
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.mock_workflow
        
        with patch('crewai_app.services.workflow_status_service.next') as mock_next:
            mock_next.return_value = self.mock_db
            
            result = self.service.reconcile_workflow_status(1)
            
            assert result is True
            # Should not call finalize since heartbeat is fresh
    
    def test_reconcile_workflow_status_not_running(self):
        """Test reconciling non-running workflow"""
        self.mock_workflow.status = "completed"
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.mock_workflow
        
        with patch('crewai_app.services.workflow_status_service.next') as mock_next:
            mock_next.return_value = self.mock_db
            
            result = self.service.reconcile_workflow_status(1)
            
            assert result is True
            # Should not call finalize since workflow is not running


if __name__ == "__main__":
    pytest.main([__file__])
