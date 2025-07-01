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

    def review(self, prompt: str) -> str:
        """Review code based on the given prompt."""
        return self._openai_service.generate(prompt, step="reviewer.review")

class ReviewerAgent:
    def review_implementation(self, implementation_result, plan, rules):
        # Review the implementation against the plan and rules
        expected_file = plan['details'].get('file')
        expected_function = plan['details'].get('function')
        actual_file = implementation_result.get('file')
        actual_function = implementation_result.get('function')
        compliant = (
            implementation_result.get('compliance') and
            actual_file == expected_file and
            actual_function == expected_function
        )
        review_result = {
            "approved": compliant,
            "comments": "Implementation matches architect's plan and rules." if compliant else f"Mismatch: expected {expected_file}.{expected_function}, got {actual_file}.{actual_function}"
        }
        return review_result

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