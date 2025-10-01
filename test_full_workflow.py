#!/usr/bin/env python3
"""
Full Workflow Test - Tests both backend and frontend agents working together
Simulates a complete Jira story implementation from planning to execution
"""

import asyncio
import logging
from datetime import datetime
from crewai_app.agents.architect import ArchitectAgent
from crewai_app.agents.developer import DeveloperAgent as BackendAgent
from crewai_app.agents.frontend import FrontendAgent
from crewai_app.models.task import Task
from crewai_app.services.openai_service import OpenAIService
from crewai_app.config import settings
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_full_workflow():
    """Test the complete workflow from architect planning to implementation"""
    
    print("🚀 Starting Full Workflow Test")
    print("=" * 60)
    
    # Test Jira Story
    jira_story = {
        "key": "NEGISHI-178",
        "title": "Implement Featured Freelancers Feature",
        "description": """
        As a client, I want to see featured freelancers on the platform homepage
        so that I can quickly discover top talent for my projects.
        
        Acceptance Criteria:
        - Display a curated list of featured freelancers on the homepage
        - Each freelancer card shows: name, title, skills, rating, and avatar
        - Freelancers are sorted by rating (highest first)
        - Component is responsive and accessible
        - Backend API provides featured freelancers data
        - Frontend component is properly federated
        """,
        "type": "Feature",
        "priority": "High"
    }
    
    print(f"📋 Jira Story: {jira_story['key']} - {jira_story['title']}")
    print(f"📝 Description: {jira_story['description'][:100]}...")
    print()
    
    # Step 1: Architect creates implementation plan
    print("🏗️  Step 1: Architect Creating Implementation Plan")
    print("-" * 40)
    
    architect_openai = OpenAIService(deployment=settings.deployment_architect)
    architect = ArchitectAgent(architect_openai)
    # Wrap the story in a dict with 'fields' key for architect agent compatibility
    story = {"fields": jira_story}
    # Use acceptance criteria from story as pm_suggestions
    pm_suggestions = jira_story.get('acceptance_criteria', [])
    selected_index = {}  # For test, pass empty dict
    plan_json, _ = architect.review_and_plan(story, pm_suggestions, selected_index)
    plan = json.loads(plan_json)
    backend_tasks = plan.get('Backend Implementation Plan', [])
    frontend_tasks = plan.get('Frontend Implementation Plan', [])
    print(f"✅ Architect Plan Generated:")
    print(f"   - Backend Tasks: {len(backend_tasks)}")
    print(f"   - Frontend Tasks: {len(frontend_tasks)}")
    print()
    for i, task in enumerate(backend_tasks + frontend_tasks, 1):
        print(f"   {i}. {task['title']} ({task['type']})")
        print(f"      {task['description'][:80]}...")
    print()
    
    # Step 2: Backend Agent Implementation
    print("⚙️  Step 2: Backend Agent Implementation")
    print("-" * 40)
    
    backend_openai = OpenAIService(deployment=settings.deployment_developer)
    backend_agent = BackendAgent(backend_openai)
    backend_results = []
    for i, task in enumerate(backend_tasks, 1):
        print(f"   🔧 Backend Task {i}: {task['title']}")
        try:
            result = backend_agent.implement_task(task, plan, None, selected_index)
            backend_results.append(result)
            print(f"      ✅ Completed - {len(result)} files created/modified")
        except Exception as e:
            print(f"      ❌ Failed: {str(e)}")
    print()
    
    # Step 3: Frontend Agent Implementation
    print("🎨 Step 3: Frontend Agent Implementation")
    print("-" * 40)
    
    frontend_openai = OpenAIService(deployment=settings.deployment_frontend)
    frontend_agent = FrontendAgent(frontend_openai)
    frontend_results = []
    for i, task in enumerate(frontend_tasks, 1):
        print(f"   🎨 Frontend Task {i}: {task['title']}")
        try:
            result = frontend_agent.implement_task(task, plan, None, selected_index)
            frontend_results.append(result)
            print(f"      ✅ Completed - {len(result)} files created/modified")
        except Exception as e:
            print(f"      ❌ Failed: {str(e)}")
    print()
    
    # Step 4: Results Summary
    print("📊 Step 4: Results Summary")
    print("-" * 40)
    
    total_backend_files = sum(len(result) for result in backend_results)
    total_frontend_files = sum(len(result) for result in frontend_results)
    
    print(f"📈 Implementation Summary:")
    print(f"   - Backend Tasks: {len(backend_tasks)}")
    print(f"   - Frontend Tasks: {len(frontend_tasks)}")
    print(f"   - Backend Files: {total_backend_files}")
    print(f"   - Frontend Files: {total_frontend_files}")
    print(f"   - Total Files: {total_backend_files + total_frontend_files}")
    print()
    
    # Check for federation awareness
    federation_indicators = []
    for result in frontend_results:
        for file_info in result:
            if 'federation' in file_info.get('file', '').lower():
                federation_indicators.append(file_info['file'])
            if 'profile' in file_info.get('file', '').lower():
                federation_indicators.append(file_info['file'])
    
    if federation_indicators:
        print("✅ Federation Awareness Detected:")
        for indicator in federation_indicators[:3]:  # Show first 3
            print(f"   - {indicator}")
        if len(federation_indicators) > 3:
            print(f"   - ... and {len(federation_indicators) - 3} more")
    else:
        print("⚠️  No federation indicators found")
    
    print()
    print("🎉 Full Workflow Test Completed!")
    print("=" * 60)
    
    return {
        'jira_story': jira_story,
        'architect_plan': plan,
        'backend_results': backend_results,
        'frontend_results': frontend_results,
        'summary': {
            'backend_tasks': len(backend_tasks),
            'frontend_tasks': len(frontend_tasks),
            'backend_files': total_backend_files,
            'frontend_files': total_frontend_files,
            'federation_aware': len(federation_indicators) > 0
        }
    }

if __name__ == "__main__":
    asyncio.run(test_full_workflow()) 