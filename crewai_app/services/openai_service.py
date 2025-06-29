import openai
from crewai_app.config import settings

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

class OpenAIService:
    def __init__(self, deployment=None):
        self.deployment = deployment or settings.azure_openai_deployment
        self.api_key = settings.azure_openai_api_key
        self.api_base = settings.azure_openai_endpoint

    def generate(self, prompt: str, max_tokens: int = 512, deployment: str = None):
        deployment_name = deployment or self.deployment
        config = DEPLOYMENT_CONFIG.get(deployment_name, DEPLOYMENT_CONFIG["default"])
        client = openai.AzureOpenAI(
            api_key=self.api_key,
            api_version=config["api_version"],
            azure_endpoint=self.api_base,
        )
        params = {
            "model": deployment_name,
            "messages": [{"role": "user", "content": prompt}]
        }
        params[config["token_param"]] = max_tokens
        response = client.chat.completions.create(**params)
        return response.choices[0].message.content 