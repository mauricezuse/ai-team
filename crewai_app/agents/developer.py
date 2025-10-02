from crewai import Agent
from crewai.tools import BaseTool
from pydantic import PrivateAttr
from crewai_app.services.openai_service import OpenAIService
from crewai_app.config import settings
import logging
import json
import re
import subprocess
import os
from crewai_app.utils.text import strip_code_fences
import ast
from crewai_app.agents.base import BaseAgent

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

class DeveloperAgent(BaseAgent):
    # Backend-specific prompt template
    BASE_PROMPT = (
        "You are an expert Python/FastAPI backend developer with deep understanding of codebases.\n"
        "IMPORTANT: When updating existing files, analyze the current content and make intelligent, surgical updates.\n"
        "Preserve existing imports, classes, functions, and structure unless they need modification for the task.\n"
        "If frontend changes are required, collaborate with the frontend agent.\n"
        "If requirements are unclear, escalate to the architect or PM agent.\n"
        "Output only valid Python code, with no extra commentary.\n"
        "Use the provided codebase context to understand existing patterns and dependencies.\n"
        "Always include or update tests: unit tests, integration tests, and Playwright tests as applicable.\n"
    )
    def __init__(self, llm_service, *args, **kwargs):
        super().__init__(
            llm_service=llm_service,
            name="developer",
            role="Backend Developer",
            goal="Write Angular and Python code for the designed stories.",
            backstory="A passionate developer who loves clean, production-ready code.",
            tools=[],
        )
        self.logger.info(f"[DeveloperAgent.__init__] Instantiated with llm_service={type(llm_service)} deployment={getattr(llm_service, 'deployment', None)}")

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

    def break_down_story(self, story, plan, rules, api_contracts=None, max_retries=2):
        import re, json, logging
        print(f"[DeveloperAgent.break_down_story] ENTERED with story={story!r}, plan={plan!r}, rules={rules!r}, api_contracts={api_contracts!r}")
        self.logger.info(f"[break_down_story] ENTERED with story={story!r}, plan={plan!r}, rules={rules!r}, api_contracts={api_contracts!r}")
        if not story or not plan:
            print(f"[DeveloperAgent.break_down_story] SKIPPING: story or plan is None/empty. story={story!r}, plan={plan!r}")
            self.logger.warning(f"[break_down_story] SKIPPING: story or plan is None/empty. story={story!r}, plan={plan!r}")
            return []
        contract_section = f"API/Data Contracts: {api_contracts}\n" if api_contracts else ""
        base_prompt = (
            contract_section +
            f"Break down the following story into up to 3 actionable development tasks. For each task, provide a title, a short description, and acceptance criteria.\n"
            f"Output a JSON list of dicts with keys: 'title', 'description', 'acceptance_criteria'.\n"
            f"Do NOT wrap your output in triple backticks, code fences, or a code block. Output only raw JSON.\n"
            f"NEVER output partial or truncated strings. If you cannot fit the full output, return a single fallback task with title 'Implement Story', description 'Implement the story as described', and acceptance criteria matching the story's acceptance criteria.\n"
            f"Story: {story}\nRules: {rules}\n"
        )
        fallback_prompt = (
            contract_section +
            f"Return a JSON list with a single task: title 'Implement Story', description 'Implement the story as described', and acceptance criteria matching the story's acceptance criteria.\n"
            f"Do NOT wrap your output in triple backticks, code fences, or a code block. Output only raw JSON.\n"
            f"Story: {story}\nRules: {rules}\n"
        )
        for attempt in range(1, max_retries + 2):
            prompt = base_prompt if attempt == 1 else fallback_prompt
            self.logger.info(f"[break_down_story] LLM call attempt {attempt} with prompt: {prompt}")
            try:
                result_str = self.llm_service.generate(prompt, step="developer.break_down_story")
                self.last_llm_output = result_str
                self.logger.info(f"[break_down_story] LLM output (attempt {attempt}): {result_str}")
                cleaned = re.sub(r"^```json\\s*|^```|```$", "", result_str.strip(), flags=re.IGNORECASE | re.MULTILINE).strip()
                self.logger.info(f"[break_down_story] Cleaned output (attempt {attempt}): {cleaned}")
                tasks = json.loads(cleaned)
                if isinstance(tasks, list) and all(isinstance(t, dict) for t in tasks):
                    self.logger.info(f"[break_down_story] Parsed tasks (attempt {attempt}): {tasks}")
                    return tasks
            except Exception as e:
                self.logger.error(f"[break_down_story] Error in attempt {attempt}: {e}\nOutput: {locals().get('result_str', None)}")
        # Fallback: return a single generic task if all attempts fail
        fallback_task = [{
            "title": "Implement Story",
            "description": "Implement the story as described",
            "acceptance_criteria": f"Acceptance criteria: {story}"
        }]
        self.logger.warning(f"[break_down_story] Returning fallback task: {fallback_task}")
        return fallback_task

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
        self.logger.info(f"[select_relevant_files] LLM prompt: {prompt}")
        files_str = self.llm_service.generate(prompt, step="developer.select_relevant_files")
        self.logger.info(f"[select_relevant_files] LLM output: {files_str}")
        try:
            files = eval(files_str, {"__builtins__": {}})
            if isinstance(files, list) and all(isinstance(f, str) for f in files):
                self.logger.info(f"[select_relevant_files] Parsed files: {files}")
                return files
        except Exception as e:
            self.logger.error(f"[select_relevant_files] Error parsing output: {e}\nOutput: {files_str}")
        # Fallback: return all files
        self.logger.warning(f"[select_relevant_files] Returning all files as fallback.")
        return list(codebase_index.keys())

    def _file_committed_in_branch(self, file_path, branch, repo_root):
        """
        Returns True if file_path was last committed in the given branch.
        """
        rel_path = os.path.relpath(file_path, repo_root)
        try:
            result = subprocess.run([
                "git", "-C", repo_root, "log", branch, "--pretty=format:%H", "--", rel_path
            ], capture_output=True, text=True)
            return bool(result.stdout.strip())
        except Exception as e:
            logging.warning(f"[DeveloperAgent] Could not check git history for {file_path}: {e}")
            return False

    def implement_task(self, task, plan, rules, codebase_index, checkpoint=None, save_checkpoint=None, branch=None, repo_root=None, api_contracts=None):
        import re, ast, logging
        contract_section = f"API/Data Contracts: {api_contracts}\n" if api_contracts else ""
        def strip_code_fences(text):
            return re.sub(r"^```[a-zA-Z]*\\s*|```$", "", text.strip(), flags=re.IGNORECASE | re.MULTILINE).strip()
        def output_validator(text):
            try:
                result = ast.literal_eval(text)
                if isinstance(result, list) and all(isinstance(f, dict) and 'file' in f and 'code' in f for f in result):
                    return result
            except Exception:
                pass
            return None
        def build_multifile_prompt(task, plan, rules, codebase_index):
            return (
                contract_section +
                self.BASE_PROMPT +
                "---\n"
                f"Task: {task}\n"
                f"Implementation Plan: {plan}\n"
                f"Acceptance Criteria: {task.get('acceptance_criteria', '')}\n"
                f"Relevant Codebase Index: {list(codebase_index.keys())}\n"
                "---\n"
            )
        def build_file_list_prompt(task, plan, rules, codebase_index):
            return (
                contract_section +
                "List all files that need to be created or modified to implement the following backend task. Output ONLY a valid Python list of file paths, with NO extra commentary, explanations, or text. Do NOT include any text before or after the list. Repeat: Output ONLY a valid Python list, e.g. ['file1.py', 'file2.py'].\n"
                f"Task: {task}\n"
                f"Implementation Plan: {plan}\n"
                f"Acceptance Criteria: {task.get('acceptance_criteria', '')}\n"
                f"Relevant Codebase Index: {list(codebase_index.keys())}\n"
            )
        def build_single_file_prompt(task, plan, rules, codebase_index, file_path):
            # Get current file content if it exists
            current_content = ""
            if repo_root and file_path:
                full_path = os.path.join(repo_root, file_path)
                if os.path.exists(full_path):
                    try:
                        with open(full_path, 'r') as f:
                            current_content = f.read()
                    except Exception as e:
                        self.logger.warning(f"Could not read existing file {full_path}: {e}")
            
            # Analyze file structure and patterns
            file_analysis = ""
            if current_content:
                lines = current_content.split('\n')
                imports = [line.strip() for line in lines if line.strip().startswith(('import ', 'from '))]
                classes = [line.strip() for line in lines if line.strip().startswith('class ')]
                functions = [line.strip() for line in lines if line.strip().startswith('def ')]
                
                file_analysis = f"""
CURRENT FILE ANALYSIS:
- Total lines: {len(lines)}
- Imports: {len(imports)} found
- Classes: {len(classes)} found
- Functions: {len(functions)} found
- File exists: YES

CURRENT IMPORTS:
{chr(10).join(imports[:10])}

CURRENT CLASSES:
{chr(10).join(classes[:5])}

CURRENT FUNCTIONS:
{chr(10).join(functions[:5])}
"""
            else:
                file_analysis = """
CURRENT FILE ANALYSIS:
- File does not exist yet
- Will create new file with appropriate structure
"""
            
            # Get related files context
            related_files = []
            file_dir = os.path.dirname(file_path) if file_path else ""
            file_name = os.path.basename(file_path) if file_path else ""
            
            # Find related files in the same directory and parent directories
            for indexed_file in codebase_index.keys():
                if os.path.dirname(indexed_file) == file_dir and indexed_file != file_path:
                    related_files.append(indexed_file)
                elif file_dir and indexed_file.startswith(file_dir + '/') and indexed_file != file_path:
                    related_files.append(indexed_file)
            
            # Get project structure context
            project_structure = []
            for indexed_file in list(codebase_index.keys())[:20]:  # Limit to first 20 files
                if indexed_file.startswith('backend/'):
                    project_structure.append(indexed_file)
            
            # Get imports and dependencies context
            imports_context = ""
            if current_content:
                import_lines = [line.strip() for line in current_content.split('\n') if line.strip().startswith('import ') or line.strip().startswith('from ')]
                if import_lines:
                    imports_context = f"Current imports:\n" + '\n'.join(import_lines[:10]) + "\n\n"
            
            return (
                contract_section +
                self.BASE_PROMPT +
                f"Implement ONLY the code for the file: {file_path}.\n"
                "CRITICAL: If the file already exists, analyze the current content and make intelligent, surgical modifications.\n"
                "DO NOT replace the entire file unless absolutely necessary.\n"
                "Preserve existing imports, classes, functions, and structure unless they need modification for the task.\n"
                "Add new functionality by extending existing classes or adding new methods/functions.\n"
                "The code must be valid, complete, and ready to run.\n"
                "Do NOT output placeholder code, .txt files, or summaries.\n"
                "If you cannot generate valid code for this file, return an empty list [].\n"
                "MODIFICATION STRATEGY:\n"
                "1. If file exists: Analyze current structure and make minimal changes\n"
                "2. If adding new functionality: Extend existing classes/methods\n"
                "3. If modifying existing code: Preserve structure and add/update specific parts\n"
                "4. If file doesn't exist: Create new file with proper structure\n"
                "Output format example:\n"
                "[\n  {\"file\": \"backend/apps/platform_service/api/endpoints/auto_backend.py\", \"code\": \"# Example code\"}\n]\n"
                "Do NOT wrap your output in triple backticks or code fences.\n"
                f"Task: {task}\n"
                f"Implementation Plan: {plan}\n"
                f"Acceptance Criteria: {task.get('acceptance_criteria', '')}\n"
                f"Target File: {file_path}\n"
                f"{file_analysis}\n"
                f"Current File Content:\n{current_content}\n"
                f"{imports_context}"
                f"Related Files in Project: {related_files[:10]}\n"
                f"Project Structure (backend files): {project_structure[:10]}\n"
                f"Relevant Codebase Context: {codebase_index.get(file_path, {})}\n"
                f"Codebase Index Keys: {list(codebase_index.keys())[:20]}\n"
            )
        return self.generate_code_with_fallback(
            task, plan, rules, codebase_index,
            build_multifile_prompt, build_file_list_prompt, build_single_file_prompt,
            strip_code_fences, output_validator, step_prefix="developer"
        )

    def escalate_to_frontend(self, reason: str, context: dict = None):
        """
        Escalate a task to the frontend agent for UI or integration support.
        Example usage: self.escalate_to_frontend('Need new UI for new API endpoint', context)
        """
        self.escalate(reason, to_agent="frontend", context=context)

    def escalate_to_architect_or_pm(self, reason: str, context: dict = None):
        """
        Escalate a task to the architect or PM agent for requirements or design clarification.
        Example usage: self.escalate_to_architect_or_pm('Unclear requirements for backend logic', context)
        """
        self.escalate(reason, to_agent="architect/pm", context=context)

    def handle_collaboration_request(self, from_agent: str, context: dict):
        """
        Handle a collaboration request from another agent (e.g., frontend, architect, PM).
        TODO: Implement logic to process incoming requests and update shared context.
        """
        self.logger.info(f"[Collaboration] Received request from {from_agent}: {context}")
        # TODO: Implement actual handling logic
        pass 

# Backward-compatible tool export for legacy workflows expecting `developer_tool`
# Mirrors the pattern used in `crewai_app/agents/tester.py`
try:
    developer_openai = OpenAIService(deployment=settings.deployment_developer)
    developer_tool = CodeGeneratorTool(developer_openai)
except Exception as e:
    # Ensure module import doesn't fail in constrained environments
    developer_tool = CodeGeneratorTool(OpenAIService(deployment=getattr(settings, 'deployment_developer', None))) 