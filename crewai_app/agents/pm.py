from crewai import Agent
from crewai.tools import BaseTool
from pydantic import PrivateAttr
from crewai_app.services.openai_service import OpenAIService
from crewai_app.config import settings

class PMTool(BaseTool):
    name: str = "pm_tool"
    description: str = "Breaks down features into user stories using OpenAI."
    _openai_service: OpenAIService = PrivateAttr()

    def __init__(self, openai_service):
        super().__init__()
        self._openai_service = openai_service

    def _run(self, prompt: str) -> str:
        return self._openai_service.generate(prompt)

    def greet(self):
        return self._run("Say hello from the Product Manager agent!")

pm_openai = OpenAIService(deployment=settings.deployment_pm)
pm_tool = PMTool(pm_openai)
pm = Agent(
    role="Product Manager",
    goal="Break down high-level features into clear, testable user stories.",
    backstory="A detail-oriented PM who ensures clarity and testability in every story.",
    tools=[pm_tool],
)

if __name__ == "__main__":
    print("PM says:", pm_tool.greet()) 