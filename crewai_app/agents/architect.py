from crewai import Agent
from crewai.tools import BaseTool
from pydantic import PrivateAttr
from crewai_app.services.openai_service import OpenAIService
from crewai_app.config import settings
import hashlib
import json
import os

CACHE_PATH = os.path.join(os.path.dirname(__file__), '../../workflow_results/llm_cache.json')

def _load_llm_cache():
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, 'r') as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {}

def _save_llm_cache(cache):
    with open(CACHE_PATH, 'w') as f:
        json.dump(cache, f, indent=2)

def _cache_key(prompt):
    return hashlib.sha256(prompt.encode('utf-8')).hexdigest()

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

class ArchitectAgent:
    def select_relevant_files(self, story, pm_suggestions, codebase_index):
        """
        Use the LLM to select the most relevant files from the codebase index for the given story and PM suggestions.
        Returns a list of file paths.
        """
        description = story['fields'].get('description', '') if isinstance(story, dict) else str(story)
        summary = story['fields'].get('summary', '') if isinstance(story, dict) else ''
        prompt = (
            f"Given the following Jira story, PM suggestions, and codebase index, select the most relevant files for implementation.\n"
            f"Jira Story Description: {description}\n"
            f"Summary: {summary}\n"
            f"PM Suggestions: {pm_suggestions}\n"
            f"Codebase Index: {list(codebase_index.keys())}\n"
            f"Output a Python list of file paths."
        )
        cache = _load_llm_cache()
        key = _cache_key(prompt)
        if key in cache:
            files_str = cache[key]
        else:
            files_str = architect_tool._run(prompt)
            cache[key] = files_str
            _save_llm_cache(cache)
        try:
            files = eval(files_str, {"__builtins__": {}})
            if isinstance(files, list) and all(isinstance(f, str) for f in files):
                return files
        except Exception:
            pass
        # Fallback: return all files
        return list(codebase_index.keys())

    def review_and_plan(self, story, pm_suggestions, global_rules, codebase_index):
        # Two-stage: first select relevant files, then plan
        selected_files = self.select_relevant_files(story, pm_suggestions, codebase_index)
        selected_index = {f: codebase_index[f] for f in selected_files if f in codebase_index}
        description = story['fields'].get('description', '') if isinstance(story, dict) else str(story)
        summary = story['fields'].get('summary', '') if isinstance(story, dict) else ''
        prompt = (
            f"You are an expert software architect. Given the following Jira story, PM suggestions, and selected codebase files, "
            f"create a detailed implementation plan. Specify backend and frontend requirements, file locations, and architectural patterns.\n"
            f"Jira Story Description: {description}\n"
            f"Summary: {summary}\n"
            f"PM Suggestions: {pm_suggestions}\n"
            f"Selected Codebase Files: {selected_index}\n"
            f"Output a Python dict with keys: 'backend', 'frontend', 'files', 'patterns', 'notes'."
        )
        cache = _load_llm_cache()
        key = _cache_key(prompt)
        try:
            if key in cache:
                plan_str = cache[key]
            else:
                plan_str = architect_tool._run(prompt)
                cache[key] = plan_str
                _save_llm_cache(cache)
            plan = eval(plan_str, {"__builtins__": {}})
            if isinstance(plan, dict):
                updated_rules = global_rules.copy()
                updated_rules['coding_style']['imports'] = 'full_path'
                llm_feedback = self.llm_validate_plan(plan, selected_index)
                plan['llm_feedback'] = llm_feedback
                return plan, updated_rules
        except Exception as e:
            # Fallback: retry with a smaller prompt if rate limit or prompt too large
            print(f"[Architect] Rate limit or prompt too large encountered: {e}. Retrying with smaller prompt.")
            small_prompt = (
                f"You are an expert software architect. Given the following Jira story summary, PM suggestions, and a list of file names, "
                f"create a high-level implementation plan. Only list backend/frontend requirements and file names.\n"
                f"Summary: {summary}\n"
                f"PM Suggestions: {pm_suggestions}\n"
                f"File Names: {list(selected_index.keys())}\n"
                f"Output a Python dict with keys: 'backend', 'frontend', 'files', 'patterns', 'notes'."
            )
            try:
                plan_str = architect_tool._run(small_prompt)
                plan = eval(plan_str, {"__builtins__": {}})
                if isinstance(plan, dict):
                    updated_rules = global_rules.copy()
                    updated_rules['coding_style']['imports'] = 'full_path'
                    plan['llm_feedback'] = '[Fallback: Used smaller prompt due to rate limit or prompt size]'
                    return plan, updated_rules
            except Exception as e2:
                print(f"[Architect] Fallback prompt also failed: {e2}")
        # Fallback to previous logic
        target_file = None
        target_function = None
        for file, info in selected_index.items():
            if info['functions']:
                target_file = file
                target_function = info['functions'][0]['name']
                break
        plan = {
            "implementation": f"Add logic to {target_function} in {target_file}",
            "details": {
                "file": target_file,
                "function": target_function,
                "pattern": global_rules['architecture']['layering'],
                "notes": "Use full path imports and follow existing error handling."
            },
            "tech_stack": "FastAPI, MySQL"
        }
        updated_rules = global_rules.copy()
        updated_rules['coding_style']['imports'] = 'full_path'
        plan['llm_feedback'] = '[Fallback: Used stub plan due to repeated errors]'
        return plan, updated_rules

    def llm_validate_plan(self, plan, codebase_index):
        prompt = (
            "You are an expert software architect. "
            "Given the following codebase index and implementation plan, "
            "does the plan fit the codebase? Suggest improvements or corrections if needed.\n"
            f"Codebase Index: {codebase_index}\n"
            f"Implementation Plan: {plan}\n"
            "Respond with a short assessment and any recommended changes."
        )
        response = OpenAIService().generate(prompt, max_tokens=256, step="architect.llm_validate_plan")
        return response

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