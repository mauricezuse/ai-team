from crewai_app.agents.base import BaseAgent
from crewai_app.services.openai_service import OpenAIService
from crewai_app.config import settings
import os

class FrontendAgent(BaseAgent):
    """
    Agent for Angular (Native Federation) frontend development.
    Inherits LLM interaction, output parsing, error handling, collaboration, and context management from BaseAgent.
    Implements frontend-specific prompt engineering, UI consistency rules, and collaboration/escalation logic.
    """
    BASE_PROMPT = (
        "You are an expert Angular developer specializing in Angular Native Federation micro-frontend architecture. "
        "This project uses Angular Native Federation with the following structure:\n"
        "- Shell application: negishi-freelancing/frontend/projects/shell (main host application)\n"
        "- Federated modules: negishi-freelancing/frontend/projects/freelancer/profile (remote module)\n"
        "- The profile module contains both client and freelancer components\n"
        "- Components are exposed via federation.config.js for remote loading\n"
        "\n"
        "IMPORTANT FEDERATION CONSIDERATIONS:\n"
        "- When creating components, consider if they should be exposed in federation.config.js\n"
        "- Use proper module boundaries and avoid tight coupling between shell and remotes\n"
        "- Shared dependencies are configured in federation.config.js\n"
        "- Components should be self-contained and follow micro-frontend best practices\n"
        "\n"
        "Create production-ready, well-structured Angular code with proper TypeScript typing, error handling, and responsive design. "
        "Include all necessary files: .ts, .html, .scss, and .spec.ts files. "
        "Always include or update tests: unit tests, integration tests, and Playwright end-to-end tests where applicable. "
        "Use modern Angular practices including OnPush change detection, proper dependency injection, and reactive forms where appropriate. "
        "Do NOT output anything else."
    )

    def __init__(self, llm_service, *args, **kwargs):
        super().__init__(
            llm_service=llm_service,
            name="frontend",
            role="Frontend Developer",
            goal="Implement Angular (Native Federation) UI and tests with strict design consistency.",
            backstory="A frontend expert who ensures all UI is beautiful, consistent, and production-ready.",
            tools=[],
        )
        self.logger.info(f"[FrontendAgent.__init__] Instantiated with llm_service={type(llm_service)} deployment={getattr(llm_service, 'deployment', None)}")

    def _run_llm(self, prompt: str, step: str, workflow_id=None, conversation_id=None, **kwargs):
        """Run LLM with tracking for frontend agent. Uses parent class method for ConversationService integration."""
        # Use parent class method which includes ConversationService integration
        return super()._run_llm(prompt, step=step, **kwargs)

    def escalate_to_backend(self, reason: str, context: dict = None):
        """
        Escalate a task to the backend agent for API or integration support.
        Example usage: self.escalate_to_backend('Need new API endpoint for filter', context)
        """
        self.escalate(reason, to_agent="backend", context=context)

    def escalate_to_architect_or_pm(self, reason: str, context: dict = None):
        """
        Escalate a task to the architect or PM agent for requirements or design clarification.
        Example usage: self.escalate_to_architect_or_pm('Unclear requirements for UI component', context)
        """
        self.escalate(reason, to_agent="architect/pm", context=context)

    def handle_collaboration_request(self, from_agent: str, context: dict):
        """
        Handle a collaboration request from another agent (e.g., backend, architect, PM).
        TODO: Implement logic to process incoming requests and update shared context.
        """
        self.logger.info(f"[Collaboration] Received request from {from_agent}: {context}")
        # TODO: Implement actual handling logic
        pass

    def break_down_story(self, story, plan, rules, api_contracts=None, max_retries=2):
        """
        Use the LLM to break down a frontend story into up to 3 actionable UI development tasks/subtasks with clear titles and acceptance criteria.
        Returns a list of dicts: [{"title": ..., "description": ..., "acceptance_criteria": ...}, ...]
        Robust to LLM output errors: requires valid JSON, retries with fallback prompt if needed.
        """
        import re, json, logging
        print(f"[FrontendAgent.break_down_story] ENTERED with story={story!r}, plan={plan!r}, rules={rules!r}, api_contracts={api_contracts!r}")
        self.logger.info(f"[break_down_story] ENTERED with story={story!r}, plan={plan!r}, rules={rules!r}, api_contracts={api_contracts!r}")
        if not story or not plan:
            print(f"[FrontendAgent.break_down_story] SKIPPING: story or plan is None/empty. story={story!r}, plan={plan!r}")
            self.logger.warning(f"[break_down_story] SKIPPING: story or plan is None/empty. story={story!r}, plan={plan!r}")
            return []
        contract_section = f"API/Data Contracts: {api_contracts}\n" if api_contracts else ""
        base_prompt = (
            contract_section +
            f"Break down the following frontend story into up to 3 actionable UI development tasks. For each task, provide a title, a short description, and acceptance criteria.\n"
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
                result_str = self._run_llm(prompt, step="frontend.break_down_story")
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

    def implement_task(self, task, plan, rules, codebase_index, checkpoint=None, save_checkpoint=None, branch=None, repo_root=None, api_contracts=None):
        import re, ast, logging
        print(f"[FrontendAgent] implement_task called. llm_service={self.llm_service} deployment={getattr(self.llm_service, 'deployment', None)}")
        logging.info(f"[FrontendAgent] implement_task called. llm_service={self.llm_service} deployment={getattr(self.llm_service, 'deployment', None)}")
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
                "List all files that need to be created or modified to implement the following Angular frontend task. Output ONLY a valid Python list of file paths, with NO extra commentary, explanations, or text. Do NOT include any text before or after the list. Repeat: Output ONLY a valid Python list, e.g. ['file1.ts', 'file2.html'].\n"
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
            
            # Analyze Angular file structure and patterns
            file_analysis = ""
            if current_content:
                lines = current_content.split('\n')
                imports = [line.strip() for line in lines if line.strip().startswith(('import ', 'from '))]
                decorators = [line.strip() for line in lines if line.strip().startswith('@')]
                classes = [line.strip() for line in lines if line.strip().startswith('export class ')]
                interfaces = [line.strip() for line in lines if line.strip().startswith('export interface ')]
                
                file_analysis = f"""
CURRENT ANGULAR FILE ANALYSIS:
- Total lines: {len(lines)}
- Imports: {len(imports)} found
- Decorators: {len(decorators)} found
- Classes: {len(classes)} found
- Interfaces: {len(interfaces)} found
- File exists: YES

CURRENT IMPORTS:
{chr(10).join(imports[:10])}

CURRENT DECORATORS:
{chr(10).join(decorators[:5])}

CURRENT CLASSES:
{chr(10).join(classes[:5])}

CURRENT INTERFACES:
{chr(10).join(interfaces[:5])}
"""
            else:
                file_analysis = """
CURRENT ANGULAR FILE ANALYSIS:
- File does not exist yet
- Will create new Angular file with proper structure
"""
            
            # Get related Angular files context
            related_files = []
            file_dir = os.path.dirname(file_path) if file_path else ""
            file_name = os.path.basename(file_path) if file_path else ""
            
            # Find related Angular files in the same directory and parent directories
            for indexed_file in codebase_index.keys():
                if os.path.dirname(indexed_file) == file_dir and indexed_file != file_path:
                    related_files.append(indexed_file)
                elif file_dir and indexed_file.startswith(file_dir + '/') and indexed_file != file_path:
                    related_files.append(indexed_file)
            
            # Get Angular project structure context
            angular_structure = []
            for indexed_file in list(codebase_index.keys())[:20]:  # Limit to first 20 files
                if indexed_file.startswith('frontend/') and any(ext in indexed_file for ext in ['.ts', '.html', '.scss', '.spec.ts']):
                    angular_structure.append(indexed_file)
            
            # Get Angular-specific context
            angular_context = ""
            if current_content:
                # Look for Angular-specific patterns
                has_component_decorator = '@Component(' in current_content
                has_module_decorator = '@NgModule(' in current_content
                has_service_decorator = '@Injectable(' in current_content
                
                angular_context = f"""
ANGULAR CONTEXT:
- Has @Component decorator: {has_component_decorator}
- Has @NgModule decorator: {has_module_decorator}
- Has @Injectable decorator: {has_service_decorator}
"""
            
            # Add federation context
            federation_context = ""
            if file_path and 'profile' in file_path:
                federation_context = """
FEDERATION CONTEXT:
- This is a federated module (profile)
- Components should be exposed in federation.config.js if they need to be loaded remotely
- Use proper module boundaries and avoid tight coupling with shell
- Consider if this component should be exposed for remote loading
"""
            elif file_path and 'shell' in file_path:
                federation_context = """
FEDERATION CONTEXT:
- This is the shell application (host)
- Components here can load remote modules from federated applications
- Use loadRemoteModule() for loading remote components
- Avoid tight coupling with remote modules
"""
            
            return (
                contract_section +
                self.BASE_PROMPT +
                f"Implement ONLY the code for the file: {file_path}.\n"
                "CRITICAL: If the file already exists, analyze the current Angular structure and make intelligent, surgical modifications.\n"
                "DO NOT replace the entire file unless absolutely necessary.\n"
                "Preserve existing imports, decorators, classes, and structure unless they need modification for the task.\n"
                "Add new functionality by extending existing classes or adding new methods/properties.\n"
                "The code must be valid, complete, and ready to run.\n"
                "Do NOT output placeholder code, .txt files, or summaries.\n"
                "If you cannot generate valid code for this file, return an empty list [].\n"
                "ANGULAR MODIFICATION STRATEGY:\n"
                "1. If file exists: Analyze current Angular structure and make minimal changes\n"
                "2. If adding new functionality: Extend existing classes/methods\n"
                "3. If modifying existing code: Preserve decorators and add/update specific parts\n"
                "4. If file doesn't exist: Create new Angular file with proper structure\n"
                "5. For components: Preserve @Component decorator and extend existing class\n"
                "6. For modules: Preserve @NgModule decorator and add to existing declarations/imports\n"
                "7. For services: Preserve @Injectable decorator and extend existing service\n"
                "8. For federation: Consider if component should be exposed in federation.config.js\n"
                "Output format example:\n"
                "[\n  {\"file\": \"frontend/projects/freelancer/profile/src/app/component-name/component-name.component.ts\", \"code\": \"# Example Angular code\"}\n]\n"
                "Do NOT wrap your output in triple backticks or code fences.\n"
                f"Task: {task}\n"
                f"Implementation Plan: {plan}\n"
                f"Acceptance Criteria: {task.get('acceptance_criteria', '')}\n"
                f"Target File: {file_path}\n"
                f"{file_analysis}\n"
                f"Current File Content:\n{current_content}\n"
                f"{angular_context}"
                f"{federation_context}"
                f"Related Angular Files in Project: {related_files[:10]}\n"
                f"Angular Project Structure: {angular_structure[:10]}\n"
                f"Relevant Codebase Context: {codebase_index.get(file_path, {})}\n"
                f"Codebase Index Keys: {list(codebase_index.keys())[:20]}\n"
            )
        return self.generate_code_with_fallback(
            task, plan, rules, codebase_index,
            build_multifile_prompt, build_file_list_prompt, build_single_file_prompt,
            strip_code_fences, output_validator, step_prefix="frontend"
        )

# Instantiate a dedicated OpenAIService for the frontend agent
frontend_openai = OpenAIService(deployment=settings.deployment_frontend) 