from crewai import Agent
from crewai.tools import BaseTool
from pydantic import PrivateAttr
from crewai_app.services.openai_service import OpenAIService
from crewai_app.config import settings

class CodeGeneratorTool(BaseTool):
    name: str = "code_generator_tool"
    description: str = "Generates code using OpenAI."
    _openai_service: OpenAIService = PrivateAttr()

    def __init__(self, openai_service):
        super().__init__()
        self._openai_service = openai_service

    def _run(self, prompt: str) -> str:
        return self._openai_service.generate(prompt)

    def greet(self):
        return self._run("Say hello from the Developer agent!")

developer_openai = OpenAIService(deployment=settings.deployment_developer)
developer_tool = CodeGeneratorTool(developer_openai)
developer = Agent(
    role="Developer",
    goal="Write Angular and Python code for the designed stories.",
    backstory="A passionate developer who loves clean, production-ready code.",
    tools=[developer_tool],
)

if __name__ == "__main__":
    print("Developer says:", developer_tool.greet()) 