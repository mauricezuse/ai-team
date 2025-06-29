from crewai import Agent
from crewai.tools import BaseTool
from pydantic import PrivateAttr
from crewai_app.services.openai_service import OpenAIService
from crewai_app.config import settings

class ArchitectTool(BaseTool):
    name: str = "architect_tool"
    description: str = "Generates architecture designs using OpenAI."
    _openai_service: OpenAIService = PrivateAttr()

    def __init__(self, openai_service):
        super().__init__()
        self._openai_service = openai_service

    def _run(self, prompt: str) -> str:
        return self._openai_service.generate(prompt)

    def greet(self):
        return self._run("Say hello from the Architect agent!")

architect_openai = OpenAIService(deployment=settings.deployment_architect)
architect_tool = ArchitectTool(architect_openai)
architect = Agent(
    role="Architect",
    goal="Design data models, API endpoints, and component structure for each story.",
    backstory="A seasoned software architect with a passion for scalable systems.",
    tools=[architect_tool],
)

if __name__ == "__main__":
    print("Architect says:", architect_tool.greet()) 