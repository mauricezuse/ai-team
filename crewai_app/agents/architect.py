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
import re
import string

CACHE_PATH = os.path.join(os.path.dirname(__file__), '../../workflow_results/llm_cache.json')
WORKFLOW_RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'workflow_results')
os.makedirs(WORKFLOW_RESULTS_DIR, exist_ok=True)

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
logger.info(f"[Architect] Available deployments: {architect_deployments}")
deployment_cycle = itertools.cycle(architect_deployments) if architect_deployments else None

def get_next_deployment():
    if deployment_cycle:
        # Log rate limit status for each deployment
        from crewai_app.services.openai_service import OpenAIService
        now = time.time()
        statuses = []
        for d in architect_deployments:
            until = OpenAIService._rate_limited_until.get(d, 0)
            status = f"{d}: {'available' if now >= until else f'rate-limited until {until-now:.1f}s'}"
            statuses.append(status)
        logger.info(f"[Architect] Deployment statuses: {statuses}")
        # Check if all are rate-limited
        all_limited = all(OpenAIService._rate_limited_until.get(d, 0) > now for d in architect_deployments)
        if all_limited:
            soonest = min(OpenAIService._rate_limited_until.get(d, 0) for d in architect_deployments)
            wait = max(soonest - now, 1)
            logger.warning(f"[Architect] All deployments rate-limited. Soonest available in {wait:.1f}s.")
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

def try_autocorrect_json(text):
    """Attempt to auto-correct common JSON issues: missing closing brace, trailing commas, etc. Now also strips control characters."""
    # Remove all non-printable/control characters
    printable = set(string.printable)
    text = ''.join(c for c in text if c in printable)
    
    # Remove trailing commas before closing braces/brackets
    text = re.sub(r',([ \r\n]*[}\]])', r'\1', text)
    
    # Add missing closing brace if likely truncated
    if text.count('{') > text.count('}'):
        text = text.rstrip() + '\n}'
    
    # Remove any text after the last closing brace
    last_brace = text.rfind('}')
    if last_brace != -1:
        text = text[:last_brace+1]
    
    # Fix common JSON issues
    text = re.sub(r'(["\w])\s*\n\s*(["\w])', r'\1,\n\2', text)  # Add missing commas
    text = re.sub(r',\s*([}\]])', r'\1', text)  # Remove trailing commas
    
    return text

def validate_and_fix_json(text, expected_type=list):
    """Validate JSON and attempt to fix common issues."""
    try:
        # First try to parse as-is
        parsed = json.loads(text)
        if isinstance(parsed, expected_type):
            return parsed
    except json.JSONDecodeError:
        pass
    
    # Try auto-correction
    corrected = try_autocorrect_json(text)
    try:
        parsed = json.loads(corrected)
        if isinstance(parsed, expected_type):
            return parsed
    except json.JSONDecodeError:
        pass
    
    # If still failing, try to extract JSON from text
    import re
    # Look for array-like patterns
    array_match = re.search(r'\[.*\]', text, re.DOTALL)
    if array_match:
        try:
            extracted = array_match.group()
            parsed = json.loads(extracted)
            if isinstance(parsed, expected_type):
                return parsed
        except:
            pass
    
    # Final fallback - create a basic structure
    if expected_type == list:
        return []
    elif expected_type == dict:
        return {}
    else:
        return None

