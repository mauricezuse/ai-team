#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crewai_app.agents.frontend import FrontendAgent, frontend_openai
from crewai_app.utils.codebase_indexer import build_directory_tree, index_selected_files_async

def test_frontend_agent():
    print("Testing Frontend Agent...")
    
    # Create a simple task
    task = {
        'title': 'Create SearchFreelancersComponent',
        'description': 'Create Angular component for searching and displaying freelancers with filtering capabilities and featured freelancer highlighting',
        'acceptance_criteria': [
            'Component displays freelancer list with search functionality',
            'Supports filtering by skills, rate range, and location',
            'Featured freelancers are visually highlighted with distinct styling',
            'Responsive design works on all devices'
        ],
        'type': 'frontend'
    }
    
    # Create a simple plan
    plan = [
        {
            'title': 'Create SearchFreelancersComponent',
            'description': 'Create Angular component for searching and displaying freelancers',
            'acceptance_criteria': ['Component displays freelancer list'],
            'type': 'frontend'
        }
    ]
    
    # Create rules
    rules = {
        'frontend': {
            'framework': 'Angular',
            'style': 'Modern, responsive design',
            'patterns': 'Use Angular best practices'
        }
    }
    
    # Create a simple codebase index
    codebase_index = {
        'frontend/projects/freelancer/profile/src/app/app.module.ts': {
            'content': 'import { NgModule } from \'@angular/core\';',
            'summary': 'Angular app module'
        },
        'frontend/projects/freelancer/profile/src/app/app.component.ts': {
            'content': 'import { Component } from \'@angular/core\';',
            'summary': 'Main app component'
        }
    }
    
    # Initialize frontend agent
    frontend_agent = FrontendAgent(frontend_openai)
    
    print(f"Task: {task['title']}")
    print(f"Description: {task['description']}")
    print(f"Acceptance Criteria: {task['acceptance_criteria']}")
    print("\n" + "="*50)
    
    try:
        # Test the implement_task method
        result = frontend_agent.implement_task(
            task=task,
            plan=plan,
            rules=rules,
            codebase_index=codebase_index,
            checkpoint=None,
            save_checkpoint=None,
            branch=None,
            repo_root=None,
            api_contracts=None
        )
        
        print("✅ Frontend Agent Result:")
        print(f"Result type: {type(result)}")
        if isinstance(result, list):
            print(f"Number of files: {len(result)}")
            for i, file_entry in enumerate(result):
                print(f"\n--- File {i+1} ---")
                print(f"File: {file_entry.get('file', 'Unknown')}")
                print(f"Code length: {len(file_entry.get('code', ''))} characters")
                print(f"Code preview: {file_entry.get('code', '')[:200]}...")
        else:
            print(f"Result: {result}")
            
    except Exception as e:
        print(f"❌ Error testing frontend agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_frontend_agent() 