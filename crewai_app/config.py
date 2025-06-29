import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    azure_openai_api_key: str = os.getenv("AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment: str = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    environment: str = os.getenv("ENVIRONMENT", "development")
    # Multi-model support
    deployment_pm: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_PM", azure_openai_deployment)
    deployment_architect: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_ARCHITECT", azure_openai_deployment)
    deployment_developer: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_DEVELOPER", azure_openai_deployment)
    deployment_reviewer: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_REVIEWER", azure_openai_deployment)
    deployment_tester: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_REVIEWER", azure_openai_deployment)

settings = Settings() 