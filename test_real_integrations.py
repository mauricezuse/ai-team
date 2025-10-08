#!/usr/bin/env python3
"""
Real Integration Test Script
Tests actual Jira story retrieval and GitHub operations with real credentials
"""

import os
import sys
import json
from datetime import datetime
from crewai_app.services.jira_service import JiraService
from crewai_app.services.github_service import GitHubService
from crewai_app.config import settings

def test_jira_integration():
    """Test real Jira story retrieval"""
    print("🔍 Testing Jira Integration...")
    
    # Check environment variables
    required_vars = ['NEGISHI_JIRA_API_TOKEN', 'NEGISHI_JIRA_EMAIL', 'NEGISHI_JIRA_BASE_URL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        print("Please set these in your .env file:")
        for var in missing_vars:
            print(f"  {var}=your-value")
        return False
    
    jira_service = JiraService(use_real=True)
    
    # Test 1: Get story metadata
    print("  📋 Testing story metadata retrieval...")
    try:
        metadata = jira_service.get_createmeta()
        if metadata:
            print("  ✅ Story metadata retrieved successfully")
        else:
            print("  ⚠️  Story metadata retrieval failed")
    except Exception as e:
        print(f"  ❌ Story metadata error: {e}")
        return False
    
    # Test 2: Get specific story
    story_id = input("  📝 Enter a Jira story ID to test (e.g., NEGISHI-178): ").strip()
    if not story_id:
        print("  ⚠️  Skipping story retrieval test")
        return True
    
    try:
        story = jira_service.get_story(story_id)
        if story:
            print(f"  ✅ Story '{story_id}' retrieved successfully")
            print(f"     Summary: {story.get('fields', {}).get('summary', 'N/A')}")
            print(f"     Description: {story.get('fields', {}).get('description', 'N/A')[:100]}...")
            return True
        else:
            print(f"  ❌ Failed to retrieve story '{story_id}'")
            return False
    except Exception as e:
        print(f"  ❌ Story retrieval error: {e}")
        return False

def test_github_integration():
    """Test real GitHub operations"""
    print("\n🔍 Testing GitHub Integration...")
    
    # Check environment variables
    required_vars = ['GITHUB_TOKEN', 'GITHUB_REPO']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        print("Please set these in your .env file:")
        for var in missing_vars:
            print(f"  {var}=your-value")
        return False
    
    github_service = GitHubService(use_real=True)
    
    # Test 1: Create test branch
    branch_name = f"integration-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    print(f"  🌿 Creating test branch: {branch_name}")
    
    try:
        branch_created = github_service.create_branch_from_main(branch_name)
        if branch_created:
            print("  ✅ Test branch created successfully")
        else:
            print("  ❌ Failed to create test branch")
            return False
    except Exception as e:
        print(f"  ❌ Branch creation error: {e}")
        return False
    
    # Test 2: Create test commit
    print("  📝 Creating test commit...")
    try:
        commit_created = github_service.commit_test_file(branch_name)
        if commit_created:
            print("  ✅ Test commit created successfully")
        else:
            print("  ❌ Failed to create test commit")
            return False
    except Exception as e:
        print(f"  ❌ Commit creation error: {e}")
        return False
    
    # Test 3: Create test PR
    print("  🔄 Creating test pull request...")
    try:
        pr_result = github_service.create_pull_request(
            branch=branch_name,
            title="NEGISHI-999: Integration Test PR",
            body="This is a test PR created by the integration test script."
        )
        if pr_result and pr_result.get("url"):
            print(f"  ✅ Test PR created successfully: {pr_result['url']}")
            return True
        else:
            print("  ❌ Failed to create test PR")
            return False
    except Exception as e:
        print(f"  ❌ PR creation error: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🚀 AI-Team Real Integration Test")
    print("=" * 50)
    
    # Check if we should use real integrations
    use_real = input("Use real integrations? (y/n): ").strip().lower() == 'y'
    
    if not use_real:
        print("⚠️  Running in stub mode - no real API calls will be made")
        return
    
    # Test Jira
    jira_success = test_jira_integration()
    
    # Test GitHub
    github_success = test_github_integration()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Integration Test Results:")
    print(f"  Jira Integration: {'✅ PASS' if jira_success else '❌ FAIL'}")
    print(f"  GitHub Integration: {'✅ PASS' if github_success else '❌ FAIL'}")
    
    if jira_success and github_success:
        print("\n🎉 All integrations working correctly!")
        print("You can now set USE_REAL_JIRA=true and USE_REAL_GITHUB=true in your .env file")
    else:
        print("\n⚠️  Some integrations failed. Please check your configuration and try again.")

if __name__ == "__main__":
    main() 