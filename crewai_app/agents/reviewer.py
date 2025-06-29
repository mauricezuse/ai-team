from crewai import Agent
from crewai.tools import BaseTool
from pydantic import PrivateAttr
from crewai_app.services.openai_service import OpenAIService
from crewai_app.config import settings

class ReviewerTool(BaseTool):
    name: str = "reviewer_tool"
    description: str = "Reviews code for correctness, style, and best practices using OpenAI."
    _openai_service: OpenAIService = PrivateAttr()

    def __init__(self, openai_service):
        super().__init__()
        self._openai_service = openai_service

    def _run(self, prompt: str) -> str:
        return self._openai_service.generate(prompt)

    def greet(self):
        return self._run("Say hello from the Reviewer agent!")

reviewer_openai = OpenAIService(deployment=settings.deployment_reviewer)
reviewer_tool = ReviewerTool(reviewer_openai)
reviewer = Agent(
    role="Reviewer",
    goal="Review code for correctness, style, and best practices.",
    backstory="A meticulous code reviewer who ensures quality and adherence to best practices.",
    tools=[reviewer_tool],
)

if __name__ == "__main__":
    print("Reviewer says:", reviewer_tool.greet()) 