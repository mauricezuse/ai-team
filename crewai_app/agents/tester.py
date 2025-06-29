from crewai import Agent
from crewai.tools import BaseTool
from pydantic import PrivateAttr
from crewai_app.services.openai_service import OpenAIService
from crewai_app.config import settings

class TesterTool(BaseTool):
    name: str = "tester_tool"
    description: str = "Writes unit and integration tests using OpenAI."
    _openai_service: OpenAIService = PrivateAttr()

    def __init__(self, openai_service):
        super().__init__()
        self._openai_service = openai_service

    def _run(self, prompt: str) -> str:
        return self._openai_service.generate(prompt)

    def greet(self):
        return self._run("Say hello from the Tester agent!")

tester_openai = OpenAIService(deployment=settings.deployment_tester)
tester_tool = TesterTool(tester_openai)
tester = Agent(
    role="Tester",
    goal="Write unit and integration tests for the code.",
    backstory="A dedicated tester who ensures code reliability and coverage.",
    tools=[tester_tool],
)

if __name__ == "__main__":
    print("Tester says:", tester_tool.greet()) 