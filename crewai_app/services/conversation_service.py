"""
Conversation Service - Handles conversation persistence, message tracking, and LLM call governance
"""
import hashlib
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from crewai_app.database import get_db, Conversation, Message, LLMCall, Workflow, with_db_retry, SafeDBSession
from crewai_app.utils.logger import logger
from crewai_app.services.event_stream import post_event
from crewai_app.utils.logging_sse import get_logging_sse_helper


class ConversationService:
    """
    Service for managing conversation persistence, message tracking, and LLM call governance.
    Provides conversation creation, message appending, artifact linking, and LLM call recording.
    """
    
    def __init__(self, workflow_id: int, agent_name: str, step_name: str):
        self.workflow_id = workflow_id
        self.agent_name = agent_name
        self.step_name = step_name
        self.current_conversation_id: Optional[int] = None
        self.logging_sse = get_logging_sse_helper(workflow_id)
    
    @with_db_retry(max_retries=5, delay=0.2)
    def get_or_create_conversation(self, status: str = "running") -> int:
        """Get or create a conversation for the current workflow/agent/step"""
        try:
            with SafeDBSession() as db:
                # Look for existing conversation for this workflow/agent/step
                conversation = db.query(Conversation).filter(
                    Conversation.workflow_id == self.workflow_id,
                    Conversation.agent == self.agent_name,
                    Conversation.step == self.step_name
                ).first()
                
                if not conversation:
                    # Create new conversation
                    conversation = Conversation(
                        workflow_id=self.workflow_id,
                        agent=self.agent_name,
                        step=self.step_name,
                        status=status,
                        timestamp=datetime.utcnow()
                    )
                    db.add(conversation)
                    db.flush()
                    
                    # Emit conversation creation event
                    post_event(self.workflow_id, {
                        "type": "conversation",
                        "conversation": {
                            "id": conversation.id,
                            "step": conversation.step,
                            "agent": conversation.agent,
                            "status": conversation.status,
                            "timestamp": conversation.timestamp.isoformat()
                        }
                    })
                    
                    # Log with SSE parity
                    self.logging_sse.log_workflow_start(self.workflow_id, self.agent_name, self.step_name)
                    logger.info(f"[ConversationService] Created conversation {conversation.id} for {self.agent_name}/{self.step_name}")
                
                self.current_conversation_id = conversation.id
                return conversation.id
                
        except Exception as e:
            logger.error(f"[ConversationService] Failed to get/create conversation: {e}")
            raise
    
    @with_db_retry(max_retries=5, delay=0.2)
    def append_message(self, role: str, content: str, artifacts: Optional[List[Dict[str, Any]]] = None, 
                      metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Append a message to the current conversation.
        
        Args:
            role: one of [system|user|assistant|tool]
            content: concise text (up to 3K tokens), large blobs should be summarized and linked
        artifacts: array of {type, id, uri, checksum?}
        metadata: {agent_name, step_name, conversation_id, created_at}
        """
        if not self.current_conversation_id:
            self.get_or_create_conversation()
        
        try:
            with SafeDBSession() as db:
                # Prepare message metadata
                message_metadata = {
                    "agent_name": self.agent_name,
                    "step_name": self.step_name,
                    "conversation_id": self.current_conversation_id,
                    "created_at": datetime.utcnow().isoformat()
                }
                if metadata:
                    message_metadata.update(metadata)
                
                # Create message record
                message = Message(
                    conversation_id=self.current_conversation_id,
                    role=role,
                    content=content,
                    artifacts=artifacts or [],
                    message_metadata=message_metadata
                )
                db.add(message)
                db.flush()
                
                # Emit message event
                post_event(self.workflow_id, {
                    "type": "message",
                    "message": {
                        "id": message.id,
                        "conversation_id": self.current_conversation_id,
                        "role": role,
                        "content": content[:500] + "..." if len(content) > 500 else content,  # Truncate for event
                        "artifacts": artifacts or [],
                        "message_metadata": message_metadata
                    }
                })
                
                # Log with SSE parity
                self.logging_sse.log_conversation(
                    self.agent_name, self.step_name, role, content, message.id
                )
                logger.info(f"[ConversationService] Appended {role} message {message.id} to conversation {self.current_conversation_id}")
                return message.id
                
        except Exception as e:
            logger.error(f"[ConversationService] Failed to append message: {e}")
            raise
    
    def record_llm_call(self, model: str, prompt: str, response: str, prompt_tokens: int, 
                       completion_tokens: int, max_tokens: int, response_time_ms: int,
                       status: str = "success", error_code: Optional[str] = None,
                       truncated_sections: Optional[List[str]] = None,
                       budget_snapshot: Optional[Dict[str, Any]] = None) -> int:
        """
        Record an LLM call with governance data.
        
        Args:
            model: Model name (e.g., "gpt-4")
            prompt: Input prompt
            response: Model response
            prompt_tokens: Actual prompt tokens used
            completion_tokens: Actual completion tokens used
            max_tokens: Max tokens requested
            response_time_ms: Response latency
            status: success|failed|truncated|skipped
            error_code: Error code if failed
            truncated_sections: List of truncated parts
            budget_snapshot: {prompt_budget_remaining, step_budget_remaining}
        """
        if not self.current_conversation_id:
            self.get_or_create_conversation()
        
        try:
            db = next(get_db())
            
            # Calculate hashes for deduplication
            prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
            response_hash = hashlib.sha256(response.encode()).hexdigest()
            
            total_tokens = prompt_tokens + completion_tokens
            total_tokens_requested = prompt_tokens + max_tokens
            
            # Calculate cost (approximate GPT-4 pricing)
            cost_per_1k_tokens = 0.03
            cost = (total_tokens / 1000) * cost_per_1k_tokens
            
            # Create LLM call record
            llm_call = LLMCall(
                conversation_id=self.current_conversation_id,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                max_tokens=max_tokens,
                total_tokens_requested=total_tokens_requested,
                response_time_ms=response_time_ms,
                status=status,
                error_code=error_code,
                truncated_sections=truncated_sections or [],
                prompt_hash=prompt_hash,
                response_hash=response_hash,
                budget_snapshot=budget_snapshot or {},
                cost=f"{cost:.4f}",
                request_data={
                    "messages": [{"role": "user", "content": prompt}],
                    "model": model,
                    "max_tokens": max_tokens
                },
                response_data={
                    "content": response,
                    "usage": {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": total_tokens
                    }
                }
            )
            db.add(llm_call)
            db.flush()
            
            # Update conversation aggregated data
            conversation = db.query(Conversation).filter(Conversation.id == self.current_conversation_id).first()
            if conversation:
                # Update or create llm_calls JSON array
                existing_calls = conversation.llm_calls if conversation.llm_calls else []
                if isinstance(existing_calls, str):
                    existing_calls = json.loads(existing_calls)
                
                # Add new call to the array
                new_call_data = {
                    "model": model,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "cost": f"{cost:.4f}",
                    "response_time_ms": response_time_ms,
                    "status": status,
                    "timestamp": datetime.utcnow().isoformat(),
                    "truncated_sections": truncated_sections or [],
                    "budget_snapshot": budget_snapshot or {}
                }
                existing_calls.append(new_call_data)
                
                # Update conversation totals
                conversation.llm_calls = existing_calls
                conversation.total_tokens_used = (conversation.total_tokens_used or 0) + total_tokens
                conversation.total_cost = f"{(float(conversation.total_cost or 0) + cost):.4f}"
            
            db.commit()
            
            # Emit LLM call event
            post_event(self.workflow_id, {
                "type": "llm_call",
                "llm_call": {
                    "id": llm_call.id,
                    "conversation_id": self.current_conversation_id,
                    "model": model,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "status": status,
                    "response_time_ms": response_time_ms,
                    "cost": f"{cost:.4f}"
                }
            })
            
            # Log with SSE parity
            self.logging_sse.log_llm_call(
                self.agent_name, self.step_name, model, prompt_tokens, completion_tokens,
                total_tokens, response_time_ms, status, f"{cost:.4f}"
            )
            logger.info(f"[ConversationService] Recorded LLM call {llm_call.id}: {model}, {total_tokens} tokens, ${cost:.4f}, status={status}")
            return llm_call.id
            
        except Exception as e:
            logger.error(f"[ConversationService] Failed to record LLM call: {e}")
            raise
    
    def update_conversation_status(self, status: str, details: Optional[str] = None, output: Optional[str] = None):
        """Update the current conversation status"""
        if not self.current_conversation_id:
            return
        
        try:
            db = next(get_db())
            conversation = db.query(Conversation).filter(Conversation.id == self.current_conversation_id).first()
            if conversation:
                conversation.status = status
                if details:
                    conversation.details = details
                if output:
                    conversation.output = output
                db.commit()
                
                # Emit status update event
                post_event(self.workflow_id, {
                    "type": "conversation_status",
                    "conversation": {
                        "id": self.current_conversation_id,
                        "status": status,
                        "details": details,
                        "output": output
                    }
                })
                
                logger.info(f"[ConversationService] Updated conversation {self.current_conversation_id} status to {status}")
                
        except Exception as e:
            logger.error(f"[ConversationService] Failed to update conversation status: {e}")
    
    def create_terminal_message(self, error_message: str, token_math: Dict[str, Any], 
                              truncated_info: Optional[Dict[str, Any]] = None,
                              resume_hint: Optional[str] = None) -> int:
        """
        Create a terminal error message with failure details and resume hints.
        
        Args:
            error_message: What failed
            token_math: {prompt_tokens, max_tokens, available_tokens, safety_buffer}
            truncated_info: What was truncated
            resume_hint: Next recommended action for resuming
        """
        terminal_content = f"TERMINAL ERROR: {error_message}\n\n"
        terminal_content += f"Token Math: {json.dumps(token_math, indent=2)}\n\n"
        
        if truncated_info:
            terminal_content += f"Truncated: {json.dumps(truncated_info, indent=2)}\n\n"
        
        if resume_hint:
            terminal_content += f"Resume Hint: {resume_hint}"
        
        # Log terminal error with SSE parity
        self.logging_sse.log_terminal_error(
            self.agent_name, self.step_name, error_message, token_math, resume_hint
        )
        
        return self.append_message(
            role="system",
            content=terminal_content,
            metadata={
                "terminal": True,
                "error_type": "token_governance",
                "resume_hint": resume_hint
            }
        )
    
    def save_resumable_checkpoint(self, step_name: str, running_summary: str, 
                                 recent_turns_window_hash: str, artifacts_index: Dict[str, Any],
                                 budgets_remaining: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save a resumable checkpoint with conversation state.
        
        Returns:
            Checkpoint data for resuming execution
        """
        checkpoint = {
            "step_name": step_name,
            "running_summary": running_summary,
            "recent_turns_window_hash": recent_turns_window_hash,
            "artifacts_index": artifacts_index,
            "budgets_remaining": budgets_remaining,
            "conversation_id": self.current_conversation_id,
            "workflow_id": self.workflow_id,
            "agent_name": self.agent_name,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Emit checkpoint event
        post_event(self.workflow_id, {
            "type": "checkpoint",
            "checkpoint": checkpoint
        })
        
        # Log checkpoint with SSE parity
        self.logging_sse.log_checkpoint(
            step_name, running_summary, len(artifacts_index)
        )
        
        logger.info(f"[ConversationService] Saved resumable checkpoint for {self.agent_name}/{step_name}")
        return checkpoint
