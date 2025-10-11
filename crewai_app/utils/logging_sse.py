"""
Logging and SSE Events Helper - Ensures parity between file logging and real-time event streams
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from crewai_app.services.event_stream import post_event
from crewai_app.utils.logger import logger


class LoggingSSEHelper:
    """
    Helper class to ensure parity between file logging and SSE event streams.
    All significant events should be logged to both file and SSE.
    """
    
    def __init__(self, workflow_id: int):
        self.workflow_id = workflow_id
        self.logger = logger
    
    def log_and_emit(self, level: str, message: str, data: Optional[Dict[str, Any]] = None, 
                    event_type: str = "log", **kwargs):
        """
        Log to file and emit to SSE stream with parity.
        
        Args:
            level: log level (info, warning, error, debug)
            message: log message
            data: additional data for the event
            event_type: type of event (log, conversation, metric, error)
            **kwargs: additional fields for the event
        """
        # Prepare event data
        event_data = {
            "type": event_type,
            "level": level,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "workflow_id": self.workflow_id
        }
        
        if data:
            event_data["data"] = data
        
        # Add any additional kwargs
        event_data.update(kwargs)
        
        # Log to file
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_message = f"[{self.workflow_id}] {message}"
        if data:
            log_message += f" | Data: {data}"
        log_method(log_message)
        
        # Emit to SSE stream
        post_event(self.workflow_id, event_data)
    
    def log_workflow_start(self, workflow_id: int, agent_name: str, step_name: str):
        """Log workflow start with both file and SSE"""
        self.log_and_emit(
            level="info",
            message=f"Starting workflow step: {agent_name}/{step_name}",
            event_type="workflow",
            agent_name=agent_name,
            step_name=step_name,
            action="start"
        )
    
    def log_workflow_step(self, agent_name: str, step_name: str, status: str, details: Optional[str] = None):
        """Log workflow step with both file and SSE"""
        self.log_and_emit(
            level="info",
            message=f"Workflow step {agent_name}/{step_name}: {status}",
            event_type="workflow",
            agent_name=agent_name,
            step_name=step_name,
            status=status,
            details=details
        )
    
    def log_llm_call(self, agent_name: str, step_name: str, model: str, prompt_tokens: int, 
                    completion_tokens: int, total_tokens: int, response_time_ms: int, 
                    status: str = "success", cost: Optional[str] = None):
        """Log LLM call with both file and SSE"""
        self.log_and_emit(
            level="info",
            message=f"LLM call: {model} | {total_tokens} tokens | {response_time_ms}ms | {status}",
            event_type="llm_call",
            agent_name=agent_name,
            step_name=step_name,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            response_time_ms=response_time_ms,
            status=status,
            cost=cost
        )
    
    def log_conversation(self, agent_name: str, step_name: str, role: str, content_preview: str, 
                        message_id: Optional[int] = None):
        """Log conversation message with both file and SSE"""
        self.log_and_emit(
            level="info",
            message=f"Conversation {role}: {content_preview[:100]}...",
            event_type="conversation",
            agent_name=agent_name,
            step_name=step_name,
            role=role,
            content_preview=content_preview,
            message_id=message_id
        )
    
    def log_escalation(self, from_agent: str, to_agent: str, reason: str, priority: str = "normal"):
        """Log escalation with both file and SSE"""
        self.log_and_emit(
            level="warning",
            message=f"Escalation: {from_agent} -> {to_agent}: {reason}",
            event_type="escalation",
            from_agent=from_agent,
            to_agent=to_agent,
            reason=reason,
            priority=priority
        )
    
    def log_collaboration(self, from_agent: str, to_agent: str, request_type: str, data_preview: str):
        """Log collaboration request with both file and SSE"""
        self.log_and_emit(
            level="info",
            message=f"Collaboration: {from_agent} -> {to_agent}: {request_type}",
            event_type="collaboration",
            from_agent=from_agent,
            to_agent=to_agent,
            request_type=request_type,
            data_preview=data_preview
        )
    
    def log_error(self, agent_name: str, step_name: str, error_message: str, error_type: str = "error", 
                 details: Optional[Dict[str, Any]] = None):
        """Log error with both file and SSE"""
        self.log_and_emit(
            level="error",
            message=f"Error in {agent_name}/{step_name}: {error_message}",
            event_type="error",
            agent_name=agent_name,
            step_name=step_name,
            error_message=error_message,
            error_type=error_type,
            details=details
        )
    
    def log_token_governance(self, agent_name: str, step_name: str, prompt_tokens: int, 
                           max_tokens: int, available_tokens: int, shrunk: bool = False,
                           truncated_sections: Optional[list] = None):
        """Log token governance decisions with both file and SSE"""
        self.log_and_emit(
            level="warning" if shrunk else "info",
            message=f"Token governance: {prompt_tokens} prompt, {max_tokens} max, {available_tokens} available" + 
                   (" (shrunk)" if shrunk else ""),
            event_type="token_governance",
            agent_name=agent_name,
            step_name=step_name,
            prompt_tokens=prompt_tokens,
            max_tokens=max_tokens,
            available_tokens=available_tokens,
            shrunk=shrunk,
            truncated_sections=truncated_sections or []
        )
    
    def log_checkpoint(self, step_name: str, running_summary: str, artifacts_count: int):
        """Log checkpoint creation with both file and SSE"""
        self.log_and_emit(
            level="info",
            message=f"Checkpoint saved for {step_name}: {artifacts_count} artifacts",
            event_type="checkpoint",
            step_name=step_name,
            running_summary_preview=running_summary[:200] + "..." if len(running_summary) > 200 else running_summary,
            artifacts_count=artifacts_count
        )
    
    def log_terminal_error(self, agent_name: str, step_name: str, error_message: str, 
                          token_math: Optional[Dict[str, Any]] = None, resume_hint: Optional[str] = None):
        """Log terminal error with both file and SSE"""
        self.log_and_emit(
            level="error",
            message=f"TERMINAL ERROR in {agent_name}/{step_name}: {error_message}",
            event_type="terminal_error",
            agent_name=agent_name,
            step_name=step_name,
            error_message=error_message,
            token_math=token_math,
            resume_hint=resume_hint
        )


def get_logging_sse_helper(workflow_id: int) -> LoggingSSEHelper:
    """Get a logging SSE helper for the given workflow"""
    return LoggingSSEHelper(workflow_id)
