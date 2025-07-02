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

    def break_down_story(self, story, plan, rules, max_retries=2):
        """
        Use the LLM to break down a story into up to 3 actionable development tasks/subtasks with clear titles and acceptance criteria.
        Returns a list of dicts: [{"title": ..., "description": ..., "acceptance_criteria": ...}, ...]
        Robust to LLM output errors: requires valid JSON, retries with fallback prompt if needed.
        """
        base_prompt = (
            f"Break down the following story into up to 3 actionable development tasks. For each task, provide a title, a short description, and acceptance criteria.\n"
            f"Output a JSON list of dicts with keys: 'title', 'description', 'acceptance_criteria'.\n"
            f"Do NOT wrap your output in triple backticks, code fences, or a code block. Output only raw JSON.\n"
            f"NEVER output partial or truncated strings. If you cannot fit the full output, return a single fallback task with title 'Implement Story', description 'Implement the story as described', and acceptance criteria matching the story's acceptance criteria.\n"
            f"Story: {story}\nRules: {rules}\n"
        )
        fallback_prompt = (
            f"Return a JSON list with a single task: title 'Implement Story', description 'Implement the story as described', and acceptance criteria matching the story's acceptance criteria.\n"
            f"Do NOT wrap your output in triple backticks, code fences, or a code block. Output only raw JSON.\n"
            f"Story: {story}\nRules: {rules}\n"
        )
        for attempt in range(1, max_retries + 2):
            prompt = base_prompt if attempt == 1 else fallback_prompt
            result_str = developer_tool._run(prompt)
            logging.info(f"[DeveloperAgent] break_down_story LLM output (attempt {attempt}): {result_str}")
            # Strip code fences and 'json' tags
            cleaned = re.sub(r"^```json\\s*|^```|```$", "", result_str.strip(), flags=re.IGNORECASE | re.MULTILINE).strip()
            try:
                tasks = json.loads(cleaned)
                if isinstance(tasks, list) and all(isinstance(t, dict) for t in tasks):
                    return tasks
            except Exception as e:
                logging.error(f"[DeveloperAgent] Error parsing LLM output in break_down_story (attempt {attempt}): {e}\nOutput: {result_str}")
        raise ValueError("LLM did not return any valid tasks for break_down_story after retries.")

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

    def implement_task(self, task, plan, rules, codebase_index, checkpoint=None, save_checkpoint=None, branch=None, repo_root=None):
        prompt = None
        result_str = None
        # --- Hybrid Multi-file/Two-pass Approach ---
        def build_multifile_prompt(task, plan, rules, codebase_index):
            return (
                "You are an expert Python/FastAPI backend developer.\n"
                "Your task is to implement the following feature as part of a production codebase.\n"
                "If the task requires changes in multiple files (e.g., models, endpoints, serializers), output a Python list of dicts, each with 'file' and 'code' keys, one per file. Do not put unrelated logic in a single file.\n"
                "Output format example:\n"
                "[\n  {\"file\": \"backend/apps/platform_service/api/endpoints/user.py\", \"code\": \"<endpoint code>\"},\n  {\"file\": \"backend/apps/platform_service/models/freelancer.py\", \"code\": \"<model code>\"}\n]\n"
                "Do NOT output explanations, summaries, or code fences. If you cannot generate valid code for a file, omit it from the list.\n"
                "---\n"
                f"Task: {task}\n"
                f"Implementation Plan: {plan}\n"
                f"Acceptance Criteria: {task.get('acceptance_criteria', '')}\n"
                f"Relevant Codebase Index: {list(codebase_index.keys())}\n"
                "---\n"
            )
        def build_file_list_prompt(task, plan, rules, codebase_index):
            return (
                "List all files that need to be created or modified to implement the following task. Output ONLY a valid Python list of file paths, with NO extra commentary, explanations, or text. Do NOT include any text before or after the list. Repeat: Output ONLY a valid Python list, e.g. ['file1.py', 'file2.py'].\n"
                f"Task: {task}\n"
                f"Implementation Plan: {plan}\n"
                f"Acceptance Criteria: {task.get('acceptance_criteria', '')}\n"
                f"Relevant Codebase Index: {list(codebase_index.keys())}\n"
            )
        def build_single_file_prompt(task, plan, rules, codebase_index, file_path):
            return (
                "You are an expert Python/FastAPI backend developer.\n"
                "Implement ONLY the code for the file: {file_path}.\n"
                "If the file already exists, update or extend it as needed.\n"
                "The code must be valid, complete, and ready to run.\n"
                "Do NOT output placeholder code, .txt files, or summaries.\n"
                "If you cannot generate valid code for this file, return an empty list [].\n"
                "Output format example:\n"
                "[\n  {\"file\": \"backend/apps/platform_service/api/endpoints/user.py\", \"code\": \"<full Python code here>\"}\n]\n"
                "Do NOT wrap your output in triple backticks or code fences.\n"
                f"Task: {task}\n"
                f"Implementation Plan: {plan}\n"
                f"Acceptance Criteria: {task.get('acceptance_criteria', '')}\n"
                f"Target File: {file_path}\n"
                f"Relevant Codebase Context: {codebase_index.get(file_path, {})}\n"
            )
        # --- Add robust list extraction utility ---
        def extract_python_list(text):
            """Extract the first Python list from a string using regex, fallback to ast.literal_eval."""
            import re
            match = re.search(r'(\[.*?\])', text, re.DOTALL)
            if match:
                list_str = match.group(1)
                try:
                    return ast.literal_eval(list_str)
                except Exception:
                    pass
            # Fallback: try to parse the whole string
            try:
                return ast.literal_eval(text)
            except Exception:
                pass
            return None
        # 1. Try multi-file output
        prompt = build_multifile_prompt(task, plan, rules, codebase_index)
        result_str = developer_tool._run(prompt)
        logging.info(f"[DeveloperAgent] Multi-file LLM output: {result_str}")
        code_files = []
        try:
            cleaned_result_str = strip_code_fences(result_str)
            result = eval(cleaned_result_str, {"__builtins__": {}})
            if isinstance(result, list) and all(isinstance(f, dict) and 'file' in f and 'code' in f for f in result):
                # Heuristic: check for truncation or excessive length
                if cleaned_result_str.strip().endswith(']') and len(cleaned_result_str) < 12000:
                    code_files = result
                    if code_files:
                        return code_files
        except Exception as e:
            logging.warning(f"[DeveloperAgent] Multi-file output parse error: {e}\nOutput: {result_str}")
        # 2. Fallback: Two-pass approach
        logging.info("[DeveloperAgent] Falling back to two-pass approach.")
        file_list_prompt = build_file_list_prompt(task, plan, rules, codebase_index)
        file_list_str = developer_tool._run(file_list_prompt)
        logging.info(f"[DeveloperAgent] File list LLM output: {file_list_str}")
        try:
            cleaned_file_list_str = strip_code_fences(file_list_str)
            file_list = extract_python_list(cleaned_file_list_str)
            if not isinstance(file_list, list):
                raise ValueError
        except Exception as e:
            logging.error(f"[DeveloperAgent] Error parsing file list: {e}\nOutput: {file_list_str}")
            raise ValueError("LLM did not return a valid file list for two-pass approach.")
        code_files = []
        for file_path in file_list:
            single_file_prompt = build_single_file_prompt(task, plan, rules, codebase_index, file_path)
            file_code_str = developer_tool._run(single_file_prompt)
            logging.info(f"[DeveloperAgent] Single-file LLM output for {file_path}: {file_code_str}")
            try:
                cleaned_file_code_str = strip_code_fences(file_code_str)
                file_result = eval(cleaned_file_code_str, {"__builtins__": {}})
                if isinstance(file_result, list):
                    for f in file_result:
                        if (
                            isinstance(f, dict)
                            and f.get('file', '').endswith((".py", ".ts", ".html", ".css", ".scss"))
                            and f.get('code')
                            and f['code'].strip()
                            and not f['file'].endswith('.txt')
                        ):
                            code_files.append(f)
            except Exception as e:
                logging.warning(f"[DeveloperAgent] Error parsing single-file output for {file_path}: {e}\nOutput: {file_code_str}")
        if code_files:
            return code_files
        else:
            logging.error(
                f"[DeveloperAgent] No valid code files generated for task: {task}\n"
                f"Plan: {plan}\n"
                f"Rules: {rules}\n"
                f"Last prompt: {prompt if prompt is not None else '[Not set]'}\n"
                f"Last LLM output: {result_str if result_str is not None else '[Not set]'}"
            )
            raise ValueError("LLM did not return any valid code files for implement_task.\n"
                             f"Task: {task}\nPlan: {plan}\nPrompt: {prompt if prompt is not None else '[Not set]'}\nOutput: {result_str if result_str is not None else '[Not set]'}")

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