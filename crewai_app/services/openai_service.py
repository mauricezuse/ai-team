import openai
from crewai_app.config import settings
import time
import logging
from typing import Optional, List, TYPE_CHECKING, Any, Dict
import uuid
import json
import threading
import itertools

if TYPE_CHECKING:
    try:
        from openai.types.chat import ChatCompletionMessageParam
    except ImportError:
        ChatCompletionMessageParam = dict  # type: ignore
else:
    ChatCompletionMessageParam = dict  # fallback for runtime

# Map deployment to API version and token parameter
DEPLOYMENT_CONFIG = {
    settings.deployment_tester: {
        "api_version": "2024-12-01-preview",
        "token_param": "max_completion_tokens"
    },
    # Default for all others
    "default": {
        "api_version": "2023-05-15",
        "token_param": "max_tokens"
    }
}

# Setup usage logging
usage_logger = logging.getLogger("openai_usage")
usage_logger.setLevel(logging.INFO)
usage_handler = logging.FileHandler("openai_usage.log")
usage_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
if not usage_logger.hasHandlers():
    usage_logger.addHandler(usage_handler)

def count_tokens(text: str, model: str = "gpt-4") -> int:
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model(model)
        return len(enc.encode(text))
    except ImportError:
        return len(text.split())  # fallback: rough word count
    except Exception:
        return len(text.split())

MAX_PROMPT_TOKENS = 32000  # Adjust to your model's context window

class PromptTooLargeError(Exception):
    def __init__(self, prompt_length, step=None):
        msg = f"Prompt too large: {prompt_length} tokens."
        if step:
            msg += f" Step: {step}."
        super().__init__(msg)
        self.prompt_length = prompt_length
        self.step = step

