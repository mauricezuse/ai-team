import os
from dotenv import load_dotenv
import openai

load_dotenv()

api_key = os.getenv("AZURE_OPENAI_API_KEY")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
deployments = {
    "DEVELOPER": os.getenv("AZURE_OPENAI_DEPLOYMENT_DEVELOPER"),
    "REVIEWER": os.getenv("AZURE_OPENAI_DEPLOYMENT_REVIEWER"),
    "ARCHITECT": os.getenv("AZURE_OPENAI_DEPLOYMENT_ARCHITECT"),
    "PM": os.getenv("AZURE_OPENAI_DEPLOYMENT_PM"),
    "TESTER": os.getenv("AZURE_OPENAI_DEPLOYMENT_TESTER"),
}

api_versions = {
    "DEVELOPER": "2023-05-15",
    "REVIEWER": "2023-05-15",
    "ARCHITECT": "2023-05-15",
    "PM": "2023-05-15",
    "TESTER": "2024-12-01-preview",
}

for role, deployment in deployments.items():
    try:
        print(f"Testing {role} deployment: {deployment}")
        client = openai.AzureOpenAI(
            api_key=api_key,
            api_version=api_versions[role],
            azure_endpoint=endpoint,
        )
        if role == "TESTER":
            response = client.chat.completions.create(
                model=deployment,
                messages=[{"role": "user", "content": f"Say hello from the {role} model!"}],
                max_completion_tokens=10,
            )
        else:
            response = client.chat.completions.create(
                model=deployment,
                messages=[{"role": "user", "content": f"Say hello from the {role} model!"}],
                max_tokens=10,
            )
        print(f"  Success: {response.choices[0].message.content}\n")
    except Exception as e:
        print(f"  ERROR: {e}\n") 