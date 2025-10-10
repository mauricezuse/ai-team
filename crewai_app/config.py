import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class Settings(BaseSettings):
    azure_openai_api_key: Optional[str] = os.getenv("AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: Optional[str] = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment: Optional[str] = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    environment: str = os.getenv("ENVIRONMENT", "development")
    # Multi-model support
    deployment_pm: Optional[str] = os.getenv("AZURE_OPENAI_DEPLOYMENT_PM", azure_openai_deployment)
    deployment_architect: Optional[str] = os.getenv("AZURE_OPENAI_DEPLOYMENT_ARCHITECT", azure_openai_deployment)
    deployment_developer: Optional[str] = os.getenv("AZURE_OPENAI_DEPLOYMENT_DEVELOPER", azure_openai_deployment)
    deployment_reviewer: Optional[str] = os.getenv("AZURE_OPENAI_DEPLOYMENT_REVIEWER", azure_openai_deployment)
    deployment_tester: Optional[str] = os.getenv("AZURE_OPENAI_DEPLOYMENT_REVIEWER", azure_openai_deployment)
    deployment_frontend: Optional[str] = os.getenv("AZURE_OPENAI_DEPLOYMENT_FRONTEND", azure_openai_deployment)
    project_key: Optional[str] = os.getenv("PROJECT_KEY", "NEGISHI")
    use_real_github: bool = os.getenv("USE_REAL_GITHUB", "false").lower() == "true"
    use_real_jira: bool = os.getenv("USE_REAL_JIRA", "false").lower() == "true"
    github_webhook_secret: Optional[str] = os.getenv("GITHUB_WEBHOOK_SECRET")

settings = Settings() 