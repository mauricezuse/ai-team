import logging
from typing import Any, Dict, Optional, List
from crewai_app.utils.logger import logger, file_handler, console_handler
from crewai_app.services.conversation_service import ConversationService

class BaseAgent:
    """
    Base class for LLM-driven agents (backend, frontend, etc).
    Provides common logic for LLM interaction, output parsing, error handling, collaboration, and context management.
    """
    BASE_PROMPT = (
        "Output ONLY a valid Python list of dicts, each with 'file' and 'code' keys, one per file. "
        "Do NOT output explanations, requirements, or summaries. Do NOT output code fences. "
        "If you cannot generate valid code, return an empty list [].\n"
        "Output format example:\n"
        "[\n  {\"file\": \"frontend/projects/freelancer/profile/src/app/example.component.ts\", \"code\": \"import { Component } from '@angular/core';\\n@Component({\\n  selector: 'app-example',\\n  templateUrl: './example.component.html',\\n  styleUrls: ['./example.component.scss']\\n})\\nexport class ExampleComponent { }\"},\n  {\"file\": \"frontend/projects/freelancer/profile/src/app/example.component.html\", \"code\": \"<div>Example works!</div>\"}\n]\n"
    )

    def __init__(self, llm_service, name: str, role: str, goal: str, backstory: str, tools: Optional[list] = None, 
                 workflow_id: Optional[int] = None, step_name: Optional[str] = None):
        self.llm_service = llm_service
        self.name = name
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.tools = tools or []
        self.workflow_id = workflow_id
        self.step_name = step_name or "default"
        self.logger = logging.getLogger(f"ai_team.{self.name}")
        self.shared_context: Dict[str, Any] = {}  # For agent collaboration
        self.llm_cache: Dict[str, Any] = {}
        self.last_llm_output = None
        self.escalation_history: List[Dict[str, Any]] = []  # Track escalations
        self.collaboration_requests: List[Dict[str, Any]] = []  # Track collaboration
        
        # Initialize conversation service for persistence
        self.conversation_service = None
        if workflow_id:
            self.conversation_service = ConversationService(workflow_id, self.name, self.step_name)
        
        # Ensure agent logger has handlers
        if not self.logger.hasHandlers():
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
        self.logger.setLevel(logger.level)
        self.logger.propagate = True

    def _run_llm(self, prompt: str, step: Optional[str] = None, max_retries: int = 2, max_tokens: int = 1024, **kwargs) -> str:
        """
        Run the LLM with retries, caching, logging, and conversation persistence.
        """
        cache_key = (prompt, step, max_tokens)
        if cache_key in self.llm_cache:
            return self.llm_cache[cache_key]
        
        # Persist user message if conversation service available
        if self.conversation_service:
            self.conversation_service.append_message(
                role="user",
                content=prompt,
                metadata={"step": step, "agent": self.name, "max_tokens": max_tokens}
            )
        
        for attempt in range(1, max_retries + 2):
            try:
                result = self.llm_service.generate(prompt, step=step, max_tokens=max_tokens, **kwargs)
                self.logger.info(f"[LLM Output] ({step or 'default'}, attempt {attempt}): {result}")
                
                # Persist assistant response if conversation service available
                if self.conversation_service:
                    self.conversation_service.append_message(
                        role="assistant",
                        content=result,
                        metadata={"step": step, "agent": self.name, "attempt": attempt}
                    )
                
                self.llm_cache[cache_key] = result
                return result
            except Exception as e:
                self.logger.error(f"[LLM Error] ({step or 'default'}, attempt {attempt}): {e}")
                
                # Persist error message if conversation service available
                if self.conversation_service:
                    self.conversation_service.append_message(
                        role="system",
                        content=f"LLM Error (attempt {attempt}): {str(e)}",
                        metadata={"step": step, "agent": self.name, "error": True, "attempt": attempt}
                    )
        
        # Final error - persist terminal message
        if self.conversation_service:
            self.conversation_service.append_message(
                role="system",
                content=f"LLM failed after {max_retries+1} attempts for step {step or 'default'}",
                metadata={"step": step, "agent": self.name, "terminal": True, "max_attempts": max_retries+1}
            )
        
        raise RuntimeError(f"LLM failed after {max_retries+1} attempts for step {step or 'default'}.")

    def parse_output(self, output: str, parse_type: str = "json") -> Any:
        """
        Parse LLM output (e.g., JSON, Python list/dict, code block). Extend as needed.
        """
        # TODO: Implement robust parsing for different output types
        import json, ast, re
        cleaned = output.strip()
        if parse_type == "json":
            try:
                return json.loads(cleaned)
            except Exception:
                pass
        if parse_type == "python":
            try:
                return ast.literal_eval(cleaned)
            except Exception:
                pass
        if parse_type == "list":
            match = re.search(r'(\[.*?\])', cleaned, re.DOTALL)
            if match:
                try:
                    return ast.literal_eval(match.group(1))
                except Exception:
                    pass
        # Fallback: return raw output
        return cleaned

    def escalate(self, reason: str, to_agent: str, context: Optional[dict] = None, priority: str = "normal") -> Dict[str, Any]:
        """
        Escalate or handoff a task to another agent (frontend, backend, architect, PM).
        Returns escalation details for workflow handling.
        """
        escalation = {
            "from_agent": self.name,
            "to_agent": to_agent,
            "reason": reason,
            "context": context or {},
            "priority": priority,
            "timestamp": logging.Formatter().formatTime(logging.LogRecord("", 0, "", 0, "", (), None)),
            "status": "pending"
        }
        
        self.escalation_history.append(escalation)
        self.logger.info(f"[Escalation] Escalating to {to_agent}: {reason}")
        self.logger.info(f"[Escalation] Context: {context}")
        
        # Persist escalation message if conversation service available
        if self.conversation_service:
            self.conversation_service.append_message(
                role="system",
                content=f"ESCALATION: {reason}",
                artifacts=[{
                    "type": "escalation",
                    "id": f"escalation_{len(self.escalation_history)}",
                    "uri": f"escalation://{self.name}->{to_agent}",
                    "metadata": escalation
                }],
                metadata={
                    "escalation": True,
                    "to_agent": to_agent,
                    "priority": priority,
                    "context": context
                }
            )
        
        return escalation

    def request_collaboration(self, target_agent: str, request_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request collaboration with another agent (e.g., API contract, UI spec).
        Returns collaboration request details.
        """
        collaboration = {
            "from_agent": self.name,
            "to_agent": target_agent,
            "request_type": request_type,
            "data": data,
            "timestamp": logging.Formatter().formatTime(logging.LogRecord("", 0, "", 0, "", (), None)),
            "status": "pending"
        }
        
        self.collaboration_requests.append(collaboration)
        self.logger.info(f"[Collaboration] Requesting {request_type} from {target_agent}")
        self.logger.info(f"[Collaboration] Data: {data}")
        
        # Persist collaboration message if conversation service available
        if self.conversation_service:
            self.conversation_service.append_message(
                role="system",
                content=f"COLLABORATION REQUEST: {request_type}",
                artifacts=[{
                    "type": "collaboration",
                    "id": f"collab_{len(self.collaboration_requests)}",
                    "uri": f"collaboration://{self.name}->{target_agent}",
                    "metadata": collaboration
                }],
                metadata={
                    "collaboration": True,
                    "to_agent": target_agent,
                    "request_type": request_type,
                    "data": data
                }
            )
        
        return collaboration

    def update_shared_context(self, key: str, value: Any):
        """
        Update the shared context for agent collaboration.
        """
        self.shared_context[key] = value
        self.logger.info(f"[Context] Updated shared context: {key} = {value}")

    def get_shared_context(self, key: str) -> Any:
        """
        Retrieve a value from the shared context.
        """
        return self.shared_context.get(key)

    def get_escalation_history(self) -> List[Dict[str, Any]]:
        """
        Get the history of escalations made by this agent.
        """
        return self.escalation_history

    def get_collaboration_requests(self) -> List[Dict[str, Any]]:
        """
        Get the history of collaboration requests made by this agent.
        """
        return self.collaboration_requests

    def clear_escalation_history(self):
        """
        Clear the escalation history (useful for testing).
        """
        self.escalation_history.clear()

    def clear_collaboration_requests(self):
        """
        Clear the collaboration requests (useful for testing).
        """
        self.collaboration_requests.clear()

    def needs_escalation(self, task: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        Determine if a task needs escalation based on complexity, requirements, or domain.
        Override in subclasses for specific logic.
        """
        # Default escalation triggers
        escalation_triggers = [
            "unclear_requirements" in task.get("flags", []),
            "cross_domain" in task.get("flags", []),
            "complex_architecture" in task.get("flags", []),
            task.get("complexity", 0) > 8,  # High complexity tasks
            "api_contract_needed" in context,
            "ui_spec_needed" in context
        ]
        
        return any(escalation_triggers)

    def should_collaborate(self, task: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        Determine if a task requires collaboration with other agents.
        Override in subclasses for specific logic.
        """
        # Default collaboration triggers
        collaboration_triggers = [
            "backend_api_needed" in task.get("dependencies", []),
            "frontend_ui_needed" in task.get("dependencies", []),
            "shared_component" in task.get("flags", []),
            "data_model_change" in task.get("flags", [])
        ]
        
        return any(collaboration_triggers)

    def generate_code_with_fallback(self, task, plan, rules, codebase_index, 
                                    build_multifile_prompt, build_file_list_prompt, build_single_file_prompt, 
                                    strip_code_fences, output_validator, step_prefix="agent"):
        """
        Two-phase code generation: (1) try multi-file, (2) if that fails, get file list and generate per-file.
        - build_multifile_prompt: function to build the multi-file prompt
        - build_file_list_prompt: function to build the file-list prompt
        - build_single_file_prompt: function to build the single-file prompt
        - strip_code_fences: function to clean LLM output
        - output_validator: function to validate and parse the output (should return list of dicts or None)
        - step_prefix: string for logging/LLM step
        Returns: list of code file dicts [{"file": ..., "code": ...}, ...]
        """
        import logging
        
        def is_output_complete(output_str):
            """Check if the output seems complete (not truncated)"""
            if not output_str or len(output_str.strip()) < 10:
                return False
                
            # Check for common incomplete patterns
            incomplete_patterns = [
                'return PaginatedResponse[',
                'def ',
                'class ',
                'import ',
                'from ',
                'if __name__ == "__main__":',
                'export class',
                '@Component(',
                '@Injectable(',
                '@NgModule('
            ]
            
            # If output ends with an incomplete pattern, it's likely truncated
            for pattern in incomplete_patterns:
                if output_str.rstrip().endswith(pattern):
                    return False
                    
            # Check for balanced braces/brackets
            open_braces = output_str.count('{') + output_str.count('[') + output_str.count('(')
            close_braces = output_str.count('}') + output_str.count(']') + output_str.count(')')
            
            if abs(open_braces - close_braces) > 2:  # Allow some imbalance for comments
                return False
                
            return True
        
        def get_llm_response_with_retry(prompt, step, max_tokens=1024, max_retries=3):
            """Get LLM response with retry logic for truncated outputs"""
            for attempt in range(max_retries):
                try:
                    # Reduce max_tokens on retries to avoid truncation
                    current_max_tokens = max_tokens // (2 ** attempt) if attempt > 0 else max_tokens
                    
                    result = self._run_llm(prompt, step=step, max_tokens=current_max_tokens)
                    
                    # Check if output seems complete
                    if is_output_complete(result):
                        return result
                    else:
                        self.logger.warning(f"[{self.name}] Output seems truncated (attempt {attempt + 1}), retrying with smaller max_tokens")
                        
                except Exception as e:
                    self.logger.error(f"[{self.name}] LLM call failed (attempt {attempt + 1}): {e}")
                    if attempt == max_retries - 1:
                        raise
                        
            return ""
        
        # 1. Try multi-file output
        prompt = build_multifile_prompt(task, plan, rules, codebase_index)
        self.logger.info(f"[{self.name}] Multi-file LLM prompt: {prompt}")
        
        result_str = get_llm_response_with_retry(prompt, step=f"{step_prefix}.implement")
        self.last_llm_output = result_str
        self.logger.info(f"[{self.name}] Multi-file LLM output: {result_str}")
        
        try:
            cleaned_result_str = strip_code_fences(result_str)
            code_files = output_validator(cleaned_result_str)
            if code_files:
                return code_files
        except Exception as e:
            self.logger.warning(f"[{self.name}] Multi-file output parse error: {e}\nPrompt: {prompt}\nOutput: {result_str}")
        
        # 2. Fallback: Two-phase approach
        self.logger.info(f"[{self.name}] Falling back to two-phase approach.")
        file_list_prompt = build_file_list_prompt(task, plan, rules, codebase_index)
        self.logger.info(f"[{self.name}] File list LLM prompt: {file_list_prompt}")
        
        file_list_str = get_llm_response_with_retry(file_list_prompt, step=f"{step_prefix}.file_list", max_tokens=512)
        self.last_llm_output = file_list_str
        self.logger.info(f"[{self.name}] File list LLM output: {file_list_str}")
        
        try:
            cleaned_file_list_str = strip_code_fences(file_list_str)
            import ast
            file_list = ast.literal_eval(cleaned_file_list_str)
            if not isinstance(file_list, list):
                raise ValueError
        except Exception as e:
            self.logger.error(f"[{self.name}] Error parsing file list: {e}\nPrompt: {file_list_prompt}\nOutput: {file_list_str}")
            raise ValueError("LLM did not return a valid file list for two-phase approach.")
        
        code_files = []
        for file_path in file_list:
            single_file_prompt = build_single_file_prompt(task, plan, rules, codebase_index, file_path)
            self.logger.info(f"[{self.name}] Single-file LLM prompt for {file_path}: {single_file_prompt}")
            
            # Use smaller max_tokens for single file to avoid truncation
            file_code_str = get_llm_response_with_retry(single_file_prompt, step=f"{step_prefix}.single_file", max_tokens=4048)
            self.last_llm_output = file_code_str
            self.logger.info(f"[{self.name}] Single-file LLM output for {file_path}: {file_code_str}")
            
            try:
                cleaned_file_code_str = strip_code_fences(file_code_str)
                file_result = output_validator(cleaned_file_code_str)
                if file_result:
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
                self.logger.warning(f"[{self.name}] Error parsing single-file output for {file_path}: {e}\nPrompt: {single_file_prompt}\nOutput: {file_code_str}")
        
        if code_files:
            return code_files
        else:
            self.logger.error(
                f"[{self.name}] No valid code files generated for task: {task}\n"
                f"Plan: {plan}\nRules: {rules}\n"
                f"Last prompt: {prompt if prompt is not None else '[Not set]'}\n"
                f"Last LLM output: {result_str if result_str is not None else '[Not set]'}"
            )
            raise ValueError("LLM did not return any valid code files for implement_task.\n"
                             f"Task: {task}\nPlan: {plan}\nPrompt: {prompt if prompt is not None else '[Not set]'}\nOutput: {result_str if result_str is not None else '[Not set]'}")

    # TODO: Add more utilities for error handling, logging, and agent collaboration as needed. 