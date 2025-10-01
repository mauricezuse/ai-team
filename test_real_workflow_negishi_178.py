#!/usr/bin/env python3
"""
Real Workflow Test with NEGISHI-178
Tests the complete workflow from story analysis to implementation
Goal: Generate a perfect PR with federation-aware agents
"""

import asyncio
import logging
import json
from datetime import datetime
from crewai_app.agents.architect import ArchitectAgent
from crewai_app.agents.developer import DeveloperAgent as BackendAgent
from crewai_app.agents.frontend import FrontendAgent
from crewai_app.services.openai_service import OpenAIService
from crewai_app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_real_workflow_negishi_178():
    """Test the complete real workflow with NEGISHI-178"""
    
    print("🚀 Starting Real Workflow Test with NEGISHI-178")
    print("=" * 60)
    
    # Real NEGISHI-178 story from Jira
    jira_story = {
        "key": "NEGISHI-178",
        "summary": "Implement Featured Freelancers Feature",
        "description": "As a client, I want to see featured freelancers prominently displayed so that I can quickly find high-quality talent for my projects.",
        "acceptance_criteria": [
            "Featured freelancers are displayed prominently on the homepage",
            "Featured freelancers have a special badge or indicator",
            "Featured freelancers are sorted by relevance and rating",
            "The feature is accessible and responsive on all devices",
            "Featured freelancers can be filtered by skills and location",
            "The implementation follows micro-frontend architecture"
        ],
        "story_points": 8,
        "priority": "High",
        "labels": ["feature", "frontend", "backend", "federation"]
    }
    
    print(f"📋 Story: {jira_story['key']} - {jira_story['summary']}")
    print(f"📝 Description: {jira_story['description']}")
    print(f"✅ Acceptance Criteria: {len(jira_story['acceptance_criteria'])} items")
    print()
    
    # Wrap story for architect compatibility
    story = {"fields": jira_story}
    
    try:
        # Step 1: Architect Analysis and Planning
        print("🏗️  Step 1: Architect Analysis and Planning")
        print("-" * 50)
        
        architect_openai = OpenAIService(deployment=settings.deployment_architect)
        architect = ArchitectAgent(architect_openai)
        
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
        
        # Display tasks
        for i, task in enumerate(backend_tasks + frontend_tasks, 1):
            task_type = "🔧 Backend" if task in backend_tasks else "🎨 Frontend"
            print(f"   {i}. [{task_type}] {task.get('title', 'Unknown Task')}")
        print()
        
        # Step 2: Backend Implementation
        print("⚙️  Step 2: Backend Implementation")
        print("-" * 50)
        
        backend_openai = OpenAIService(deployment=settings.deployment_developer)
        backend_agent = BackendAgent(backend_openai)
        
        backend_results = []
        for i, task in enumerate(backend_tasks, 1):
            print(f"   {i}. Implementing: {task.get('title', 'Unknown Task')}")
            try:
                result = backend_agent.implement_task(task, plan, None, selected_index)
                backend_results.append(result)
                print(f"      ✅ Completed - {len(result)} files created/modified")
            except Exception as e:
                print(f"      ❌ Failed: {str(e)}")
        print()
        
        # Step 3: Frontend Implementation
        print("🎨 Step 3: Frontend Implementation")
        print("-" * 50)
        
        frontend_openai = OpenAIService(deployment=settings.deployment_frontend)
        frontend_agent = FrontendAgent(frontend_openai)
        
        frontend_results = []
        for i, task in enumerate(frontend_tasks, 1):
            print(f"   {i}. Implementing: {task.get('title', 'Unknown Task')}")
            try:
                result = frontend_agent.implement_task(task, plan, None, selected_index)
                frontend_results.append(result)
                print(f"      ✅ Completed - {len(result)} files created/modified")
            except Exception as e:
                print(f"      ❌ Failed: {str(e)}")
        print()
        
        # Step 4: Results Summary
        print("📊 Step 4: Implementation Results Summary")
        print("-" * 50)
        
        total_backend_files = sum(len(result) for result in backend_results)
        total_frontend_files = sum(len(result) for result in frontend_results)
        total_files = total_backend_files + total_frontend_files
        
        print(f"✅ Backend Implementation:")
        print(f"   - Tasks Completed: {len(backend_results)}/{len(backend_tasks)}")
        print(f"   - Files Created/Modified: {total_backend_files}")
        
        print(f"✅ Frontend Implementation:")
        print(f"   - Tasks Completed: {len(frontend_results)}/{len(frontend_tasks)}")
        print(f"   - Files Created/Modified: {total_frontend_files}")
        
        print(f"📁 Total Files Generated: {total_files}")
        print()
        
        # Step 5: Federation Awareness Check
        print("🔗 Step 5: Federation Architecture Validation")
        print("-" * 50)
        
        federation_indicators = []
        
        # Check for federation config updates
        if total_frontend_files > 0:
            federation_indicators.append("✅ Frontend components generated")
        
        # Check for proper module structure
        if any("federation" in str(result).lower() for result in frontend_results):
            federation_indicators.append("✅ Federation configuration detected")
        
        # Check for micro-frontend patterns
        if any("profile" in str(result).lower() or "shell" in str(result).lower() for result in frontend_results):
            federation_indicators.append("✅ Micro-frontend architecture patterns detected")
        
        for indicator in federation_indicators:
            print(f"   {indicator}")
        
        if not federation_indicators:
            print("   ⚠️  No federation indicators detected")
        print()
        
        # Step 6: PR Readiness Assessment
        print("🚀 Step 6: PR Readiness Assessment")
        print("-" * 50)
        
        success_rate = ((len(backend_results) + len(frontend_results)) / 
                       (len(backend_tasks) + len(frontend_tasks))) * 100
        
        if success_rate >= 90:
            print("   🎉 EXCELLENT: High success rate - PR ready!")
        elif success_rate >= 70:
            print("   ✅ GOOD: Moderate success rate - PR mostly ready")
        else:
            print("   ⚠️  NEEDS WORK: Low success rate - PR needs improvement")
        
        print(f"   📈 Success Rate: {success_rate:.1f}%")
        print(f"   📁 Total Files: {total_files}")
        print(f"   🔧 Backend Tasks: {len(backend_results)}/{len(backend_tasks)}")
        print(f"   🎨 Frontend Tasks: {len(frontend_results)}/{len(frontend_tasks)}")
        
        if total_files > 0:
            print("   ✅ Files generated successfully")
        else:
            print("   ❌ No files generated")
        
        print()
        print("🎯 Workflow Test Complete!")
        
    except Exception as e:
        print(f"❌ Workflow failed: {str(e)}")
        logger.error(f"Workflow error: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_real_workflow_negishi_178()) 