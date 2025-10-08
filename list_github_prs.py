import os
from crewai_app.services.github_service import GitHubService

print(f"NEGISHI_GITHUB_TOKEN: {os.environ.get('NEGISHI_GITHUB_TOKEN')}")
print(f"NEGISHI_GITHUB_REPO: {os.environ.get('NEGISHI_GITHUB_REPO')}")

github = GitHubService(use_real=True)

# List all PRs
prs = github.list_pull_requests(state="all")
for pr in prs:
    print(f"PR #{pr['number']}: {pr['title']}")
    print(f"  State: {pr['state']}")
    print(f"  URL: {pr['html_url']}")
    print(f"  Head: {pr['head']['ref']}  ->  Base: {pr['base']['ref']}")
    print()

# Fetch and print details for PR #6
print("\n--- Details for PR #6 ---")
pr6 = github.get_pull_request(6)
if pr6:
    print(f"Title: {pr6['title']}")
    print(f"State: {pr6['state']}")
    print(f"URL: {pr6['html_url']}")
    print(f"Body: {pr6['body']}")
    print(f"Created by: {pr6['user']['login']}")
    print(f"Commits: {pr6['commits']}, Additions: {pr6['additions']}, Deletions: {pr6['deletions']}")
else:
    print("Could not fetch PR #6 details.")

# Fetch and print file changes for PR #6
print("\n--- Files changed in PR #6 ---")
files = github.get_pull_request_files(6)
if files:
    for f in files:
        print(f"- {f['filename']} ({f['status']}, +{f['additions']}/-{f['deletions']})")
        print(f"  Patch: {f.get('patch', '[no patch]')[:200]}{'...' if f.get('patch') and len(f['patch']) > 200 else ''}")
else:
    print("No files or could not fetch file changes for PR #6.") 