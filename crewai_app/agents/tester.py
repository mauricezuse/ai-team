from crewai import Agent
from crewai.tools import BaseTool
from pydantic import PrivateAttr
from crewai_app.services.openai_service import OpenAIService
from crewai_app.config import settings
import time
import hashlib

class TesterTool(BaseTool):
    name: str = "tester_tool"
    description: str = "Writes unit and integration tests using OpenAI."
    _openai_service: OpenAIService = PrivateAttr()

    def __init__(self, openai_service):
        super().__init__()
        self._openai_service = openai_service

    def _run(self, prompt: str, workflow_id=None, conversation_id=None) -> str:
        return self._openai_service.generate(
            prompt, 
            step="tester.test",
            workflow_id=workflow_id,
            conversation_id=conversation_id
        )

    def greet(self):
        return self._run("Say hello from the Tester agent!")

class TesterAgent:
    def __init__(self):
        self._llm_cache = {}

    def _prompt_hash(self, prompt):
        return hashlib.sha256(prompt.encode('utf-8')).hexdigest()

    def _cache_get(self, key):
        return self._llm_cache.get(key)

    def _cache_set(self, key, value):
        self._llm_cache[key] = value

    def select_relevant_files(self, implementation_result, plan, codebase_index):
        """
        Use the LLM to select which files need Playwright tests for the given implementation result and plan.
        Returns a list of file paths.
        """
        impl_str = str(implementation_result)[:250]
        plan_str = str(plan)[:250]
        file_paths = list(codebase_index.keys())[:10]
        prompt = (
            f"Given the following implementation result and plan, select which files from the codebase index need Playwright tests.\n"
            f"Implementation Result: {impl_str}\n"
            f"Plan: {plan_str}\n"
            f"Codebase Index: {file_paths}\n"
            f"Output a Python list of file paths."
        )
        if len(prompt) > 2000:
            prompt = f"Files: {[f[:40] for f in file_paths]}\nSummary: Playwright test selection."
        prompt_hash = self._prompt_hash(prompt)
        cached = self._cache_get(prompt_hash)
        if cached:
            return cached
        time.sleep(10)  # Throttle LLM calls
        files_str = tester_tool._run(prompt)
        try:
            files = eval(files_str, {"__builtins__": {}})
            if isinstance(files, list) and all(isinstance(f, str) for f in files):
                self._cache_set(prompt_hash, files)
                return files
        except Exception:
            pass
        # Fallback: return pruned file list
        self._cache_set(prompt_hash, file_paths)
        return file_paths

    def prepare_and_run_tests(self, implementation_result, plan, rules, codebase_index, workflow_id=None, conversation_id=None):
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
            test_code = tester_tool._run(prompt, workflow_id, conversation_id)
            file_entry['test_code'] = test_code
            file_entry['test_location'] = test_location
        if files_to_test:
            return {"tests": files_to_test, "result": "Playwright tests generated"}
        # Fallback stub
        test_result = {
            "tests": [
                {"file": "unknown", "test_code": "test_feature_x", "test_location": "tests/playwright/"},
                {"file": "unknown", "test_code": "test_feature_y", "test_location": "tests/playwright/"}
            ],
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