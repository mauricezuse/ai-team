"""
Workflow Status Management Service
Handles workflow status finalization, heartbeat tracking, and zombie detection
"""
import threading
import time
from typing import Dict, Any, Optional, Set
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from crewai_app.database import get_db, Workflow
from crewai_app.config import settings
from crewai_app.utils.logger import logger

class WorkflowStatusService:
    """Manages workflow status with heartbeat and finalization"""
    
    def __init__(self):
        self.heartbeat_interval = settings.heartbeat_interval_seconds
        self.heartbeat_timeout = settings.heartbeat_timeout_seconds
        self._heartbeat_threads: Dict[int, threading.Thread] = {}
        self._stop_heartbeat = threading.Event()
        self._lock = threading.Lock()
        
        # Start background audit task
        self._start_audit_task()
    
    def finalize_workflow_status(
        self, 
        workflow_id: int, 
        terminal_status: str, 
        finished_at: Optional[datetime] = None,
        error: Optional[str] = None
    ) -> bool:
        """
        Idempotent finalization of workflow status.
        Once a workflow is terminal, it cannot regress to non-terminal.
        """
        if terminal_status not in ["completed", "failed", "cancelled"]:
            logger.error(f"[WorkflowStatusService] Invalid terminal status: {terminal_status}")
            return False
        
        try:
            db = next(get_db())
            workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
            
            if not workflow:
                logger.error(f"[WorkflowStatusService] Workflow {workflow_id} not found")
                return False
            
            # Check if already terminal - enforce invariant
            if workflow.status in ["completed", "failed", "cancelled"]:
                logger.info(f"[WorkflowStatusService] Workflow {workflow_id} already in terminal state: {workflow.status}")
                return True
            
            # Update to terminal status
            workflow.status = terminal_status
            workflow.finished_at = finished_at or datetime.utcnow()
            if error:
                workflow.error = error
            workflow.updated_at = datetime.utcnow()
            
            db.commit()
            
            # Stop heartbeat for this workflow
            self._stop_workflow_heartbeat(workflow_id)
            
            logger.info(f"[WorkflowStatusService] Finalized workflow {workflow_id} with status: {terminal_status}")
            return True
            
        except Exception as e:
            logger.error(f"[WorkflowStatusService] Failed to finalize workflow {workflow_id}: {e}")
            return False
        finally:
            try:
                db.close()
            except:
                pass
    
    def start_workflow_heartbeat(self, workflow_id: int) -> bool:
        """Start heartbeat tracking for a workflow"""
        try:
            with self._lock:
                if workflow_id in self._heartbeat_threads:
                    logger.warning(f"[WorkflowStatusService] Heartbeat already running for workflow {workflow_id}")
                    return True
                
                # Start heartbeat thread
                thread = threading.Thread(
                    target=self._heartbeat_worker,
                    args=(workflow_id,),
                    daemon=True
                )
                thread.start()
                self._heartbeat_threads[workflow_id] = thread
                
                logger.info(f"[WorkflowStatusService] Started heartbeat for workflow {workflow_id}")
                return True
                
        except Exception as e:
            logger.error(f"[WorkflowStatusService] Failed to start heartbeat for workflow {workflow_id}: {e}")
            return False
    
    def _stop_workflow_heartbeat(self, workflow_id: int):
        """Stop heartbeat tracking for a workflow"""
        with self._lock:
            if workflow_id in self._heartbeat_threads:
                del self._heartbeat_threads[workflow_id]
                logger.info(f"[WorkflowStatusService] Stopped heartbeat for workflow {workflow_id}")

    def touch_heartbeat(self, workflow_id: int) -> None:
        """Update last_heartbeat_at to now for the given workflow."""
        try:
            db = next(get_db())
            workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
            if workflow and workflow.status == "running":
                workflow.last_heartbeat_at = datetime.utcnow()
                db.commit()
        except Exception as e:
            logger.debug(f"[WorkflowStatusService] touch_heartbeat error for {workflow_id}: {e}")
        finally:
            try:
                db.close()
            except Exception:
                pass
    
    def _heartbeat_worker(self, workflow_id: int):
        """Background worker that updates heartbeat timestamp"""
        while not self._stop_heartbeat.is_set():
            try:
                # Update heartbeat timestamp
                db = next(get_db())
                workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
                
                if workflow and workflow.status == "running":
                    workflow.last_heartbeat_at = datetime.utcnow()
                    db.commit()
                    logger.debug(f"[WorkflowStatusService] Updated heartbeat for workflow {workflow_id}")
                else:
                    # Workflow no longer running, stop heartbeat
                    self._stop_workflow_heartbeat(workflow_id)
                    break
                    
            except Exception as e:
                logger.error(f"[WorkflowStatusService] Heartbeat error for workflow {workflow_id}: {e}")
            
            # Wait for next heartbeat
            time.sleep(self.heartbeat_interval)
        
        try:
            db.close()
        except:
            pass
    
    def _start_audit_task(self):
        """Start background task to audit stale workflows"""
        def audit_worker():
            while not self._stop_heartbeat.is_set():
                try:
                    self._audit_stale_workflows()
                except Exception as e:
                    logger.error(f"[WorkflowStatusService] Audit task error: {e}")
                
                # Run audit every minute
                time.sleep(60)
        
        audit_thread = threading.Thread(target=audit_worker, daemon=True)
        audit_thread.start()
        logger.info("[WorkflowStatusService] Started audit task for stale workflows")
    
    def _audit_stale_workflows(self):
        """Audit and mark stale running workflows as failed"""
        try:
            db = next(get_db())
            cutoff_time = datetime.utcnow() - timedelta(seconds=self.heartbeat_timeout)
            
            # Find running workflows with stale heartbeat
            stale_workflows = db.query(Workflow).filter(
                Workflow.status == "running",
                Workflow.last_heartbeat_at < cutoff_time
            ).all()
            
            for workflow in stale_workflows:
                seconds = (datetime.utcnow() - (workflow.last_heartbeat_at or workflow.started_at or datetime.utcnow())).total_seconds()
                logger.warning(f"[WorkflowStatusService] Marking stale workflow {workflow.id} as failed after {int(seconds)}s since last heartbeat")
                self.finalize_workflow_status(
                    workflow.id,
                    "failed",
                    error=f"Heartbeat timeout after {self.heartbeat_timeout} seconds"
                )
                
        except Exception as e:
            logger.error(f"[WorkflowStatusService] Audit failed: {e}")
        finally:
            try:
                db.close()
            except:
                pass
    
    def get_workflow_status_info(self, workflow_id: int) -> Dict[str, Any]:
        """Get comprehensive workflow status information"""
        try:
            db = next(get_db())
            workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
            
            if not workflow:
                return {
                    "workflow_id": workflow_id,
                    "status": "not_found",
                    "isTerminal": True,
                    "message": "Workflow not found"
                }
            
            is_terminal = workflow.status in ["completed", "failed", "cancelled"]
            
            # Check if heartbeat is stale
            heartbeat_stale = False
            if workflow.status == "running" and workflow.last_heartbeat_at:
                time_since_heartbeat = datetime.utcnow() - workflow.last_heartbeat_at
                heartbeat_stale = time_since_heartbeat.total_seconds() > self.heartbeat_timeout
            
            return {
                "workflow_id": workflow_id,
                "status": workflow.status,
                "isTerminal": is_terminal,
                "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
                "finished_at": workflow.finished_at.isoformat() if workflow.finished_at else None,
                "error": workflow.error,
                "last_heartbeat_at": workflow.last_heartbeat_at.isoformat() if workflow.last_heartbeat_at else None,
                "heartbeat_stale": heartbeat_stale,
                "message": f"Workflow is {workflow.status}"
            }
            
        except Exception as e:
            logger.error(f"[WorkflowStatusService] Failed to get status info for workflow {workflow_id}: {e}")
            return {
                "workflow_id": workflow_id,
                "status": "error",
                "isTerminal": True,
                "message": f"Failed to get status: {e}"
            }
        finally:
            try:
                db.close()
            except:
                pass
    
    def reconcile_workflow_status(self, workflow_id: int) -> bool:
        """Manually reconcile workflow status based on heartbeat"""
        try:
            db = next(get_db())
            workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
            
            if not workflow:
                return False
            
            if workflow.status == "running":
                # Check if heartbeat is stale
                if workflow.last_heartbeat_at:
                    time_since_heartbeat = datetime.utcnow() - workflow.last_heartbeat_at
                    if time_since_heartbeat.total_seconds() > self.heartbeat_timeout:
                        logger.info(f"[WorkflowStatusService] Reconciling stale workflow {workflow_id}")
                        return self.finalize_workflow_status(
                            workflow_id,
                            "failed",
                            error="Manual reconciliation: heartbeat timeout"
                        )
            
            return True
            
        except Exception as e:
            logger.error(f"[WorkflowStatusService] Failed to reconcile workflow {workflow_id}: {e}")
            return False
        finally:
            try:
                db.close()
            except:
                pass
    
    def shutdown(self):
        """Shutdown the service and stop all background tasks"""
        self._stop_heartbeat.set()
        logger.info("[WorkflowStatusService] Shutdown initiated")

# Global service instance
workflow_status_service = WorkflowStatusService()
