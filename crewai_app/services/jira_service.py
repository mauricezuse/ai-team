# Placeholder for Jira integration service
import os
import requests

class JiraService:
    def __init__(self, use_real: bool):
        self.use_real = use_real
        self.token = os.getenv("JIRA_API_TOKEN")
        self.email = os.getenv("JIRA_EMAIL")
        self.base_url = os.getenv("JIRA_BASE_URL")
        self.project_key = os.getenv("PROJECT_KEY", "NEGISHI")

    def create_ticket(self, summary, description):
        if self.use_real:
            url = f"{self.base_url}/rest/api/3/issue"
            auth = (self.email, self.token)
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            data = {
                "fields": {
                    "project": {"key": self.project_key},
                    "summary": summary,
                    "description": description,
                    "issuetype": {"name": "Task"}
                }
            }
            try:
                response = requests.post(url, auth=auth, headers=headers, json=data)
                response.raise_for_status()
                issue = response.json()
                issue_key = issue.get("key")
                issue_url = f"{self.base_url}/browse/{issue_key}" if issue_key else None
                print(f"[Jira] Created ticket: {issue_url}")
                return {"url": issue_url, "summary": summary}
            except Exception as e:
                print(f"[Jira ERROR] {e}")
                return None
        else:
            print(f"[Stub] Would create Jira ticket: {summary}")
            return {"url": "https://your-domain.atlassian.net/browse/PROJ-123", "summary": summary} 