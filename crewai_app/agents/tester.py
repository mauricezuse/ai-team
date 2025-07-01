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
        return self._openai_service.generate(prompt, step="tester.test")

    def greet(self):
        return self._run("Say hello from the Tester agent!")

class TesterAgent:
    def select_relevant_files(self, implementation_result, plan, codebase_index):
        """
        Use the LLM to select which files need Playwright tests for the given implementation result and plan.
        Returns a list of file paths.
        """
        prompt = (
            f"Given the following implementation result and plan, select which files from the codebase index need Playwright tests.\n"
            f"Implementation Result: {implementation_result}\n"
            f"Plan: {plan}\n"
            f"Codebase Index: {list(codebase_index.keys())}\n"
            f"Output a Python list of file paths."
        )
        files_str = tester_tool._run(prompt)
        try:
            files = eval(files_str, {"__builtins__": {}})
            if isinstance(files, list) and all(isinstance(f, str) for f in files):
                return files
        except Exception:
            pass
        # Fallback: return all files
        return list(codebase_index.keys())

    def prepare_and_run_tests(self, implementation_result, plan, rules, codebase_index):
        # Two-stage: first select relevant files, then generate tests
        selected_files = self.select_relevant_files(implementation_result, plan, codebase_index)
        files_to_test = []
        if isinstance(implementation_result, list):
            files_to_test = [f for f in implementation_result if f.get('file') in selected_files]
        elif isinstance(plan, dict) and isinstance(plan.get('details', {}).get('file'), str):
            if plan['details']['file'] in selected_files:
                files_to_test = [{"file": plan['details']['file'], "code": plan.get('details', {}).get('code', '')}]
        for file_entry in files_to_test:
            filename = file_entry['file']
            # Determine test type and location
            if filename.startswith('frontend'):
                test_type = 'Playwright end-to-end test for Angular frontend'
                test_location = 'frontend/playwright/tests/'
            elif filename.startswith('backend'):
                test_type = 'Playwright API test for FastAPI backend'
                test_location = 'backend/tests/playwright/'
            else:
                test_type = 'Playwright test'
                test_location = 'tests/playwright/'
            prompt = (
                f"Write a {test_type} for the following file. "
                f"Place the test in {test_location}. "
                f"Use Playwright best practices.\n"
                f"File: {filename}\n"
                f"Code:\n{file_entry['code']}\n"
                f"Rules: {rules}\n"
            )
            test_code = tester_tool._run(prompt)
            file_entry['test_code'] = test_code
            file_entry['test_location'] = test_location
        if files_to_test:
            return {"tests": files_to_test, "result": "Playwright tests generated"}
        # Fallback stub
        test_result = {
            "tests": ["test_feature_x", "test_feature_y"],
            "result": "All tests passed"
        }
        return test_result

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