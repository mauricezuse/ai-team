# Placeholder for Jira integration service
import os
import requests
from crewai_app.utils.logger import logger

class JiraService:
    def __init__(self, use_real: bool):
        self.use_real = use_real
        self.token = os.getenv("NEGISHI_JIRA_API_TOKEN")
        self.email = os.getenv("NEGISHI_JIRA_EMAIL")
        self.base_url = os.getenv("NEGISHI_JIRA_BASE_URL")
        self.project_key = os.getenv("NEGISHI_PROJECT_KEY", "NEGISHI")

    def get_createmeta(self):
        """
        Fetches the create metadata for the configured project from Jira.
        Returns the JSON response or None if the request fails.
        """
        if not self.use_real:
            logger.info("[Stub] Would fetch Jira create metadata.")
            return None
        url = f"{self.base_url}/rest/api/3/issue/createmeta?projectKeys={self.project_key}&expand=projects.issuetypes.fields"
        auth = (self.email, self.token)
        headers = {
            "Accept": "application/json"
        }
        logger.debug(f"[Jira DEBUG] GET {url} with auth user: {self.email}")
        try:
            response = requests.get(url, auth=auth, headers=headers)
            logger.debug(f"[Jira DEBUG] Response status: {response.status_code}")
            logger.debug(f"[Jira DEBUG] Response content: {response.text}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"[Jira ERROR] /createmeta failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"[Jira ERROR] Response content: {e.response.text}")
            return None

    def _to_adf(self, text):
        """
        Converts a plain text string to a simple Atlassian Document Format (ADF) document.
        """
        return {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": text}
                    ]
                }
            ]
        }

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
                    "description": self._to_adf(description),
                    "issuetype": {"name": "Story"}
                }
            }
            logger.debug(f"[Jira DEBUG] Creating ticket with payload: {data}")
            logger.debug(f"[Jira DEBUG] POST {url} with auth user: {self.email}")
            try:
                response = requests.post(url, auth=auth, headers=headers, json=data)
                logger.debug(f"[Jira DEBUG] Response status: {response.status_code}")
                logger.debug(f"[Jira DEBUG] Response content: {response.text}")
                response.raise_for_status()
                issue = response.json()
                issue_key = issue.get("key")
                issue_url = f"{self.base_url}/browse/{issue_key}" if issue_key else None
                logger.info(f"[Jira] Created ticket: {issue_url}")
                return {"url": issue_url, "summary": summary}
            except requests.exceptions.HTTPError as e:
                logger.error(f"[Jira ERROR] HTTPError: {e}")
                if e.response is not None:
                    logger.error(f"[Jira ERROR] Status code: {e.response.status_code}")
                    logger.error(f"[Jira ERROR] Response headers: {e.response.headers}")
                    logger.error(f"[Jira ERROR] Response content: {e.response.text}")
                return None
            except Exception as e:
                logger.error(f"[Jira ERROR] Unexpected: {e}")
                return None
        else:
            logger.info(f"[Stub] Would create Jira ticket: {summary}")
            return {"url": "https://your-domain.atlassian.net/browse/PROJ-123", "summary": summary}

    def get_story(self, story_id):
        """
        Fetches a Jira issue (story) by its key.
        Returns the JSON response or None if the request fails.
        """
        if not self.use_real:
            logger.info(f"[Stub] Would fetch Jira story: {story_id}")
            return {"key": story_id, "fields": {"summary": "Stub story summary", "description": "Stub story description"}}
        url = f"{self.base_url}/rest/api/3/issue/{story_id}"
        auth = (self.email, self.token)
        headers = {"Accept": "application/json"}
        logger.debug(f"[Jira DEBUG] GET {url} with auth user: {self.email}")
        try:
            response = requests.get(url, auth=auth, headers=headers)
            logger.debug(f"[Jira DEBUG] Response status: {response.status_code}")
            logger.debug(f"[Jira DEBUG] Response content: {response.text}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"[Jira ERROR] get_story failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"[Jira ERROR] Response content: {e.response.text}")
            return None 