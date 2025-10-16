# Placeholder for GitHub integration service
# Requires: pip install requests
import os
import requests  # type: ignore
import subprocess

class GitHubService:
    def __init__(self, use_real: bool = True):
        self.use_real = use_real
        self.project_key = os.getenv("NEGISHI_PROJECT_KEY", "NEGISHI")
        self.token = os.getenv("NEGISHI_GITHUB_TOKEN")
        self.repo = os.getenv("NEGISHI_GITHUB_REPO")
        self.api_url = f"https://api.github.com/repos/{self.repo}"
        # Load tokens, repo, etc. as needed

    def create_pull_request(self, branch, title, body):
        if self.use_real:
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github+json"
            }
            data = {
                "title": title,
                "head": branch,
                "base": "main",
                "body": body
            }
            try:
                response = requests.post(f"{self.api_url}/pulls", headers=headers, json=data)
                response.raise_for_status()
                pr = response.json()
                print(f"[GitHub] Created PR: {pr.get('html_url')}")
                return {"url": pr.get("html_url"), "title": pr.get("title")}
            except requests.exceptions.HTTPError as e:
                print(f"[GitHub ERROR] HTTPError: {e}")
                if e.response is not None:
                    print(f"[GitHub ERROR] Status code: {e.response.status_code}")
                    print(f"[GitHub ERROR] Response headers: {e.response.headers}")
                    print(f"[GitHub ERROR] Response content: {e.response.text}")
                return None
            except Exception as e:
                print(f"[GitHub ERROR] Unexpected: {e}")
                return None
        else:
            print(f"[Stub] Would create PR: {title}")
            return {"url": "https://github.com/your-org/your-repo/pull/123", "title": title}

    def create_branch_from_main(self, new_branch):
        if self.use_real:
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github+json"
            }
            # Get the latest commit SHA of main
            main_ref_url = f"{self.api_url}/git/ref/heads/main"
            resp = requests.get(main_ref_url, headers=headers)
            resp.raise_for_status()
            main_sha = resp.json()["object"]["sha"]
            # Create the new branch
            data = {
                "ref": f"refs/heads/{new_branch}",
                "sha": main_sha
            }
            create_ref_url = f"{self.api_url}/git/refs"
            resp = requests.post(create_ref_url, headers=headers, json=data)
            resp.raise_for_status()
            print(f"[GitHub] Created branch: {new_branch}")
            return True
        else:
            print(f"[Stub] Would create branch: {new_branch}")
            return True

    def commit_test_file(self, branch, filename="integration_test.txt", content="Integration test file."):
        if self.use_real:
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github+json"
            }
            # Get the latest commit SHA and tree SHA of the branch
            ref_url = f"{self.api_url}/git/ref/heads/{branch}"
            ref_resp = requests.get(ref_url, headers=headers)
            ref_resp.raise_for_status()
            commit_sha = ref_resp.json()["object"]["sha"]
            commit_url = f"{self.api_url}/git/commits/{commit_sha}"
            commit_resp = requests.get(commit_url, headers=headers)
            commit_resp.raise_for_status()
            tree_sha = commit_resp.json()["tree"]["sha"]
            # Create a new blob (file)
            blob_url = f"{self.api_url}/git/blobs"
            blob_data = {"content": content, "encoding": "utf-8"}
            blob_resp = requests.post(blob_url, headers=headers, json=blob_data)
            blob_resp.raise_for_status()
            blob_sha = blob_resp.json()["sha"]
            # Create a new tree with the new file
            tree_url = f"{self.api_url}/git/trees"
            tree_data = {
                "base_tree": tree_sha,
                "tree": [
                    {
                        "path": filename,
                        "mode": "100644",
                        "type": "blob",
                        "sha": blob_sha
                    }
                ]
            }
            tree_resp = requests.post(tree_url, headers=headers, json=tree_data)
            tree_resp.raise_for_status()
            new_tree_sha = tree_resp.json()["sha"]
            # Create a new commit
            commit_data = {
                "message": "NEGISHI-999: Integration test commit",
                "tree": new_tree_sha,
                "parents": [commit_sha]
            }
            new_commit_resp = requests.post(f"{self.api_url}/git/commits", headers=headers, json=commit_data)
            new_commit_resp.raise_for_status()
            new_commit_sha = new_commit_resp.json()["sha"]
            # Update the branch ref to point to the new commit
            update_ref_url = f"{self.api_url}/git/refs/heads/{branch}"
            update_ref_data = {"sha": new_commit_sha}
            update_ref_resp = requests.patch(update_ref_url, headers=headers, json=update_ref_data)
            update_ref_resp.raise_for_status()
            print(f"[GitHub] Committed test file to branch: {branch}")
            return True
        else:
            print(f"[Stub] Would commit test file to branch: {branch}")
            return True

    def list_pull_requests(self, state="all"):
        if self.use_real:
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github+json"
            }
            params = {"state": state}
            try:
                response = requests.get(f"{self.api_url}/pulls", headers=headers, params=params)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"[GitHub ERROR] Failed to list PRs: {e}")
                return []
        else:
            print("[Stub] Would list PRs")
            return []

    def get_pull_request(self, number):
        if self.use_real:
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github+json"
            }
            try:
                response = requests.get(f"{self.api_url}/pulls/{number}", headers=headers)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"[GitHub ERROR] Failed to fetch PR #{number}: {e}")
                return None
        else:
            print(f"[Stub] Would fetch PR #{number}")
            return None

    def get_pull_request_files(self, number):
        if self.use_real:
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github+json"
            }
            try:
                response = requests.get(f"{self.api_url}/pulls/{number}/files", headers=headers)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"[GitHub ERROR] Failed to fetch PR files for #{number}: {e}")
                return []
        else:
            print(f"[Stub] Would fetch PR files for #{number}")
            return []

    def add_submodule(self, submodule_path: str, repo_url: str):
        """
        Adds the given repo as a git submodule at the specified path.
        Usage:
            github_service.add_submodule('backend', 'https://github.com/your-org/backend-repo.git')
        """
        try:
            if os.path.exists(submodule_path):
                print(f"[GitHubService] Submodule path '{submodule_path}' already exists. Skipping add.")
                return True
            print(f"[GitHubService] Adding submodule: {repo_url} at {submodule_path}")
            subprocess.run(["git", "submodule", "add", repo_url, submodule_path], check=True)
            subprocess.run(["git", "submodule", "update", "--init", "--recursive"], check=True)
            print(f"[GitHubService] Submodule added and initialized: {submodule_path}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[GitHubService ERROR] Failed to add submodule: {e}")
            return False 

    # ------- New helper methods for PR/checks/diffs/artifacts --------
    def get_workflow_pr(self, workflow):
        """
        Resolve the latest PR for the given workflow. Implement based on naming or saved metadata.
        """
        if not self.use_real:
            # Stub: no PR returned
            return None
        try:
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github+json"
            }
            # Heuristic: list PRs and match by branch naming or title prefix
            prs = requests.get(f"{self.api_url}/pulls", headers=headers, params={"state": "all"}).json()
            for pr in prs:
                title = pr.get('title') or ''
                if workflow.jira_story_id and workflow.jira_story_id in title:
                    return {
                        'number': pr.get('number'),
                        'url': pr.get('html_url'),
                        'title': pr.get('title'),
                        'state': pr.get('state'),
                        'head_branch': pr.get('head', {}).get('ref'),
                        'base_branch': pr.get('base', {}).get('ref'),
                        'head_sha': pr.get('head', {}).get('sha'),
                        'created_at': pr.get('created_at'),
                        'merged_at': pr.get('merged_at'),
                    }
            return None
        except Exception:
            return None

    def list_check_runs_for_pr(self, workflow, pr_number):
        if not self.use_real:
            return []
        try:
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github+json"
            }
            # Obtain head SHA first
            pr = requests.get(f"{self.api_url}/pulls/{pr_number}", headers=headers).json()
            head_sha = pr.get('head', {}).get('sha')
            if not head_sha:
                return []
            checks = requests.get(f"{self.api_url}/commits/{head_sha}/check-runs", headers={**headers, "Accept": "application/vnd.github.antiope-preview+json"}).json()
            runs = checks.get('check_runs', []) if isinstance(checks, dict) else []
            out = []
            for r in runs:
                out.append({
                    'name': r.get('name'),
                    'status': r.get('status'),
                    'conclusion': r.get('conclusion'),
                    'html_url': r.get('html_url') or r.get('details_url'),
                    'started_at': r.get('started_at'),
                    'completed_at': r.get('completed_at'),
                })
            return out
        except Exception:
            return []

    def get_workflow_diffs(self, workflow):
        if not self.use_real:
            return []
        try:
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github+json"
            }
            # Heuristic: find PR and get files with patches
            pr = self.get_workflow_pr(workflow)
            if not pr:
                return []
            files = requests.get(f"{self.api_url}/pulls/{pr['number']}/files", headers=headers).json()
            diffs = []
            for f in files or []:
                diffs.append({
                    'path': f.get('filename'),
                    'patch': f.get('patch') or '',
                    'head_sha': pr.get('head_sha'),
                    'base_sha': None,
                })
            return diffs
        except Exception:
            return []

    def list_workflow_artifacts(self, workflow):
        if not self.use_real:
            return []
        try:
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github+json"
            }
            # Basic approach: list Actions artifacts (requires Actions usage)
            arts = requests.get(f"{self.api_url}/actions/artifacts", headers=headers).json()
            items = arts.get('artifacts', []) if isinstance(arts, dict) else []
            out = []
            for a in items:
                out.append({
                    'kind': 'actions-artifact',
                    'uri': a.get('archive_download_url'),
                    'checksum': None,
                    'size_in_bytes': a.get('size_in_bytes'),
                })
            return out
        except Exception:
            return []

    def rerun_check_suite(self, check_suite_id: int) -> bool:
        if not self.use_real:
            print(f"[Stub] Would re-run check suite {check_suite_id}")
            return True
        try:
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github+json"
            }
            url = f"{self.api_url}/check-suites/{check_suite_id}/rerequest"
            resp = requests.post(url, headers=headers)
            if 200 <= resp.status_code < 300:
                return True
            print(f"[GitHub ERROR] Rerun check suite failed: {resp.status_code} {resp.text}")
            return False
        except Exception as e:
            print(f"[GitHub ERROR] rerun_check_suite failed: {e}")
            return False