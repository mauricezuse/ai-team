from crewai import Agent
from crewai.tools import BaseTool
from pydantic import PrivateAttr
from crewai_app.services.openai_service import OpenAIService
from crewai_app.config import settings
import hashlib
import json
import os
import itertools
from crewai_app.utils.logger import logger
import time

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

# Parse comma-separated deployment names from config
architect_deployments = [d.strip() for d in getattr(settings, 'deployment_architect', '').split(',') if d.strip()]
deployment_cycle = itertools.cycle(architect_deployments) if architect_deployments else None

def get_next_deployment():
    if deployment_cycle:
        deployment = next(deployment_cycle)
        logger.info(f"[Architect] Selected deployment: {deployment}")
        return deployment
    deployment = getattr(settings, 'deployment_architect', None)
    logger.info(f"[Architect] Selected deployment (fallback): {deployment}")
    return deployment

class ArchitectTool(BaseTool):
    name: str = "architect_tool"
    description: str = "Generates architecture designs using OpenAI."
    _openai_service: OpenAIService = PrivateAttr()

    def __init__(self, openai_service):
        super().__init__()
        self._openai_service = openai_service

    def _run(self, prompt: str, deployment=None) -> str:
        return self._openai_service.generate(prompt, deployment=deployment)

    def greet(self):
        return self._run("Say hello from the Architect agent!")

class ArchitectAgent:
    def __init__(self, openai_service, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.llm_service = openai_service

    def _cache_get(self, key):
        if not hasattr(self, '_llm_cache'):
            self._llm_cache = {}
        return self._llm_cache.get(key)

    def _cache_set(self, key, value):
        if not hasattr(self, '_llm_cache'):
            self._llm_cache = {}
        self._llm_cache[key] = value

    def _prompt_hash(self, prompt):
        return hashlib.sha256(prompt.encode('utf-8')).hexdigest()

    def select_relevant_files(self, story, pm_suggestions, codebase_index):
        description = story['fields'].get('description', '') if isinstance(story, dict) else str(story)
        summary = story['fields'].get('summary', '') if isinstance(story, dict) else ''
        description = str(description)[:250]
        pm_suggestions = str(pm_suggestions)[:250]
        file_paths = list(codebase_index.keys())[:10]
        prompt = f"Story: {summary}\nDescription: {description}\nPM Suggestions: {pm_suggestions}\nFiles: {file_paths}"
        if len(prompt) > 2000:
            prompt = f"Story: {summary[:100]}\nFiles: {[f[:40] for f in file_paths]}"
        prompt_hash = self._prompt_hash(prompt)
        cached = self._cache_get(prompt_hash)
        if cached:
            return cached
        time.sleep(10)  # Throttle architect LLM calls
        deployment = get_next_deployment()
        logger.info(f"[ArchitectAgent] Using deployment: {deployment} for select_relevant_files")
        try:
            result = self.llm_service.generate(prompt, deployment=deployment, step="select_relevant_files")
            self._cache_set(prompt_hash, result)
            return result
        except Exception as e:
            logger.warning(f"ArchitectAgent.select_relevant_files fallback: {e}")
            fallback = f"Files: {[f[:40] for f in file_paths]}"
            self._cache_set(prompt_hash, fallback)
            return fallback

    def review_and_plan(self, story, pm_suggestions, selected_index):
        description = story['fields'].get('description', '') if isinstance(story, dict) else str(story)
        summary = story['fields'].get('summary', '') if isinstance(story, dict) else ''
        description = str(description)[:250]
        pm_suggestions = str(pm_suggestions)[:250]
        file_names = list(selected_index.keys())[:5]
        prompt = f"Story: {summary}\nDescription: {description}\nPM Suggestions: {pm_suggestions}\nSelected Files: {file_names}"
        if len(prompt) > 2000:
            prompt = f"Story: {summary[:100]}\nFiles: {[f[:40] for f in file_names]}"
        prompt_hash = self._prompt_hash(prompt)
        cached = self._cache_get(prompt_hash)
        if cached:
            return cached, {}
        time.sleep(10)  # Throttle architect LLM calls
        deployment = get_next_deployment()
        logger.info(f"[ArchitectAgent] Using deployment: {deployment} for review_and_plan")
        try:
            result = self.llm_service.generate(prompt, deployment=deployment, step="review_and_plan")
            self._cache_set(prompt_hash, result)
            return result, {}
        except Exception as e:
            logger.warning(f"ArchitectAgent.review_and_plan fallback: {e}")
            fallback = f"Files: {[f[:40] for f in file_names]}"
            self._cache_set(prompt_hash, fallback)
            return fallback, {}

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