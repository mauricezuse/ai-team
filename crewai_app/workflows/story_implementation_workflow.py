import yaml
import os
import json
import tempfile
import subprocess
from crewai_app.services.jira_service import JiraService
from crewai_app.services.github_service import GitHubService
from crewai_app.agents.pm import PMAgent
from crewai_app.agents.architect import ArchitectAgent
from crewai_app.agents.developer import DeveloperAgent
from crewai_app.agents.tester import TesterAgent
from crewai_app.agents.reviewer import ReviewerAgent
from crewai_app.utils.codebase_indexer import build_directory_tree, agent_select_relevant_files, index_selected_files_async
from crewai_app.services.openai_service import PromptTooLargeError

CHECKPOINT_DIR = "workflow_results"
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

class StoryImplementationWorkflow:
    """
    Story implementation workflow with robust, scalable codebase indexing.
    Uses SemanticSearchAgent and async indexing for large codebases.
    To use in other workflows:
      1. build_directory_tree(root_dir)
      2. agent_select_relevant_files(tree, story, agent=None, plugin='semantic')
      3. index_selected_files_async(root_dir, selected_files)
    """
    def __init__(self, story_id, use_real_jira=True, use_real_github=True, codebase_root=None):
        self.story_id = story_id
        self.jira_service = JiraService(use_real_jira)
        self.github_service = GitHubService(use_real_github)
        self.global_rules = self.load_global_rules()
        self.story_rules = None  # Can be set/overridden by architect
        self.workflow_log = []
        # Agents
        self.pm = PMAgent()
        self.architect = ArchitectAgent()
        self.developer = DeveloperAgent()
        self.tester = TesterAgent()
        self.reviewer = ReviewerAgent()
        # Use NEGISHI_GITHUB_REPO for codebase_root if not provided
        self.codebase_root = codebase_root or self.prepare_external_repo()
        self.checkpoint_file = os.path.join(CHECKPOINT_DIR, f"story_{self.story_id}_checkpoint.json")

    def prepare_external_repo(self):
        """
        Clone or update the external repo specified by NEGISHI_GITHUB_REPO env var.
        If the value is not a full URL, build it using org/user and repo from .env or env vars.
        Returns the local path to the repo.
        """
        repo_ref = os.environ.get("NEGISHI_GITHUB_REPO")
        if not repo_ref:
            raise ValueError("NEGISHI_GITHUB_REPO environment variable is not set.")
        # If not a full URL, build it
        if not repo_ref.startswith("http") and not repo_ref.startswith("git@"):
            # Try to get org/user and repo from env or .env
            if "/" in repo_ref:
                org, repo = repo_ref.split("/")
            else:
                org = os.environ.get("NEGISHI_GITHUB_ORG", "ZuseSystems")
                repo = repo_ref
            repo_url = f"https://github.com/{org}/{repo}.git"
        else:
            repo_url = repo_ref
        repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
        base_dir = os.path.join(tempfile.gettempdir(), "negishi_external_repos")
        os.makedirs(base_dir, exist_ok=True)
        repo_path = os.path.join(base_dir, repo_name)
        if not os.path.exists(repo_path):
            print(f"Cloning external repo {repo_url} to {repo_path}...")
            subprocess.run(["git", "clone", repo_url, repo_path], check=True)
        else:
            print(f"Updating external repo at {repo_path}...")
            subprocess.run(["git", "-C", repo_path, "pull"], check=True)
        return repo_path

    def load_global_rules(self):
        with open('coding_rules.yaml', 'r') as f:
            return yaml.safe_load(f)

    def _convert_sets_to_lists(self, obj):
        if isinstance(obj, dict):
            return {k: self._convert_sets_to_lists(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_sets_to_lists(i) for i in obj]
        elif isinstance(obj, set):
            return list(obj)
        else:
            return obj

    def save_checkpoint(self):
        with open(self.checkpoint_file, 'w') as f:
            json.dump(self._convert_sets_to_lists(self.workflow_log), f, indent=2)

    def load_checkpoint(self):
        if os.path.exists(self.checkpoint_file):
            with open(self.checkpoint_file, 'r') as f:
                self.workflow_log = json.load(f)
            return True
        return False

    def get_last_step(self):
        if not self.workflow_log:
            return None
        return self.workflow_log[-1]['step']

    def run(self, resume=False):
        """
        Run the workflow from the beginning or resume from the last checkpoint.
        Set resume=True to continue from the last successful step.
        """
        if resume and self.load_checkpoint():
            last_step = self.get_last_step()
            # Always reload codebase_index if resuming
            codebase_index = None
            selected_files = []
            for entry in self.workflow_log:
                if entry.get('step') == 'codebase_indexed':
                    selected_files = entry.get('selected_files', [])
                    break
            if selected_files:
                codebase_index = index_selected_files_async(self.codebase_root, selected_files)
            # Ensure codebase_index is never None
            if codebase_index is None:
                print("[WARN] codebase_index could not be reconstructed from checkpoint. Using empty index.")
                codebase_index = {}
        else:
            self.workflow_log = []
            last_step = None
            codebase_index = None

        # 0. Index the codebase (scalable, agent-driven, semantic, async)
        if last_step is None:
            try:
                # Only index backend and frontend directories
                tree = build_directory_tree(self.codebase_root, allowed_dirs=['backend', 'frontend'])
            except Exception:
                tree = None
            try:
                selected_files = agent_select_relevant_files(tree, self.story_id, agent=None, plugin='semantic')
            except Exception:
                selected_files = []
            try:
                codebase_index = index_selected_files_async(self.codebase_root, selected_files)
            except Exception:
                codebase_index = {}
            self.workflow_log.append({'step': 'codebase_indexed', 'index': list(codebase_index.keys()), 'selected_files': selected_files, 'indexing': 'semantic+async'})
            self.save_checkpoint()
        else:
            codebase_index = None  # Will be reloaded if needed

        # 1. Retrieve story details
        if last_step is None or last_step == 'codebase_indexed':
            story = self.jira_service.get_story(self.story_id)
            self.workflow_log.append({'step': 'story_retrieved', 'story': story})
            self.save_checkpoint()
        else:
            story = self.workflow_log[-1]['story'] if self.workflow_log[-1]['step'] == 'story_retrieved' else None

        # 2. PM reviews story, suggests improvements
        if last_step in [None, 'codebase_indexed', 'story_retrieved']:
            try:
                pm_suggestions = self.pm.review_story(story)
            except PromptTooLargeError as e:
                msg = f"Prompt too large in PM review (step: pm_review). Please optimize the prompt and try again."
                self.workflow_log.append({'step': 'pm_review_error', 'error': str(e), 'message': msg})
                self.save_checkpoint()
                print(msg)
                return self.workflow_log
            self.workflow_log.append({'step': 'pm_review', 'suggestions': pm_suggestions})
            self.save_checkpoint()
        else:
            pm_suggestions = self.workflow_log[-1]['suggestions'] if self.workflow_log[-1]['step'] == 'pm_review' else None

        # 3. Architect review and plan (two-stage: file selection, then plan)
        if last_step in [None, 'codebase_indexed', 'story_retrieved', 'pm_review']:
            # Filter codebase index to only top-level backend endpoint files and top-level frontend Angular component files
            backend_endpoints = [f for f in codebase_index if f.startswith('backend/apps/platform_service/api/endpoints/') and f.count('/') == 5 and f.endswith('.py')]
            frontend_components = [f for f in codebase_index if f.startswith('frontend/profile/src/app/') and f.count('/') == 5 and f.endswith('.ts')]
            top_level_files = backend_endpoints + frontend_components
            filtered_index = {f: codebase_index[f] for f in top_level_files}
            selected_files = self.architect.select_relevant_files(story, pm_suggestions, filtered_index)
            selected_index = {f: filtered_index[f] for f in selected_files if f in filtered_index}
            plan, updated_rules = self.architect.review_and_plan(story, pm_suggestions, self.global_rules, selected_index)
            self.story_rules = updated_rules
            self.workflow_log.append({'step': 'architect_review', 'plan': plan, 'selected_files': selected_files})
            self.save_checkpoint()
            last_step = 'architect_review'
        else:
            if self.workflow_log[-1]['step'] == 'architect_review':
                plan = self.workflow_log[-1]['plan']
                self.story_rules = self.workflow_log[-1]['rules']
            else:
                plan = None
                self.story_rules = self.global_rules

        # 4. User reviews/accepts/modifies (real user interaction)
        if last_step in [None, 'codebase_indexed', 'story_retrieved', 'pm_review', 'architect_review']:
            print("\n--- Architect's Implementation Plan ---")
            print(plan)
            user_input = input("Do you approve this plan? (y/n): ").strip().lower()
            user_approved = user_input == 'y'
            self.workflow_log.append({'step': 'user_review', 'approved': user_approved})
            self.save_checkpoint()
            if not user_approved:
                self.workflow_log.append({'step': 'terminated', 'reason': 'User did not approve'})
                self.save_checkpoint()
                print("Workflow terminated: User did not approve the plan.")
                return self.workflow_log
        else:
            if self.workflow_log[-1]['step'] == 'user_review' and not self.workflow_log[-1]['approved']:
                print("Workflow terminated: User did not approve the plan.")
                return self.workflow_log

        # 5. Assign to developer & tester, pass rules (now per-task, two-stage)
        if last_step in [None, 'codebase_indexed', 'story_retrieved', 'pm_review', 'architect_review', 'user_review']:
            # 1. Break down the story into tasks
            tasks = self.developer.break_down_story(story, plan, self.story_rules)
            self.workflow_log.append({'step': 'tasks_broken_down', 'tasks': tasks})
            self.save_checkpoint()
            branch_name = f"story-{self.story_id}-branch"
            subprocess.run(["git", "-C", self.codebase_root, "checkout", branch_name], check=True)
            for i, task in enumerate(tasks):
                # Developer: two-stage (file selection, then code)
                dev_result = self.developer.implement_task(task, plan, self.story_rules, codebase_index)
                self.workflow_log.append({'step': f'developer_implementation_{i}', 'task': task, 'result': dev_result})
                self.save_checkpoint()
                # Commit code for this task (as before)
                if isinstance(dev_result, list):
                    for file_entry in dev_result:
                        filename = file_entry['file']
                        content = file_entry['code']
                        file_path = os.path.join(self.codebase_root, filename)
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        with open(file_path, 'w') as f:
                            f.write(content)
                        subprocess.run(["git", "-C", self.codebase_root, "add", filename], check=True)
                    commit_msg = f"NEGISHI-{self.story_id}: Implemented task '{task.get('title', str(i))}'"
                    subprocess.run(["git", "-C", self.codebase_root, "commit", "-m", commit_msg], check=True)
                    subprocess.run(["git", "-C", self.codebase_root, "push"], check=True)
                # Tester: two-stage (file selection, then tests)
                test_result = self.tester.prepare_and_run_tests(dev_result, plan, self.story_rules, codebase_index)
                self.workflow_log.append({'step': f'tester_result_{i}', 'task': task, 'test_result': test_result})
                self.save_checkpoint()
                # Commit Playwright tests if generated
                if isinstance(test_result, dict) and 'tests' in test_result and isinstance(test_result['tests'], list):
                    for test_file in test_result['tests']:
                        test_filename = test_file.get('file')
                        test_code = test_file.get('test_code')
                        test_location = test_file.get('test_location')
                        if test_filename and test_code and test_location:
                            test_path = os.path.join(self.codebase_root, test_location, os.path.basename(test_filename) + '_test.ts')
                            os.makedirs(os.path.dirname(test_path), exist_ok=True)
                            with open(test_path, 'w') as f:
                                f.write(test_code)
                            subprocess.run(["git", "-C", self.codebase_root, "add", test_path], check=True)
                    commit_msg = f"NEGISHI-{self.story_id}: Added Playwright tests for task '{task.get('title', str(i))}'"
                    subprocess.run(["git", "-C", self.codebase_root, "commit", "-m", commit_msg], check=True)
                    subprocess.run(["git", "-C", self.codebase_root, "push"], check=True)
        else:
            dev_result = self.workflow_log[-1]['result'] if self.workflow_log[-1]['step'] == 'developer_implementation' else None

        if last_step in [None, 'codebase_indexed', 'story_retrieved', 'pm_review', 'architect_review', 'user_review', 'developer_implementation']:
            try:
                test_result = self.tester.prepare_and_run_tests(story, plan, self.story_rules)
                # Commit Playwright tests if generated
                if isinstance(test_result, dict) and 'tests' in test_result and isinstance(test_result['tests'], list):
                    branch_name = f"story-{self.story_id}-branch"
                    subprocess.run(["git", "-C", self.codebase_root, "checkout", branch_name], check=True)
                    test_files = []
                    for test in test_result['tests']:
                        # Determine test file path
                        if test['test_location'].endswith('/'):
                            test_dir = os.path.join(self.codebase_root, test['test_location'])
                        else:
                            test_dir = os.path.join(self.codebase_root, test['test_location'] + '/')
                        os.makedirs(test_dir, exist_ok=True)
                        # Use the base name of the file being tested for the test file name
                        base_name = os.path.splitext(os.path.basename(test['file']))[0]
                        test_file_path = os.path.join(test_dir, f"test_{base_name}.spec.ts")
                        with open(test_file_path, 'w') as f:
                            f.write(test['test_code'])
                        subprocess.run(["git", "-C", self.codebase_root, "add", test_file_path], check=True)
                        print(f"[Git] Staged Playwright test {test_file_path} for commit.")
                        test_files.append(test_file_path)
                    if test_files:
                        commit_msg = f"{self.story_id}: Add Playwright tests"
                        subprocess.run(["git", "-C", self.codebase_root, "commit", "-m", commit_msg], check=True)
                        subprocess.run(["git", "-C", self.codebase_root, "push", "origin", branch_name], check=True)
                        print(f"[Git] Committed and pushed Playwright tests to {branch_name}")
            except PromptTooLargeError as e:
                msg = f"Prompt too large in Tester step (step: tester_result). Please optimize the prompt and try again."
                self.workflow_log.append({'step': 'tester_result_error', 'error': str(e), 'message': msg})
                self.save_checkpoint()
                print(msg)
                return self.workflow_log
            self.workflow_log.append({'step': 'tester_result', 'result': test_result})
            self.save_checkpoint()
        else:
            test_result = self.workflow_log[-1]['result'] if self.workflow_log[-1]['step'] == 'tester_result' else None

        # 6. Reviewer checks implementation against rules
        if last_step in [None, 'codebase_indexed', 'story_retrieved', 'pm_review', 'architect_review', 'user_review', 'developer_implementation', 'tester_result']:
            try:
                review_result = self.reviewer.review_implementation(dev_result, plan, self.story_rules)
            except PromptTooLargeError as e:
                msg = f"Prompt too large in Reviewer step (step: reviewer_result). Please optimize the prompt and try again."
                self.workflow_log.append({'step': 'reviewer_result_error', 'error': str(e), 'message': msg})
                self.save_checkpoint()
                print(msg)
                return self.workflow_log
            self.workflow_log.append({'step': 'reviewer_result', 'result': review_result})
            self.save_checkpoint()
        else:
            review_result = self.workflow_log[-1]['result'] if self.workflow_log[-1]['step'] == 'reviewer_result' else None

        # 7. PR is created if approved
        if last_step in [None, 'codebase_indexed', 'story_retrieved', 'pm_review', 'architect_review', 'user_review', 'developer_implementation', 'tester_result', 'reviewer_result', 'tasks_broken_down']:
            if review_result.get('approved'):
                pr = self.github_service.create_pull_request(
                    branch=branch_name,
                    title=f"{self.story_id}: Implementation PR",
                    body="Automated PR for story implementation."
                )
                self.workflow_log.append({'step': 'pr_created', 'pr': pr})
            else:
                self.workflow_log.append({'step': 'pr_skipped', 'reason': 'Review not approved'})
            self.save_checkpoint()

        # 8. Log/report
        return self.workflow_log

# Example usage:
# workflow = StoryImplementationWorkflow('NEGISHI-123')
# log = workflow.run(resume=True)  # Set resume=True to continue from last checkpoint
# print(log)

# Documentation:
# - This workflow will create a branch, commit the developer's implementation, and open a PR in the external repo.
# - Requires: aiofiles (for async indexing), OPENAI_API_VERSION env var for Azure OpenAI embeddings.
# - Error handling is included for branch creation, commit, and PR creation steps. 