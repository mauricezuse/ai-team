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

    def implement(self, prompt: str) -> str:
        """Generate code based on the given prompt."""
        return self._openai_service.generate(prompt, step="developer.implement")

class DeveloperAgent:
    def implement_story(self, story, plan, rules):
        # If the story is a prompt string, generate both backend and frontend stubs
        if isinstance(story, str):
            # Backend file (from plan)
            backend_file = plan['details'].get('file', 'backend/auto_backend.py')
            backend_code = f"# Backend implementation for story\n# (Python, FastAPI)\n# TODO: Implement actual logic for: {story}\n"
            # Frontend Angular component stub
            frontend_file = 'frontend/profile/src/app/auto-component/auto-component.component.ts'
            frontend_code = (
                "import { Component } from '@angular/core';\n"
                "@Component({\n"
                "  selector: 'app-auto-component',\n"
                "  templateUrl: './auto-component.component.html',\n"
                "  styleUrls: ['./auto-component.component.css']\n"
                "})\n"
                "export class AutoComponent {\n"
                "  // TODO: Implement Angular logic for: " + story + "\n"
                "}\n"
            )
            return [
                {"file": backend_file, "code": backend_code},
                {"file": frontend_file, "code": frontend_code}
            ]
        # Otherwise, fallback to previous logic
        target_file = plan['details'].get('file')
        target_function = plan['details'].get('function')
        implementation_result = {
            "code": f"# Implemented code in {target_file}, function {target_function}\n",
            "file": target_file,
            "function": target_function,
            "notes": "Followed full_path imports as per rules.",
            "compliance": True
        }
        if not target_file or not target_function:
            implementation_result["compliance"] = False
            implementation_result["warning"] = "Architect plan missing file/function details."
        return implementation_result

    def break_down_story(self, story, plan, rules):
        """
        Use the LLM to break down a story into actionable development tasks/subtasks with clear titles and acceptance criteria.
        Returns a list of dicts: [{"title": ..., "description": ..., "acceptance_criteria": ...}, ...]
        """
        prompt = (
            f"Break down the following story into actionable development tasks. "
            f"For each task, provide a title, a short description, and acceptance criteria.\n"
            f"Story: {story}\n"
            f"Implementation Plan: {plan}\n"
            f"Rules: {rules}\n"
            f"Output a Python list of dicts with keys: 'title', 'description', 'acceptance_criteria'."
        )
        tasks_str = developer_tool._run(prompt)
        try:
            tasks = eval(tasks_str, {"__builtins__": {}})
            if isinstance(tasks, list):
                return tasks
        except Exception:
            pass
        return []

    def select_relevant_files(self, task, plan, codebase_index):
        """
        Use the LLM to select the most relevant files from the codebase index for the given task and plan.
        Returns a list of file paths.
        """
        prompt = (
            f"Given the following development task and implementation plan, select the most relevant files from the codebase index.\n"
            f"Task: {task}\n"
            f"Implementation Plan: {plan}\n"
            f"Codebase Index: {list(codebase_index.keys())}\n"
            f"Output a Python list of file paths."
        )
        files_str = developer_tool._run(prompt)
        try:
            files = eval(files_str, {"__builtins__": {}})
            if isinstance(files, list) and all(isinstance(f, str) for f in files):
                return files
        except Exception:
            pass
        # Fallback: return all files
        return list(codebase_index.keys())

    def implement_task(self, task, plan, rules, codebase_index):
        # Two-stage: first select relevant files, then generate code
        selected_files = self.select_relevant_files(task, plan, codebase_index)
        selected_index = {f: codebase_index[f] for f in selected_files if f in codebase_index}
        prompt = (
            f"Implement the following task as part of the story. "
            f"Generate both backend (Python, FastAPI) and frontend (Angular, native federation) code as needed. "
            f"Only generate code for the following files: {selected_files}. "
            f"If multiple files are needed, output a list of dicts with 'file' and 'code' keys for each file.\n"
            f"Task: {task}\n"
            f"Implementation Plan: {plan}\n"
            f"Rules: {rules}\n"
            f"Selected Codebase Files: {selected_index}\n"
        )
        result_str = developer_tool._run(prompt)
        try:
            result = eval(result_str, {"__builtins__": {}})
            if isinstance(result, list):
                return result
        except Exception:
            pass
        # Fallback: return a stub
        return [{"file": "backend/auto_backend.py", "code": f"# TODO: Implement: {task}"}]

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