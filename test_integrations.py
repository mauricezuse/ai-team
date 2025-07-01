import os
import time
from crewai_app.config import settings
from crewai_app.services.github_service import GitHubService
from crewai_app.services.jira_service import JiraService

print("=== AI-Team Integration Test ===")

# GitHub Test
print("\n[GitHub Integration Test]")
github_service = GitHubService(settings.use_real_github)
branch_name = f"test-integration-branch-{int(time.time())}"
# Create the branch from main first
branch_created = github_service.create_branch_from_main(branch_name)
if branch_created:
    commit_created = github_service.commit_test_file(branch_name)
    if commit_created:
        pr_result = github_service.create_pull_request(
            branch=branch_name,
            title="NEGISHI-999: Integration Test PR",
            body="This is a test PR created by the integration test script."
        )
        if pr_result and pr_result.get("url"):
            print(f"SUCCESS: PR created at {pr_result['url']}")
        else:
            print("FAILURE: PR was not created.")
    else:
        print("FAILURE: Commit was not created, skipping PR creation.")
else:
    print("FAILURE: Branch was not created, skipping PR creation.")

# Jira Test
print("\n[Jira Integration Test]")
jira_service = JiraService(settings.use_real_jira)
jira_result = jira_service.create_ticket(
    summary="Integration Test Ticket",
    description="This is a test Jira ticket created by the integration test script."
)
if jira_result and jira_result.get("url"):
    print(f"SUCCESS: Jira ticket created at {jira_result['url']}")
else:
    print("FAILURE: Jira ticket was not created.") 