class OpenAIService:
    # Shared rate limit state for all instances
    _rate_limited_until: Dict[str, float] = {}
    _lock = threading.Lock()

    def __init__(self, deployment: Optional[str] = None):
        self.deployment = deployment or settings.azure_openai_deployment or ""
        self.api_key = settings.azure_openai_api_key
        self.api_base = settings.azure_openai_endpoint or ""
        # Parse deployments if comma-separated
        if self.deployment and "," in self.deployment:
            self.deployments = [d.strip() for d in self.deployment.split(",") if d.strip()]
        else:
            self.deployments = [self.deployment] if self.deployment else []
        self._deployment_cycle = itertools.cycle(self.deployments) if self.deployments else None
        logging.info(f"[OpenAIService.__init__] Instantiated with deployment: '{self.deployment}' | api_base: '{self.api_base}'")

    def _get_next_available_deployment(self):
        if not self._deployment_cycle:
            return self.deployment
        now = time.time()
        for _ in range(len(self.deployments)):
            candidate = next(self._deployment_cycle)
            with self._lock:
                until = self._rate_limited_until.get(candidate, 0)
            if now >= until:
                return candidate
        # All are rate-limited; find soonest available
        soonest = min(self._rate_limited_until.get(d, 0) for d in self.deployments)
        wait = max(soonest - now, 1)
        logging.warning(f"All architect deployments are rate-limited. Waiting {wait:.1f} seconds for next available.")
        time.sleep(wait)
        # After wait, try again
        return self._get_next_available_deployment()

    @staticmethod
    def count_tokens(prompt: str) -> int:
        try:
            import tiktoken
            enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
            return len(enc.encode(prompt))
        except ImportError:
            return len(prompt.split())  # fallback: rough word count
        except Exception:
            return len(prompt.split())

    def generate(self, prompt: str, max_tokens: int = 512, deployment: Optional[str] = None, step: Optional[str] = None, workflow_id: Optional[int] = None, conversation_id: Optional[int] = None) -> str:
        prompt_length = self.count_tokens(prompt)
        logging.info(f"[OpenAIService] Prompt size: {prompt_length} tokens (max {MAX_PROMPT_TOKENS}) at step '{step}'")
        if prompt_length > MAX_PROMPT_TOKENS * 0.9:
            logging.warning(f"[OpenAIService] Prompt size is close to the model's context window: {prompt_length} tokens at step '{step}'")
        if prompt_length > MAX_PROMPT_TOKENS:
            logging.error(f"Prompt too large: {prompt_length} tokens at step '{step}'. Aborting call.")
            # Log to openai_usage.log as well
            with open('openai_usage.log', 'a') as f:
                f.write(json.dumps({
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "event": "prompt_too_large",
                    "step": step,
                    "prompt_length": prompt_length
                }) + "\n")
            raise PromptTooLargeError(prompt_length, step)
        # Improved load balancing: select next available deployment
        deployment_name = deployment or self._get_next_available_deployment()
        logging.info(f"[OpenAIService] Using deployment: '{deployment_name}' | api_base: '{self.api_base}' | step: '{step}'")
        if not deployment_name:
            logging.warning(f"[OpenAIService] WARNING: No deployment name set for step '{step}'. This may cause requests to go to the wrong model.")
        config = DEPLOYMENT_CONFIG.get(deployment_name, DEPLOYMENT_CONFIG["default"])
        client = openai.AzureOpenAI(
            api_key=self.api_key,
            api_version=config["api_version"],
            azure_endpoint=self.api_base,
        )
        # Prepare payload
        messages = [{"role": "user", "content": prompt}]
        token_param = config["token_param"]
        payload = {
            "model": deployment_name,
            "messages": messages,
            token_param: max_tokens
        }
        # Generate a unique request ID for traceability
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Log the payload before making the call
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "request_id": request_id,
            "event": "request_payload",
            "payload": {
                "model": deployment_name,
                "max_tokens": max_tokens,
                "prompt_length": OpenAIService.count_tokens(prompt),
                "messages": messages
            }
        }
        with open("openai_usage.log", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        model_name = deployment_name
        prompt_tokens = count_tokens(prompt, model=model_name)
        total_tokens_requested = prompt_tokens + max_tokens
        usage_logger.info(f"[REQUEST] model={model_name} prompt_tokens={prompt_tokens} max_tokens={max_tokens} total_tokens_requested={total_tokens_requested}")

        max_retries = 6
        delay = 1
        for attempt in range(max_retries):
            logging.info(f"[OpenAIService] Attempt {attempt+1}/{max_retries} with deployment: {deployment_name} at step '{step}'")
            try:
                # Cast messages to Any to satisfy type checker for openai SDK
                if token_param == "max_tokens":
                    response = client.chat.completions.create(
                        model=deployment_name,
                        messages=messages,  # type: ignore
                        max_tokens=max_tokens
                    )
                else:
                    response = client.chat.completions.create(
                        model=deployment_name,
                        messages=messages,  # type: ignore
                        max_completion_tokens=max_tokens
                    )
                # Log response token usage if available
                usage = getattr(response, 'usage', None)
                if usage:
                    usage_logger.info(f"[RESPONSE] model={model_name} prompt_tokens={getattr(usage, 'prompt_tokens', None)} completion_tokens={getattr(usage, 'completion_tokens', None)} total_tokens={getattr(usage, 'total_tokens', None)}")
                
                # Capture LLM call data for database storage
                if workflow_id and conversation_id:
                    self._capture_llm_call(
                        workflow_id=workflow_id,
                        conversation_id=conversation_id,
                        model=deployment_name,
                        prompt=prompt,
                        response=response,
                        start_time=start_time,
                        request_id=request_id
                    )
                
                # Ensure we always return a string
                if response.choices and response.choices[0].message and response.choices[0].message.content:
                    return response.choices[0].message.content
                else:
                    return ""
            except Exception as e:
                # Check for rate limit or transient errors
                is_rate_limit = hasattr(e, 'status_code') and getattr(e, 'status_code', None) == 429
                is_httpx_429 = hasattr(e, 'response') and hasattr(e.response, 'status_code') and e.response.status_code == 429
                if is_rate_limit or is_httpx_429 or '429' in str(e):
                    # Mark this deployment as rate-limited
                    retry_after = 60  # default
                    if hasattr(e, 'response') and hasattr(e.response, 'headers'):
                        headers = e.response.headers
                        retry_after = int(headers.get('Retry-After', retry_after))
                    with self._lock:
                        self._rate_limited_until[deployment_name] = time.time() + retry_after
                    logging.warning(f"Deployment {deployment_name} hit rate limit (429). Skipping for {retry_after} seconds.")
                    # Log all deployments' rate limit status
                    now = time.time()
                    statuses = []
                    for d in self.deployments:
                        until = self._rate_limited_until.get(d, 0)
                        status = f"{d}: {'available' if now >= until else f'rate-limited until {until-now:.1f}s'}"
                        statuses.append(status)
                    logging.warning(f"[OpenAIService] Deployment statuses after rate limit: {statuses}")
                    all_limited = all(self._rate_limited_until.get(d, 0) > now for d in self.deployments)
                    if all_limited:
                        soonest = min(self._rate_limited_until.get(d, 0) for d in self.deployments)
                        wait = max(soonest - now, 1)
                        logging.warning(f"[OpenAIService] All deployments rate-limited. Soonest available in {wait:.1f}s.")
                    deployment_name = self._get_next_available_deployment()
                    config = DEPLOYMENT_CONFIG.get(deployment_name, DEPLOYMENT_CONFIG["default"])
                    client = openai.AzureOpenAI(
                        api_key=self.api_key,
                        api_version=config["api_version"],
                        azure_endpoint=self.api_base,
                    )
                    continue
                usage_logger.warning(f"[ERROR] model={deployment_name} error={e} attempt={attempt+1}/{max_retries}")
                logging.error(f"OpenAIService error: {e}")
                raise
        logging.error("OpenAIService: Exceeded max retries for OpenAI API call.")
        usage_logger.error(f"[FAILED] model={deployment_name} Exceeded max retries for OpenAI API call.")
        raise RuntimeError("OpenAIService: Exceeded max retries for OpenAI API call.")
    
    def _capture_llm_call(self, workflow_id: int, conversation_id: int, model: str, prompt: str, response, start_time: float, request_id: str):
        """Capture LLM call data and store in database"""
        try:
            from crewai_app.database import get_db, Conversation, LLMCall
            import json
            from datetime import datetime
            
            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Extract usage data
            usage = getattr(response, 'usage', None)
            prompt_tokens = getattr(usage, 'prompt_tokens', 0) if usage else 0
            completion_tokens = getattr(usage, 'completion_tokens', 0) if usage else 0
            total_tokens = getattr(usage, 'total_tokens', 0) if usage else 0
            
            # Calculate cost (approximate GPT-4 pricing)
            cost_per_1k_tokens = 0.03  # $0.03 per 1K tokens for GPT-4
            cost = (total_tokens / 1000) * cost_per_1k_tokens
            
            # Prepare request and response data
            request_data = {
                "messages": [{"role": "user", "content": prompt}],
                "model": model,
                "max_tokens": getattr(response, 'max_tokens', 512)
            }
            
            response_data = {
                "content": response.choices[0].message.content if response.choices and response.choices[0].message else "",
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens
                }
            }
            
            # Get database session
            db = next(get_db())
            
            # Create LLMCall record
            llm_call = LLMCall(
                conversation_id=conversation_id,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost=f"{cost:.4f}",
                response_time_ms=response_time_ms,
                request_data=request_data,
                response_data=response_data
            )
            db.add(llm_call)
            
            # Update conversation with aggregated data
            conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
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
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_data": request_data,
                    "response_data": response_data
                }
                existing_calls.append(new_call_data)
                
                # Update conversation
                conversation.llm_calls = existing_calls
                conversation.total_tokens_used = (conversation.total_tokens_used or 0) + total_tokens
                conversation.total_cost = f"{(float(conversation.total_cost or 0) + cost):.4f}"
            
            db.commit()
            logging.info(f"[OpenAIService] Captured LLM call: {model}, {total_tokens} tokens, ${cost:.4f}")
            
        except Exception as e:
            logging.error(f"[OpenAIService] Failed to capture LLM call data: {e}")
            # Don't raise exception to avoid breaking the main workflow 