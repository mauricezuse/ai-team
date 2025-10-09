"""
LLM Tracking Service - Captures real LLM call data for workflow conversations
"""
import time
import json
from typing import Optional, Dict, Any
from datetime import datetime
from crewai_app.services.openai_service import OpenAIService
from crewai_app.database import get_db, Conversation, LLMCall
from crewai_app.utils.logger import logger

class LLMTrackingService:
    """
    Wrapper service that tracks LLM calls and stores them in the database
    """
    
    def __init__(self, openai_service: OpenAIService, workflow_id: Optional[int] = None, conversation_id: Optional[int] = None):
        self.openai_service = openai_service
        self.workflow_id = workflow_id
        self.conversation_id = conversation_id
        self.llm_calls = []
    
    def generate(self, prompt: str, max_tokens: int = 512, deployment: Optional[str] = None, step: Optional[str] = None) -> str:
        """Generate response and track LLM call data"""
        start_time = time.time()
        
        # Make the actual LLM call
        response = self.openai_service.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            deployment=deployment,
            step=step,
            workflow_id=self.workflow_id,
            conversation_id=self.conversation_id
        )
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Store LLM call data
        llm_call_data = {
            "model": deployment or "gpt-4",
            "prompt": prompt,
            "response": response,
            "response_time_ms": response_time_ms,
            "timestamp": datetime.utcnow().isoformat(),
            "step": step
        }
        
        self.llm_calls.append(llm_call_data)
        
        # If we have conversation_id, store in database
        if self.conversation_id:
            self._store_llm_call_in_db(llm_call_data)
        
        return response
    
    def _store_llm_call_in_db(self, llm_call_data: Dict[str, Any]):
        """Store LLM call data in the database"""
        try:
            db = next(get_db())
            
            # Create LLMCall record
            llm_call = LLMCall(
                conversation_id=self.conversation_id,
                model=llm_call_data["model"],
                prompt_tokens=self._estimate_tokens(llm_call_data["prompt"]),
                completion_tokens=self._estimate_tokens(llm_call_data["response"]),
                total_tokens=self._estimate_tokens(llm_call_data["prompt"]) + self._estimate_tokens(llm_call_data["response"]),
                cost=self._calculate_cost(llm_call_data),
                response_time_ms=llm_call_data["response_time_ms"],
                request_data={
                    "messages": [{"role": "user", "content": llm_call_data["prompt"]}],
                    "model": llm_call_data["model"],
                    "step": llm_call_data["step"]
                },
                response_data={
                    "content": llm_call_data["response"],
                    "usage": {
                        "prompt_tokens": self._estimate_tokens(llm_call_data["prompt"]),
                        "completion_tokens": self._estimate_tokens(llm_call_data["response"]),
                        "total_tokens": self._estimate_tokens(llm_call_data["prompt"]) + self._estimate_tokens(llm_call_data["response"])
                    }
                }
            )
            db.add(llm_call)
            
            # Update conversation with aggregated data
            conversation = db.query(Conversation).filter(Conversation.id == self.conversation_id).first()
            if conversation:
                # Update or create llm_calls JSON array
                existing_calls = conversation.llm_calls if conversation.llm_calls else []
                if isinstance(existing_calls, str):
                    existing_calls = json.loads(existing_calls)
                
                # Add new call to the array
                new_call_data = {
                    "model": llm_call_data["model"],
                    "prompt_tokens": llm_call.prompt_tokens,
                    "completion_tokens": llm_call.completion_tokens,
                    "total_tokens": llm_call.total_tokens,
                    "cost": llm_call.cost,
                    "response_time_ms": llm_call_data["response_time_ms"],
                    "timestamp": llm_call_data["timestamp"],
                    "request_data": llm_call.request_data,
                    "response_data": llm_call.response_data
                }
                existing_calls.append(new_call_data)
                
                # Update conversation
                conversation.llm_calls = existing_calls
                conversation.total_tokens_used = (conversation.total_tokens_used or 0) + llm_call.total_tokens
                conversation.total_cost = f"{(float(conversation.total_cost or 0) + float(llm_call.cost)):.4f}"
            
            db.commit()
            logger.info(f"[LLMTrackingService] Captured LLM call: {llm_call_data['model']}, {llm_call.total_tokens} tokens, ${llm_call.cost}")
            
        except Exception as e:
            logger.error(f"[LLMTrackingService] Failed to store LLM call data: {e}")
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        try:
            import tiktoken
            enc = tiktoken.encoding_for_model("gpt-4")
            return len(enc.encode(text))
        except ImportError:
            return len(text.split())  # fallback: rough word count
        except Exception:
            return len(text.split())
    
    def _calculate_cost(self, llm_call_data: Dict[str, Any]) -> str:
        """Calculate cost based on token usage"""
        prompt_tokens = self._estimate_tokens(llm_call_data["prompt"])
        completion_tokens = self._estimate_tokens(llm_call_data["response"])
        total_tokens = prompt_tokens + completion_tokens
        
        # GPT-4 pricing: $0.03 per 1K tokens
        cost_per_1k_tokens = 0.03
        cost = (total_tokens / 1000) * cost_per_1k_tokens
        return f"{cost:.4f}"
    
    def get_llm_calls(self) -> list:
        """Get all captured LLM calls"""
        return self.llm_calls
    
    def clear_llm_calls(self):
        """Clear captured LLM calls"""
        self.llm_calls = []
