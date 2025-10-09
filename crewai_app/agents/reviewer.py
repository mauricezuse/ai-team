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
    def review_implementation(self, implementation_result, plan, rules, workflow_id=None, conversation_id=None):
        # Support both old and new plan formats
        if isinstance(plan, dict) and 'details' in plan:
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
        # New plan section: list of tasks (dicts with 'title', 'description', etc.)
        if isinstance(plan, list):
            # Approve if any file in implementation_result matches a file in any plan task (if specified)
            implemented_files = set()
            if isinstance(implementation_result, list):
                for entry in implementation_result:
                    if 'file' in entry:
                        implemented_files.add(entry['file'])
            elif isinstance(implementation_result, dict) and 'file' in implementation_result:
                implemented_files.add(implementation_result['file'])
            plan_files = set()
            for task in plan:
                if isinstance(task, dict) and 'file' in task:
                    plan_files.add(task['file'])
            # If plan doesn't specify files, just approve if implementation_result is non-empty
            if not plan_files:
                approved = bool(implemented_files)
                comments = "Implementation present. No specific file required by plan."
            else:
                approved = bool(implemented_files & plan_files)
                comments = "Implementation matches plan files." if approved else f"Mismatch: expected one of {plan_files}, got {implemented_files}"
            return {"approved": approved, "comments": comments}
        # Fallback: approve if implementation_result is non-empty
        approved = bool(implementation_result)
        comments = "Implementation present. Plan format not recognized."
        return {"approved": approved, "comments": comments}

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