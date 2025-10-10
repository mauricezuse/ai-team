#!/usr/bin/env python3
"""
Enhanced Story Implementation Workflow
Improved workflow with better agent collaboration, escalation handling, and error recovery.
"""

import yaml
import os
import json
import tempfile
import subprocess
from typing import Dict, List, Any, Optional
from datetime import datetime
from crewai_app.services.jira_service import JiraService
from crewai_app.services.github_service import GitHubService
from crewai_app.agents.pm import PMAgent
from crewai_app.agents.architect import ArchitectAgent
from crewai_app.agents.developer import DeveloperAgent
from crewai_app.agents.tester import TesterAgent
from crewai_app.agents.reviewer import ReviewerAgent
from crewai_app.agents.frontend import FrontendAgent, frontend_openai
from crewai_app.utils.codebase_indexer import build_directory_tree, agent_select_relevant_files, index_selected_files_async
from crewai_app.services.openai_service import PromptTooLargeError, OpenAIService
from crewai_app.utils.logger import logger, attach_handlers_to_all_ai_team_loggers
from crewai_app.config import settings

logger.info('[EnhancedWorkflow] Logger initialized in enhanced_story_workflow.py')

CHECKPOINT_DIR = "workflow_results"
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

class EnhancedStoryWorkflow:
    """
    Enhanced story implementation workflow with improved agent collaboration,
    escalation handling, and error recovery.
    """
    
    def __init__(self, story_id: str, use_real_jira: bool = True, use_real_github: bool = True, 
                 codebase_root: Optional[str] = None, user_intervention_mode: bool = False, 
                 workflow_id: Optional[int] = None):
        self.story_id = story_id
        self.workflow_id = workflow_id  # Store workflow_id for LLM tracking
        self.jira_service = JiraService(use_real_jira)
        self.github_service = GitHubService(use_real_github)
        self.global_rules = self.load_global_rules()
        self.story_rules = None
        self.workflow_log = []
        self.collaboration_queue = []  # Track pending collaborations
        self.escalation_queue = []     # Track pending escalations
        self.current_conversation_id = None  # Track current conversation for LLM calls
        
        # Initialize agents with proper OpenAIService instances
        self.pm = PMAgent()
        self.architect = ArchitectAgent(OpenAIService(deployment=settings.deployment_architect))
        self.developer = DeveloperAgent(OpenAIService(deployment=settings.deployment_developer))
        self.tester = TesterAgent()
        self.reviewer = ReviewerAgent()
        self.frontend = FrontendAgent(frontend_openai)
        
        # Agent registry for easy lookup
        self.agents = {
            'pm': self.pm,
            'architect': self.architect,
            'developer': self.developer,
            'frontend': self.frontend,
            'tester': self.tester,
            'reviewer': self.reviewer
        }
        
        self.codebase_root = codebase_root or self.prepare_external_repo()
        self.checkpoint_file = os.path.join(CHECKPOINT_DIR, f"enhanced_story_{self.story_id}_checkpoint.json")
        self.user_intervention_mode = user_intervention_mode
        
        # Ensure all ai_team.* loggers have handlers
        attach_handlers_to_all_ai_team_loggers()

    def prepare_external_repo(self):
        """Clone or update the external repo specified by NEGISHI_GITHUB_REPO env var."""
        repo_ref = os.environ.get("NEGISHI_GITHUB_REPO")
        if not repo_ref:
            raise ValueError("NEGISHI_GITHUB_REPO environment variable is not set.")
        
        if not repo_ref.startswith("http") and not repo_ref.startswith("git@"):
            if "/" in repo_ref:
                org, repo = repo_ref.split("/")
            else:
                org = os.environ.get("NEGISHI_GITHUB_ORG", "ZuseSystems")
                repo = repo_ref
            repo_url = f"https://github.com/{org}/{repo}.git"
        else:
            repo_url = repo_ref
            
        repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
        workspace_root = os.getcwd()
        submodule_path = os.path.join(workspace_root, "repos", repo_name)
        os.makedirs(os.path.dirname(submodule_path), exist_ok=True)
        
        if not os.path.exists(submodule_path):
            print(f"Adding backend repo as submodule: {repo_url} -> {submodule_path}")
            self.github_service.add_submodule(submodule_path, repo_url)
        else:
            print(f"Backend repo already present at {submodule_path}")
        return submodule_path

    def load_global_rules(self):
        """Load global coding rules from YAML file."""
        with open('coding_rules.yaml', 'r') as f:
            return yaml.safe_load(f)

    def save_checkpoint(self):
        """Save workflow state to checkpoint file."""
        checkpoint_data = {
            'story_id': self.story_id,
            'workflow_log': self.workflow_log,
            'collaboration_queue': self.collaboration_queue,
            'escalation_queue': self.escalation_queue,
            'story_rules': self.story_rules,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2, default=str)
        
        logger.info(f'[EnhancedWorkflow] Checkpoint saved to {self.checkpoint_file}')

    def load_checkpoint(self) -> bool:
        """Load workflow state from checkpoint file."""
        if not os.path.exists(self.checkpoint_file):
            return False
        
        try:
            with open(self.checkpoint_file, 'r') as f:
                checkpoint_data = json.load(f)
            
            self.workflow_log = checkpoint_data.get('workflow_log', [])
            self.collaboration_queue = checkpoint_data.get('collaboration_queue', [])
            self.escalation_queue = checkpoint_data.get('escalation_queue', [])
            self.story_rules = checkpoint_data.get('story_rules')
            
            logger.info(f'[EnhancedWorkflow] Checkpoint loaded from {self.checkpoint_file}')
            return True
        except Exception as e:
            logger.error(f'[EnhancedWorkflow] Failed to load checkpoint: {e}')
            return False

    def get_last_step(self) -> Optional[str]:
        """Get the last completed step from workflow log."""
        if not self.workflow_log:
            return None
        return self.workflow_log[-1].get('step')

    def handle_escalation(self, escalation: Dict[str, Any]) -> bool:
        """Handle an escalation request between agents."""
        from_agent = escalation['from_agent']
        to_agent = escalation['to_agent']
        reason = escalation['reason']
        context = escalation.get('context', {})
        
        logger.info(f'[EnhancedWorkflow] Handling escalation: {from_agent} -> {to_agent}: {reason}')
        
        if to_agent not in self.agents:
            logger.error(f'[EnhancedWorkflow] Unknown agent: {to_agent}')
            return False
        
        # Add to escalation queue for processing
        self.escalation_queue.append({
            **escalation,
            'status': 'queued',
            'queued_at': datetime.now().isoformat()
        })
        
        # Log the escalation
        self.workflow_log.append({
            'step': 'escalation_queued',
            'escalation': escalation,
            'timestamp': datetime.now().isoformat()
        })
        
        return True

    def handle_collaboration(self, collaboration: Dict[str, Any]) -> bool:
        """Handle a collaboration request between agents."""
        from_agent = collaboration['from_agent']
        to_agent = collaboration['to_agent']
        request_type = collaboration['request_type']
        data = collaboration['data']
        
        logger.info(f'[EnhancedWorkflow] Handling collaboration: {from_agent} -> {to_agent}: {request_type}')
        
        if to_agent not in self.agents:
            logger.error(f'[EnhancedWorkflow] Unknown agent: {to_agent}')
            return False
        
        # Add to collaboration queue for processing
        self.collaboration_queue.append({
            **collaboration,
            'status': 'queued',
            'queued_at': datetime.now().isoformat()
        })
        
        # Log the collaboration request
        self.workflow_log.append({
            'step': 'collaboration_queued',
            'collaboration': collaboration,
            'timestamp': datetime.now().isoformat()
        })
        
        return True

    def process_collaboration_queue(self) -> List[Dict[str, Any]]:
        """Process all pending collaboration requests."""
        results = []
        
        for collaboration in self.collaboration_queue[:]:  # Copy to avoid modification during iteration
            if collaboration['status'] != 'queued':
                continue
                
            try:
                # Process the collaboration based on request type
                result = self._process_collaboration_request(collaboration)
                collaboration['status'] = 'completed'
                collaboration['result'] = result
                results.append(result)
                
            except Exception as e:
                collaboration['status'] = 'failed'
                collaboration['error'] = str(e)
                logger.error(f'[EnhancedWorkflow] Collaboration failed: {e}')
        
        return results

    def _process_collaboration_request(self, collaboration: Dict[str, Any]) -> Dict[str, Any]:
        """Process a specific collaboration request."""
        request_type = collaboration['request_type']
        data = collaboration['data']
        
        if request_type == 'api_contract':
            # Frontend requesting API contract from backend
            return self._generate_api_contract(data)
        elif request_type == 'ui_spec':
            # Backend requesting UI spec from frontend
            return self._generate_ui_spec(data)
        elif request_type == 'data_model':
            # Any agent requesting data model from architect
            return self._generate_data_model(data)
        else:
            raise ValueError(f'Unknown collaboration request type: {request_type}')

    def _generate_api_contract(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate API contract for frontend-backend collaboration."""
        endpoint_name = data.get('endpoint_name', 'unknown')
        description = data.get('description', '')
        
        # Use developer agent to generate API contract
        prompt = f"""
        Generate an API contract for: {endpoint_name}
        Description: {description}
        
        Include:
        - HTTP method and path
        - Request parameters and body schema
        - Response schema
        - Error codes
        - Example requests/responses
        """
        
        # Create conversation for developer API contract generation
        conversation_id = self._create_conversation('api_contract_generation', 'developer')
        
        result = self.developer._run_llm(
            prompt, 
            step="api_contract_generation",
            workflow_id=self.workflow_id,
            conversation_id=conversation_id
        )
        
        return {
            'type': 'api_contract',
            'endpoint_name': endpoint_name,
            'contract': result,
            'generated_by': 'developer'
        }

    def _generate_ui_spec(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate UI specification for backend-frontend collaboration."""
        component_name = data.get('component_name', 'unknown')
        description = data.get('description', '')
        
        # Use frontend agent to generate UI spec
        prompt = f"""
        Generate a UI specification for: {component_name}
        Description: {description}
        
        Include:
        - Component structure
        - Props/inputs
        - Events/outputs
        - Styling requirements
        - Accessibility considerations
        """
        
        # Create conversation for frontend UI spec generation
        conversation_id = self._create_conversation('ui_spec_generation', 'frontend')
        
        result = self.frontend._run_llm(
            prompt, 
            step="ui_spec_generation",
            workflow_id=self.workflow_id,
            conversation_id=conversation_id
        )
        
        return {
            'type': 'ui_spec',
            'component_name': component_name,
            'spec': result,
            'generated_by': 'frontend'
        }

    def _generate_data_model(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data model specification."""
        model_name = data.get('model_name', 'unknown')
        description = data.get('description', '')
        
        # Use architect agent to generate data model
        prompt = f"""
        Generate a data model for: {model_name}
        Description: {description}
        
        Include:
        - Fields and types
        - Relationships
        - Validation rules
        - Database considerations
        """
        
        # Create conversation for architect data model generation
        conversation_id = self._create_conversation('data_model_generation', 'architect')
        
        result = self.architect._run_llm(
            prompt, 
            step="data_model_generation",
            workflow_id=self.workflow_id,
            conversation_id=conversation_id
        )
        
        return {
            'type': 'data_model',
            'model_name': model_name,
            'model': result,
            'generated_by': 'architect'
        }

    def run(self, resume: bool = False) -> List[Dict[str, Any]]:
        """
        Run the enhanced workflow with improved collaboration and escalation handling.
        """
        print(f'[EnhancedWorkflow] Starting enhanced workflow for story {self.story_id}')
        logger.info(f'[EnhancedWorkflow] Enhanced workflow started for story {self.story_id}')
        
        try:
            # Load checkpoint if resuming
            if resume and self.load_checkpoint():
                last_step = self.get_last_step()
                print(f'[EnhancedWorkflow] Resuming from step: {last_step}')
            else:
                last_step = None
                self.workflow_log = []
                self.collaboration_queue = []
                self.escalation_queue = []

            # Step 1: Retrieve and analyze story
            if last_step is None:
                story = self._retrieve_and_analyze_story()
                if not story:
                    raise ValueError("Failed to retrieve story from Jira")
                
                # Step 2: Index codebase
                codebase_index = self._index_codebase()
                
                # Step 3: Generate implementation plan
                plan = self._generate_implementation_plan(story, codebase_index)
                
                # Step 4: Break down tasks with collaboration
                tasks = self._break_down_tasks_with_collaboration(story, plan)
                
                # Step 5: Process collaboration queue
                collaboration_results = self.process_collaboration_queue()
                
                # Step 6: Execute tasks with escalation handling
                results = self._execute_tasks_with_escalation(tasks, plan, codebase_index)
                
                # Step 7: Final review and testing
                final_results = self._final_review_and_testing(results)
                
                self.save_checkpoint()
                return final_results
            else:
                # Resume logic - implement based on last_step
                print(f'[EnhancedWorkflow] Resume logic not yet implemented for step: {last_step}')
                return self.workflow_log
                
        except Exception as e:
            logger.error(f'[EnhancedWorkflow] Workflow failed: {e}')
            self.save_checkpoint()
            raise
    
    def _create_conversation(self, step: str, agent: str, status: str = 'running') -> Optional[int]:
        """Create conversation in database before agent execution for LLM tracking"""
        if not self.workflow_id:
            logger.warning(f"[EnhancedWorkflow] No workflow_id available for conversation creation")
            return None
            
        try:
            from crewai_app.database import get_db, Conversation
            from datetime import datetime
            
            db = next(get_db())
            
            conversation = Conversation(
                workflow_id=self.workflow_id,
                step=step,
                agent=agent,
                status=status,
                timestamp=datetime.utcnow()
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            
            logger.info(f"[EnhancedWorkflow] Created conversation {conversation.id} for step {step}")
            return conversation.id
            
        except Exception as e:
            logger.error(f"[EnhancedWorkflow] Failed to create conversation: {e}")
            return None

    def _retrieve_and_analyze_story(self) -> Optional[Dict[str, Any]]:
        """Retrieve story from Jira and perform initial analysis."""
        print(f'[EnhancedWorkflow] Retrieving story {self.story_id} from Jira...')
        
        story = self.jira_service.get_story(self.story_id)
        if not story:
            logger.error(f'[EnhancedWorkflow] Failed to retrieve story {self.story_id}')
            return None
        
        # Create conversation for PM analysis
        self.current_conversation_id = self._create_conversation('story_retrieved_and_analyzed', 'pm')
        
        # PM analysis with LLM tracking context
        pm_suggestions = self.pm.review_story(
            story, 
            workflow_id=self.workflow_id,
            conversation_id=self.current_conversation_id
        )
        
        self.workflow_log.append({
            'step': 'story_retrieved_and_analyzed',
            'story': story,
            'pm_suggestions': pm_suggestions,
            'timestamp': datetime.now().isoformat()
        })
        
        return story

    def _index_codebase(self) -> Dict[str, Any]:
        """Index the codebase for relevant files."""
        print('[EnhancedWorkflow] Indexing codebase...')
        
        try:
            # Include common monorepo-style layouts
            tree = build_directory_tree(self.codebase_root, allowed_dirs=['backend', 'frontend', 'backend/apps'])
            selected_files = agent_select_relevant_files(tree, self.story_id, agent=None, plugin='semantic')
            codebase_index = index_selected_files_async(self.codebase_root, selected_files)
            # Cache for later tester use
            self.latest_codebase_index = codebase_index
            
            self.workflow_log.append({
                'step': 'codebase_indexed',
                'selected_files': selected_files,
                'index_keys': list(codebase_index.keys()),
                'timestamp': datetime.now().isoformat()
            })
            
            return codebase_index
        except Exception as e:
            logger.error(f'[EnhancedWorkflow] Codebase indexing failed: {e}')
            return {}

    def _generate_implementation_plan(self, story: Dict[str, Any], codebase_index: Dict[str, Any]) -> Dict[str, Any]:
        """Generate implementation plan with architect."""
        print('[EnhancedWorkflow] Generating implementation plan...')
        
        # Get pm_suggestions from workflow log, with fallback
        pm_suggestions = None
        for entry in reversed(self.workflow_log):
            if 'pm_suggestions' in entry:
                pm_suggestions = entry['pm_suggestions']
                break
        
        if pm_suggestions is None:
            # Fallback: generate basic suggestions
            pm_suggestions = ["Implement the story according to acceptance criteria"]
        
        # Filter relevant files for architect
        backend_endpoints = [f for f in codebase_index if f.startswith('backend/apps/platform_service/api/endpoints/') and f.count('/') == 5 and f.endswith('.py')]
        frontend_components = [f for f in codebase_index if f.startswith('frontend/profile/src/app/') and f.count('/') == 5 and f.endswith('.ts')]
        top_level_files = backend_endpoints + frontend_components
        filtered_index = {f: codebase_index[f] for f in top_level_files}
        
        # Create conversation for architect file selection
        conversation_id = self._create_conversation('file_selection', 'architect')
        
        selected_files = self.architect.select_relevant_files(
            story, 
            pm_suggestions, 
            filtered_index,
            workflow_id=self.workflow_id,
            conversation_id=conversation_id
        )
        selected_index = {f: filtered_index[f] for f in selected_files if f in filtered_index}
        
        # Generate plans
        # Create conversation for architect user acceptance plan
        conversation_id = self._create_conversation('user_acceptance_plan', 'architect')
        
        user_plan = self.architect.generate_plan_for_user_acceptance(
            story, 
            pm_suggestions, 
            selected_index,
            workflow_id=self.workflow_id,
            conversation_id=conversation_id
        )
        # Create conversation for architect dev plan
        conversation_id = self._create_conversation('dev_plan', 'architect')
        
        dev_plan, updated_rules = self.architect.review_and_plan(
            story, 
            pm_suggestions, 
            selected_index,
            workflow_id=self.workflow_id,
            conversation_id=conversation_id
        )
        
        self.story_rules = updated_rules
        
        # Parse dev plan
        if isinstance(dev_plan, str):
            try:
                plan = json.loads(dev_plan)
            except Exception as e:
                logger.error(f'[EnhancedWorkflow] Failed to parse architect plan: {e}')
                plan = {}
        else:
            plan = dev_plan
        
        self.workflow_log.append({
            'step': 'implementation_plan_generated',
            'plan': plan,
            'user_plan': user_plan,
            'selected_files': selected_files,
            'timestamp': datetime.now().isoformat()
        })
        
        return plan

    def _break_down_tasks_with_collaboration(self, story: Dict[str, Any], plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Break down tasks with collaboration between agents."""
        print('[EnhancedWorkflow] Breaking down tasks with collaboration...')
        
        backend_plan = plan.get('Backend Implementation Plan', [])
        frontend_plan = plan.get('Frontend Implementation Plan', [])
        
        # Break down tasks
        backend_tasks = []
        frontend_tasks = []
        
        if backend_plan:
            try:
                backend_tasks = self.developer.break_down_story(story, backend_plan, self.story_rules)
            except Exception as e:
                logger.error(f'[EnhancedWorkflow] Backend task breakdown failed: {e}')
        
        if frontend_plan:
            try:
                frontend_tasks = self.frontend.break_down_story(story, frontend_plan, self.story_rules)
            except Exception as e:
                logger.error(f'[EnhancedWorkflow] Frontend task breakdown failed: {e}')
        
        # Check for collaboration needs
        all_tasks = backend_tasks + frontend_tasks
        for task in all_tasks:
            if self.developer.should_collaborate(task, {}):
                # Request collaboration
                collaboration = self.developer.request_collaboration(
                    'frontend', 'api_contract', {'endpoint_name': task.get('title', 'unknown')}
                )
                self.handle_collaboration(collaboration)
        
        self.workflow_log.append({
            'step': 'tasks_broken_down_with_collaboration',
            'backend_tasks': backend_tasks,
            'frontend_tasks': frontend_tasks,
            'timestamp': datetime.now().isoformat()
        })
        
        return all_tasks

    def _execute_tasks_with_escalation(self, tasks: List[Dict[str, Any]], plan: Dict[str, Any], codebase_index: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute tasks with escalation handling."""
        print('[EnhancedWorkflow] Executing tasks with escalation handling...')
        
        results = []
        branch_name = f"enhanced-story-{self.story_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Create branch
        try:
            subprocess.run(["git", "-C", self.codebase_root, "checkout", "-b", branch_name], check=True)
        except subprocess.CalledProcessError:
            # Branch might already exist
            subprocess.run(["git", "-C", self.codebase_root, "checkout", branch_name], check=False)
        
        for i, task in enumerate(tasks):
            task_type = task.get('type', '').lower()
            agent = self.agents.get('frontend' if task_type == 'frontend' else 'developer')
            
            if not agent:
                logger.error(f'[EnhancedWorkflow] No agent found for task type: {task_type}')
                continue
            
            print(f'[EnhancedWorkflow] Executing task {i+1}/{len(tasks)}: {task.get("title", "Unknown")}')
            
            try:
                # Check if escalation is needed
                if agent.needs_escalation(task, {}):
                    escalation = agent.escalate(
                        "Task requires architectural review",
                        "architect",
                        {"task": task, "context": "complex_implementation"}
                    )
                    self.handle_escalation(escalation)
                
                # Execute task
                result = agent.implement_task(
                    task, plan, self.story_rules, codebase_index,
                    branch=branch_name, repo_root=self.codebase_root
                )
                
                # Persist any generated files to the repo and commit them
                try:
                    self._persist_and_commit_result(result, branch_name)
                except Exception as e:
                    logger.error(f"[EnhancedWorkflow] Persist/commit failed: {e}")

                results.append({
                    'task': task,
                    'result': result,
                    'status': 'completed',
                    'agent': agent.name
                })
                
            except Exception as e:
                logger.error(f'[EnhancedWorkflow] Task execution failed: {e}')
                results.append({
                    'task': task,
                    'error': str(e),
                    'status': 'failed',
                    'agent': agent.name
                })
        
        self.workflow_log.append({
            'step': 'tasks_executed_with_escalation',
            'results': results,
            'branch_name': branch_name,
            'timestamp': datetime.now().isoformat()
        })
        
        # After tasks, push branch and create PR
        try:
            self._push_branch_and_create_pr(branch_name)
        except Exception as e:
            logger.error(f"[EnhancedWorkflow] Push/PR failed: {e}")
        
        return results

    def _push_branch_and_create_pr(self, branch_name: str) -> None:
        import subprocess
        # Push branch
        try:
            subprocess.run(["git", "-C", self.codebase_root, "push", "-u", "origin", branch_name], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"[EnhancedWorkflow] git push failed: {e}")
            return
        # Create PR
        pr_title = f"{self.story_id}: Enhanced workflow implementation"
        pr_body = f"Automated implementation for {self.story_id} including code and tests."
        pr = self.github_service.create_pull_request(branch_name, pr_title, pr_body)
        if pr:
            self.workflow_log.append({'step': 'pr_created', 'pr': pr, 'timestamp': datetime.now().isoformat()})
        else:
            self.workflow_log.append({'step': 'pr_skipped', 'reason': 'PR creation failed', 'timestamp': datetime.now().isoformat()})

    def _final_review_and_testing(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Perform final review and testing."""
        print('[EnhancedWorkflow] Performing final review and testing...')
        
        # Reviewer review
        review_results = []
        for result in results:
            if result['status'] == 'completed':
                try:
                    # Use the correct method name from ReviewerAgent
                    # Create conversation for reviewer implementation review
                    conversation_id = self._create_conversation('implementation_review', 'reviewer')
                    
                    review = self.reviewer.review_implementation(
                        result['result'], 
                        result.get('task', {}), 
                        self.story_rules,
                        workflow_id=self.workflow_id,
                        conversation_id=conversation_id
                    )
                    review_results.append({
                        'task': result['task'],
                        'review': review,
                        'status': 'reviewed'
                    })
                except Exception as e:
                    logger.error(f'[EnhancedWorkflow] Review failed: {e}')
        
        # Tester testing (pass real codebase index and persist generated tests)
        test_results = []
        for result in results:
            if result['status'] == 'completed':
                try:
                    # Create conversation for tester test preparation
                    conversation_id = self._create_conversation('test_preparation', 'tester')
                    
                    tests = self.tester.prepare_and_run_tests(
                        result['result'],
                        result.get('task', {}),
                        self.story_rules,
                        getattr(self, 'latest_codebase_index', {}),
                        workflow_id=self.workflow_id,
                        conversation_id=conversation_id
                    )
                    # Write tests to disk and commit
                    if isinstance(tests, dict) and isinstance(tests.get('tests'), list):
                        self._persist_tests_and_commit(tests['tests'], getattr(self, 'current_branch', None))
                    test_results.append({
                        'task': result['task'],
                        'tests': tests,
                        'status': 'tested'
                    })
                except Exception as e:
                    logger.error(f'[EnhancedWorkflow] Test generation failed: {e}')
        
        final_results = {
            'implementation_results': results,
            'review_results': review_results,
            'test_results': test_results,
            'collaboration_results': self.collaboration_queue,
            'escalation_results': self.escalation_queue
        }
        
        self.workflow_log.append({
            'step': 'final_review_and_testing_completed',
            'final_results': final_results,
            'timestamp': datetime.now().isoformat()
        })
        
        return [final_results] 

    def _persist_and_commit_result(self, result: Any, branch_name: str) -> None:
        """Persist agent result files to the repo and create a commit."""
        import os
        import subprocess
        if not result:
            return
        self.current_branch = branch_name
        files_written = []
        # Result can be a list[{file, code}] or dict with similar structure
        items = []
        if isinstance(result, list):
            items = [r for r in result if isinstance(r, dict) and 'file' in r and 'code' in r]
        elif isinstance(result, dict) and 'file' in result and 'code' in result:
            items = [result]
        for item in items:
            rel_path = item['file']
            code = item['code']
            abs_path = os.path.join(self.codebase_root, rel_path)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, 'w') as f:
                f.write(code)
            files_written.append(rel_path)
        if not files_written:
            return
        # git add/commit
        try:
            subprocess.run(["git", "-C", self.codebase_root, "add"] + files_written, check=True)
            commit_msg = f"{os.environ.get('NEGISHI_BRANCH_ID', self.story_id)}: Implement {len(files_written)} file(s)"
            subprocess.run(["git", "-C", self.codebase_root, "commit", "-m", commit_msg], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"[EnhancedWorkflow] git add/commit failed: {e}")

    def _persist_tests_and_commit(self, tests: List[Dict[str, Any]], branch_name: Optional[str]) -> None:
        """Persist generated test files and commit them."""
        import os
        import subprocess
        files_written = []
        for t in tests:
            file_hint = t.get('file') or 'unknown'
            test_dir = t.get('test_location') or 'tests/'
            test_code = t.get('test_code') or ''
            # Create a deterministic filename
            base_name = os.path.basename(file_hint).replace('.', '_')
            test_filename = os.path.join(test_dir, f"test_{base_name}.py") if test_dir.startswith('backend') or test_dir.startswith('tests') else os.path.join(test_dir, f"{base_name}.spec.ts")
            abs_path = os.path.join(self.codebase_root, test_filename)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, 'w') as f:
                f.write(test_code)
            files_written.append(test_filename)
        if not files_written:
            return
        try:
            subprocess.run(["git", "-C", self.codebase_root, "add"] + files_written, check=True)
            commit_msg = f"{os.environ.get('NEGISHI_BRANCH_ID', self.story_id)}: Add {len(files_written)} autogenerated tests"
            subprocess.run(["git", "-C", self.codebase_root, "commit", "-m", commit_msg], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"[EnhancedWorkflow] git add/commit (tests) failed: {e}")