def chunk_large_output(text, max_chunk_size=4000):
    """Split large text into manageable chunks."""
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    # Split by lines to preserve structure
    lines = text.split('\n')
    for line in lines:
        if len(current_chunk) + len(line) + 1 > max_chunk_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = line
        else:
            current_chunk += '\n' + line if current_chunk else line
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def write_debug_file(filename, content):
    path = os.path.join(WORKFLOW_RESULTS_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

class ArchitectAgent:
    def __init__(self, openai_service, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.llm_service = openai_service
        self.last_llm_output = None
        self.conversation_service = None  # Will be set by workflow

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

    def _run_llm(self, prompt: str, step: str, workflow_id=None, conversation_id=None, **kwargs):
        """Run LLM with tracking for architect agent. Includes ConversationService integration."""
        # Persist user message if conversation service available
        if self.conversation_service:
            self.conversation_service.append_message(
                role="user",
                content=prompt,
                metadata={"step": step, "agent": "architect", "max_tokens": kwargs.get('max_tokens', 1024)}
            )
        
        # Call LLM service
        result = self.llm_service.generate(prompt, step=step, **kwargs)
        
        # Persist assistant response if conversation service available
        if self.conversation_service:
            self.conversation_service.append_message(
                role="assistant",
                content=result,
                metadata={"step": step, "agent": "architect"}
            )
        
        return result

    def select_relevant_files(self, story, pm_suggestions, codebase_index, workflow_id=None, conversation_id=None):
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
        
        # Use _run_llm to ensure ConversationService integration
        try:
            result = self._run_llm(
                prompt, 
                step="select_relevant_files",
                workflow_id=workflow_id,
                conversation_id=conversation_id
            )
            self._cache_set(prompt_hash, result)
            return result
        except Exception as e:
            logger.warning(f"ArchitectAgent.select_relevant_files fallback: {e}")
            fallback = f"Files: {[f[:40] for f in file_paths]}"
            self._cache_set(prompt_hash, fallback)
            return fallback

    def generate_backend_plan(self, story, pm_suggestions, selected_index, workflow_id=None, conversation_id=None):
        import json
        description = story['fields'].get('description', '') if isinstance(story, dict) else str(story)
        summary = story['fields'].get('summary', '') if isinstance(story, dict) else ''
        pm_suggestions = str(pm_suggestions)[:250]
        file_names = list(selected_index.keys())[:5]
        
        # Shorter, more focused prompt
        prompt = (
            "Generate backend tasks for this story. Output ONLY a JSON array of objects with: title, description, acceptance_criteria, type='backend'.\n"
            f"Story: {summary[:200]}\n"
            f"Files: {file_names[:3]}\n"
            "Example: [{\"title\": \"Update endpoint\", \"description\": \"Add filtering\", \"acceptance_criteria\": [\"Endpoint accepts params\"], \"type\": \"backend\"}]"
        )
        
        # Use _run_llm to ensure ConversationService integration
        try:
            result = self._run_llm(
                prompt, 
                step="dev_agents.backend_plan", 
                max_tokens=1500,
                workflow_id=workflow_id,
                conversation_id=conversation_id
            )
            self.last_llm_output = result
            
            # Validate and fix JSON
            parsed = validate_and_fix_json(result, list)
            if parsed is None:
                logger.error("[ArchitectAgent] Failed to parse backend plan JSON")
                return []
            
            # Post-process: if result is a list of strings, convert to list of objects
            if isinstance(parsed, list) and all(isinstance(t, str) for t in parsed):
                logger.warning("[ArchitectAgent] LLM returned a list of strings for backend plan; converting to objects.")
                parsed = [{
                    "title": t,
                    "description": t,
                    "acceptance_criteria": [t],
                    "type": "backend"
                } for t in parsed]
            
            logger.info(f"[ArchitectAgent] Final backend plan: {parsed}")
            return parsed
            
        except Exception as e:
            logger.error(f"[ArchitectAgent] Error generating backend plan: {e}")
            return []

    def generate_frontend_plan(self, story, pm_suggestions, selected_index, workflow_id=None, conversation_id=None):
        import json
        
        description = story['fields'].get('description', '') if isinstance(story, dict) else str(story)
        summary = story['fields'].get('summary', '') if isinstance(story, dict) else ''
        pm_suggestions = str(pm_suggestions)[:250]
        file_names = list(selected_index.keys())[:5]
        
        # Shorter, more focused prompt with federation context
        prompt = (
            "Generate frontend tasks for Angular Native Federation. Output ONLY a JSON array of objects with: title, description, acceptance_criteria, type='frontend'.\n"
            "Federation: Shell app loads remote components from federated modules via federation.config.js\n"
            f"Story: {summary[:200]}\n"
            f"Files: {file_names[:3]}\n"
            "Example: [{\"title\": \"Create component\", \"description\": \"Add to federated module\", \"acceptance_criteria\": [\"Component works\"], \"type\": \"frontend\"}]"
        )
        
        try:
            # Use _run_llm to ensure ConversationService integration
            llm_output = self._run_llm(
                prompt, 
                step="dev_agents.frontend_plan", 
                max_tokens=1500,
                workflow_id=workflow_id,
                conversation_id=conversation_id
            )
            self.last_llm_output = llm_output
            
            # Validate and fix JSON
            parsed = validate_and_fix_json(llm_output, list)
            if parsed is None:
                logger.error("[ArchitectAgent] Failed to parse frontend plan JSON")
                return []
            
            # Validate each item has required fields
            validated_tasks = []
            for task in parsed:
                if isinstance(task, dict):
                    # Ensure all required fields are present
                    task_obj = {
                        'title': task.get('title', 'Frontend Task'),
                        'description': task.get('description', 'Implement frontend functionality'),
                        'acceptance_criteria': task.get('acceptance_criteria', ['Task completed']),
                        'type': 'frontend'
                    }
                    validated_tasks.append(task_obj)
                else:
                    # Convert string to task object
                    task_obj = {
                        'title': str(task),
                        'description': f'Implement {str(task)}',
                        'acceptance_criteria': [f'{str(task)} is implemented'],
                        'type': 'frontend'
                    }
                    validated_tasks.append(task_obj)
            
            logger.info(f"[ArchitectAgent] Final frontend plan: {validated_tasks}")
            return validated_tasks
            
        except Exception as e:
            logger.error(f"[ArchitectAgent] Error generating frontend plan: {e}")
            # Return fallback task
            fallback_task = {
                'title': 'Implement Frontend Features',
                'description': 'Implement frontend features as described in the story',
                'acceptance_criteria': ['Frontend features are implemented'],
                'type': 'frontend'
            }
            return [fallback_task]

    def generate_api_contracts(self, story, pm_suggestions, selected_index, workflow_id=None, conversation_id=None):
        import json
        
        description = story['fields'].get('description', '') if isinstance(story, dict) else str(story)
        summary = story['fields'].get('summary', '') if isinstance(story, dict) else ''
        pm_suggestions = str(pm_suggestions)[:250]
        file_names = list(selected_index.keys())[:5]

        # --- NEW: Extract available schemas/models from codebase index ---
        # Look for files that likely define models/schemas (Python: models.py, schemas.py, TypeScript: *.model.ts, *.schema.ts, etc.)
        schema_files = [f for f in selected_index.keys() if any(s in f.lower() for s in ['model', 'schema'])]
        schema_names = set()
        for f in schema_files:
            # Try to extract class/interface names from the index summary if available
            summary = selected_index.get(f, '')
            # Look for class, interface, or type definitions
            import re
            found = re.findall(r'(class|interface|type)\s+(\w+)', summary)
            for _, name in found:
                schema_names.add(f"{name} ({f})")
        if not schema_names:
            # Fallback: just list the filenames
            schema_names = set(schema_files)
        schemas_section = "\nAvailable Schemas/Models in the codebase:\n" + ("\n".join(sorted(schema_names)) if schema_names else "None found")

        # --- END NEW ---

        # Shorter, more focused prompt
        prompt = (
            "Generate API contracts. Output ONLY a JSON object with endpoints and models.\n"
            f"Story: {summary[:200]}\n"
            f"Files: {file_names[:3]}\n"
            f"{schemas_section}\n"
            "If a schema/model exists above, reference it by name (and file path if needed) instead of redefining it. Only define new schemas if not found above.\n"
            "Example: {\"endpoints\": {\"GET /api\": {\"description\": \"List items\", \"response\": {\"items\": \"Item (models/item.py)\"}}}, \"models\": {}}\n"
        )
        
        try:
            # Use _run_llm to ensure ConversationService integration
            llm_output = self._run_llm(
                prompt, 
                step="dev_agents.api_contracts", 
                max_tokens=1500,
                workflow_id=workflow_id,
                conversation_id=conversation_id
            )
            self.last_llm_output = llm_output
            
            # Validate and fix JSON
            parsed = validate_and_fix_json(llm_output, dict)
            if parsed is None:
                logger.error("[ArchitectAgent] Failed to parse API contracts JSON")
                return {}
            
            logger.info(f"[ArchitectAgent] Final API contracts: {parsed}")
            return parsed
                
        except Exception as e:
            logger.error(f"[ArchitectAgent] Failed to generate API/data contracts: {e}")
            return {
                "endpoints": {
                    "GET /freelancers": {
                        "description": "List freelancers with filtering",
                        "query_params": {"skills": "string", "rate_min": "number"},
                        "response": {"freelancers": "array", "total": "number"}
                    }
                },
                "models": {
                    "Freelancer": {
                        "id": "string",
                        "name": "string",
                        "skills": "array"
                    }
                }
            }

    def review_and_plan(self, story, pm_suggestions, selected_index, workflow_id=None, conversation_id=None):
        """
        Generate a machine-parseable implementation plan for dev agents in three LLM calls: backend, frontend, and API/data contracts.
        """
        import json
        prompt_hash = self._prompt_hash(str(story) + str(pm_suggestions) + str(selected_index))
        cached = self._cache_get(prompt_hash)
        if cached:
            return cached, {}
        
        time.sleep(10)  # Throttle architect LLM calls
        plan = {}
        
        # Backend
        try:
            backend_result = self.generate_backend_plan(story, pm_suggestions, selected_index, workflow_id, conversation_id)
            plan['Backend Implementation Plan'] = backend_result
        except Exception as e:
            logger.error(f"[ArchitectAgent] Failed to generate backend plan: {e}")
            plan['Backend Implementation Plan'] = []
        
        # Frontend
        try:
            frontend_result = self.generate_frontend_plan(story, pm_suggestions, selected_index, workflow_id, conversation_id)
            plan['Frontend Implementation Plan'] = frontend_result
        except Exception as e:
            logger.error(f"[ArchitectAgent] Failed to generate frontend plan: {e}")
            plan['Frontend Implementation Plan'] = []
        
        # API/Data Contracts
        try:
            api_result = self.generate_api_contracts(story, pm_suggestions, selected_index, workflow_id, conversation_id)
            plan['API/Data Contracts'] = api_result
        except Exception as e:
            logger.error(f"[ArchitectAgent] Failed to generate API/data contracts: {e}")
            plan['API/Data Contracts'] = {}
        
        logger.info(f"[ArchitectAgent] Final dev-agent plan dict: {plan}")
        self._cache_set(prompt_hash, json.dumps(plan))
        return json.dumps(plan), {}

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

    def generate_plan_for_user_acceptance(self, story, pm_suggestions, selected_index, workflow_id=None, conversation_id=None):
        """
        Generate a user-facing implementation plan for user acceptance using BASE_PROMPT_FOR_USER_ACCEPTANCE.
        """
        from crewai_app.agents.architect import BASE_PROMPT_FOR_USER_ACCEPTANCE
        description = story['fields'].get('description', '') if isinstance(story, dict) else str(story)
        summary = story['fields'].get('summary', '') if isinstance(story, dict) else ''
        pm_suggestions = str(pm_suggestions)[:250]
        file_names = list(selected_index.keys())[:5]
        
        # Shorter prompt to prevent truncation
        prompt = (
            BASE_PROMPT_FOR_USER_ACCEPTANCE +
            f"\nStory: {str(summary)[:300]}\nDescription: {str(description)[:300]}\nPM Suggestions: {str(pm_suggestions)[:200]}\nSelected Files: {file_names[:3]}"
        )
        
        write_debug_file('architect_user_prompt.txt', prompt)
        
        try:
            # Use _run_llm to ensure ConversationService integration
            result = self._run_llm(
                prompt, 
                step="user_acceptance", 
                max_tokens=2000,
                workflow_id=workflow_id,
                conversation_id=conversation_id
            )
            write_debug_file('architect_user_llm_output.txt', result)
            self.last_llm_output = result
            
            # Validate JSON output
            try:
                json.loads(result)
                return result
            except json.JSONDecodeError:
                # Try to fix the JSON
                corrected = try_autocorrect_json(result)
                try:
                    json.loads(corrected)
                    return corrected
                except:
                    # Return a basic structure if all else fails
                    return '{"API/Data Contracts": {}, "Backend Implementation Plan": [], "Frontend Implementation Plan": []}'
                    
        except Exception as e:
            logger.error(f"[ArchitectAgent] Error generating user plan: {e}")
            return '{"API/Data Contracts": {}, "Backend Implementation Plan": [], "Frontend Implementation Plan": []}'

BASE_PROMPT_FOR_USER_ACCEPTANCE = (
    "You are a senior software architect. Given a user story and PM suggestions, produce an implementation plan.\n"
    "Output ONLY a valid JSON object with keys: 'API/Data Contracts', 'Backend Implementation Plan', 'Frontend Implementation Plan'.\n"
    "Each section should contain concrete tasks. If not needed, use empty arrays.\n"
    "IMPORTANT: Output ONLY the JSON object, NO extra text.\n"
    "Example: {\"API/Data Contracts\": {}, \"Backend Implementation Plan\": [], \"Frontend Implementation Plan\": []}\n"
)

BASE_PROMPT = (
    "You are an expert software architect.\n"
    "Your job is to break down user stories into actionable implementation plans for backend and frontend agents, and to define API/data contracts.\n"
    "Output a single valid JSON object with the following keys: 'Backend Implementation Plan', 'Frontend Implementation Plan', 'API/Data Contracts', 'Acceptance Criteria'.\n"
    "Each value must be a string or array with clear, actionable requirements for the respective agent.\n"
    "IMPORTANT: Output ONLY the JSON object, with NO extra commentary, explanations, markdown, or text before or after.\n"
    "Do NOT include any control characters, newlines inside string values, or invalid JSON.\n"
    "If you output anything else, the workflow will break.\n"
    "If a section is not needed, use an empty string or array.\n"
    "Example output:\n"
    "{\n  \"Backend Implementation Plan\": [\"...\"],\n  \"Frontend Implementation Plan\": [\"...\"],\n  \"API/Data Contracts\": \"...\",\n  \"Acceptance Criteria\": [\"...\"]\n}\n"
)

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