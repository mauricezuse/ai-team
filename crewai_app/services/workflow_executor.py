"""
Background Workflow Executor Service
Handles non-blocking workflow execution with proper status tracking
"""
import threading
import time
from typing import Dict, Any, Optional
from datetime import datetime
from crewai_app.database import get_db, Workflow, Conversation
from crewai_app.workflows.enhanced_story_workflow import EnhancedStoryWorkflow
from crewai_app.services.jira_service import JiraService
from crewai_app.utils.logger import logger

class WorkflowExecutor:
    """Manages background workflow execution"""
    
    def __init__(self):
        self.running_workflows: Dict[int, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def execute_workflow_async(self, workflow_id: int) -> Dict[str, Any]:
        """Start workflow execution in background and return immediately"""
        
        # Check if workflow is already running
        with self._lock:
            if workflow_id in self.running_workflows:
                return {
                    "message": "Workflow is already running",
                    "workflow_id": workflow_id,
                    "status": "running"
                }
        
        # Start background thread
        thread = threading.Thread(
            target=self._execute_workflow_background,
            args=(workflow_id,),
            daemon=True
        )
        thread.start()
        
        # Mark as running
        with self._lock:
            self.running_workflows[workflow_id] = {
                "thread": thread,
                "start_time": datetime.utcnow(),
                "status": "running"
            }
        
        logger.info(f"[WorkflowExecutor] Started background execution for workflow {workflow_id}")
        
        return {
            "message": "Workflow execution started in background",
            "workflow_id": workflow_id,
            "status": "running"
        }
    
    def _execute_workflow_background(self, workflow_id: int):
        """Execute workflow in background thread"""
        try:
            logger.info(f"[WorkflowExecutor] Starting background execution for workflow {workflow_id}")
            
            # Get database session
            db = next(get_db())
            workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
            
            if not workflow:
                logger.error(f"[WorkflowExecutor] Workflow {workflow_id} not found")
                return
            
            # Update workflow status
            workflow.status = "running"
            db.commit()
            
            # Check if we should use real Jira or mock data
            use_real_jira = True
            try:
                jira_service = JiraService(use_real=True)
                story_data = jira_service.get_story(workflow.jira_story_id)
                if not story_data:
                    use_real_jira = False
            except Exception as e:
                logger.warning(f"[WorkflowExecutor] Jira story {workflow.jira_story_id} not found: {e}")
                use_real_jira = False
            
            # Create and run the enhanced workflow
            enhanced_workflow = EnhancedStoryWorkflow(
                story_id=workflow.jira_story_id,
                use_real_jira=use_real_jira,
                use_real_github=True,
                workflow_id=workflow_id  # Pass workflow_id for LLM tracking
            )
            
            # Run the workflow and get results
            results = enhanced_workflow.run()
            
            # Store the workflow log in the database
            if hasattr(enhanced_workflow, 'workflow_log') and enhanced_workflow.workflow_log:
                for log_entry in enhanced_workflow.workflow_log:
                    # Get or create conversation with enhanced data
                    conversation = Conversation(
                        workflow_id=workflow_id,
                        step=log_entry.get('step', 'unknown'),
                        agent=log_entry.get('agent', 'unknown'),
                        status=log_entry.get('status', 'completed'),
                        details=log_entry.get('details', ''),
                        output=log_entry.get('output', ''),
                        prompt=log_entry.get('prompt', '')
                    )
                    db.add(conversation)
                    db.flush()
                    
                    # Store code files if they exist
                    if 'code_files' in log_entry and log_entry['code_files']:
                        from crewai_app.database import CodeFile
                        for file_path in log_entry['code_files']:
                            code_file = CodeFile(
                                workflow_id=workflow_id,
                                conversation_id=conversation.id,
                                filename=file_path.split('/')[-1],
                                file_path=file_path,
                                file_type='generated'
                            )
                            db.add(code_file)
            
            # Update workflow status to completed
            workflow.status = "completed"
            db.commit()
            
            logger.info(f"[WorkflowExecutor] Completed background execution for workflow {workflow_id}")
            
        except Exception as e:
            logger.error(f"[WorkflowExecutor] Background execution failed for workflow {workflow_id}: {e}")
            
            # Update workflow status to error
            try:
                db = next(get_db())
                workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
                if workflow:
                    workflow.status = "error"
                    db.commit()
            except Exception as db_error:
                logger.error(f"[WorkflowExecutor] Failed to update workflow status: {db_error}")
        
        finally:
            # Remove from running workflows
            with self._lock:
                if workflow_id in self.running_workflows:
                    del self.running_workflows[workflow_id]
    
    def get_workflow_status(self, workflow_id: int) -> Dict[str, Any]:
        """Get current status of a workflow"""
        with self._lock:
            if workflow_id in self.running_workflows:
                workflow_info = self.running_workflows[workflow_id]
                return {
                    "workflow_id": workflow_id,
                    "status": "running",
                    "start_time": workflow_info["start_time"].isoformat(),
                    "duration_seconds": (datetime.utcnow() - workflow_info["start_time"]).total_seconds()
                }
            else:
                # Check database for final status
                try:
                    db = next(get_db())
                    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
                    if workflow:
                        return {
                            "workflow_id": workflow_id,
                            "status": workflow.status,
                            "message": f"Workflow is {workflow.status}"
                        }
                    else:
                        return {
                            "workflow_id": workflow_id,
                            "status": "not_found",
                            "message": "Workflow not found"
                        }
                except Exception as e:
                    logger.error(f"[WorkflowExecutor] Failed to get workflow status: {e}")
                    return {
                        "workflow_id": workflow_id,
                        "status": "error",
                        "message": f"Failed to get status: {e}"
                    }
    
    def get_running_workflows(self) -> Dict[int, Dict[str, Any]]:
        """Get all currently running workflows"""
        with self._lock:
            return {
                workflow_id: {
                    "start_time": info["start_time"].isoformat(),
                    "duration_seconds": (datetime.utcnow() - info["start_time"]).total_seconds()
                }
                for workflow_id, info in self.running_workflows.items()
            }

# Global executor instance
workflow_executor = WorkflowExecutor()
