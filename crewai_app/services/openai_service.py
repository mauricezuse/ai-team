import openai
from crewai_app.config import settings
import time
import logging
from typing import Optional, List, TYPE_CHECKING, Any
import uuid
import json

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

try:
    import tiktoken
except ImportError:
    from typing import Any
    tiktoken: Any = None

def count_tokens(text: str, model: str = "gpt-4") -> int:
    if tiktoken is None:
        return len(text.split())  # fallback: rough word count
    try:
        enc = tiktoken.encoding_for_model(model)
        return len(enc.encode(text))
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
    def __init__(self, deployment: Optional[str] = None):
        self.deployment = deployment or settings.azure_openai_deployment or ""
        self.api_key = settings.azure_openai_api_key
        self.api_base = settings.azure_openai_endpoint or ""

    @staticmethod
    def count_tokens(prompt: str) -> int:
        # Fallback: count tokens as words if tiktoken is not available
        if tiktoken:
            try:
                enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
                return len(enc.encode(prompt))
            except Exception:
                pass
        return len(prompt.split())

    def generate(self, prompt: str, max_tokens: int = 512, deployment: Optional[str] = None, step: Optional[str] = None) -> str:
        prompt_length = self.count_tokens(prompt)
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
        deployment_name = deployment or self.deployment
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
                # Ensure we always return a string
                if response.choices and response.choices[0].message and response.choices[0].message.content:
                    return response.choices[0].message.content
                else:
                    return ""
            except Exception as e:
                # Check for rate limit or transient errors
                is_rate_limit = hasattr(e, 'status_code') and getattr(e, 'status_code', None) == 429
                is_httpx_429 = hasattr(e, 'response') and hasattr(e.response, 'status_code') and e.response.status_code == 429
                usage_logger.warning(f"[ERROR] model={model_name} error={e} attempt={attempt+1}/{max_retries}")
                if is_rate_limit or is_httpx_429 or '429' in str(e):
                    logging.warning(f"OpenAI rate limit hit (attempt {attempt+1}/{max_retries}). Retrying in {delay} seconds...")
                    time.sleep(delay)
                    delay *= 2
                else:
                    logging.error(f"OpenAIService error: {e}")
                    raise
        logging.error("OpenAIService: Exceeded max retries for OpenAI API call.")
        usage_logger.error(f"[FAILED] model={model_name} Exceeded max retries for OpenAI API call.")
        raise RuntimeError("OpenAIService: Exceeded max retries for OpenAI API call.") 