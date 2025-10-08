#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crewai_app.agents.frontend import FrontendAgent
from crewai_app.services.openai_service import OpenAIService

def test_federation_awareness():
    print("Testing Frontend Agent Federation Awareness...")
    
    # Create a task that should create a component in the federated profile module
    task = {
        'title': 'Create Featured Freelancers Component in Profile Module',
        'description': 'Create a component to display featured freelancers in the federated profile module',
        'acceptance_criteria': [
            'Component displays featured freelancers list',
            'Component is properly exposed in federation.config.js',
            'Component follows micro-frontend best practices'
        ],
        'type': 'frontend'
    }
    
    # Create a simple plan
    plan = [
        {
            'title': 'Create Federated Component',
            'description': 'Create component in profile module with federation exposure',
            'acceptance_criteria': ['Component is federated correctly'],
            'type': 'frontend'
        }
    ]
    
    # Create rules
    rules = {
        'frontend': {
            'framework': 'Angular Native Federation',
            'style': 'Modern, responsive design',
            'patterns': 'Use micro-frontend best practices'
        }
    }
    
    # Create a codebase index with federation-aware files
    codebase_index = {
        'negishi-freelancing/frontend/projects/freelancer/profile/federation.config.js': {
            'content': 'module.exports = withNativeFederation({\n  name: "profile",\n  exposes: {\n    "./Component": "./projects/freelancer/profile/src/app/app.component.ts",\n    "./Routes": "./projects/freelancer/profile/src/app/app.routes.ts"\n  }\n});',
            'summary': 'Profile module federation configuration'
        },
        'negishi-freelancing/frontend/projects/freelancer/profile/src/app/app.component.ts': {
            'content': 'import { Component } from \'@angular/core\';\n\n@Component({\n  selector: \'app-root\',\n  templateUrl: \'./app.component.html\',\n  styleUrls: [\'./app.component.scss\']\n})\nexport class AppComponent {\n  title = \'Freelancer Platform\';\n}',
            'summary': 'Main app component in profile module'
        },
        'negishi-freelancing/frontend/projects/shell/federation.config.js': {
            'content': 'module.exports = withNativeFederation({\n  shared: {\n    ...shareAll({\n      singleton: true,\n      strictVersion: false,\n      requiredVersion: "auto",\n    })\n  }\n});',
            'summary': 'Shell application federation configuration'
        }
    }
    
    print("Testing Frontend Agent with Federation Awareness...")
    
    # Initialize frontend agent with OpenAI service
    openai_service = OpenAIService()
    frontend_agent = FrontendAgent(openai_service)
    
    try:
        # Test creating a component in the federated profile module
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
        
        print("✅ Frontend Agent Federation-Aware Result:")
        print(f"Result type: {type(result)}")
        if isinstance(result, list):
            print(f"Number of files: {len(result)}")
            for i, file_entry in enumerate(result):
                print(f"\n--- File {i+1} ---")
                print(f"File: {file_entry.get('file', 'Unknown')}")
                print(f"Code length: {len(file_entry.get('code', ''))} characters")
                print(f"Code preview: {file_entry.get('code', '')[:500]}...")
                
                # Check for federation awareness
                code = file_entry.get('code', '')
                file_path = file_entry.get('file', '')
                
                if 'federation' in code.lower() or 'loadRemoteModule' in code:
                    print("✅ FEDERATION AWARE: Code includes federation considerations")
                elif 'profile' in file_path and 'component' in file_path:
                    print("✅ FEDERATION AWARE: Creating component in federated profile module")
                elif 'shell' in file_path:
                    print("✅ FEDERATION AWARE: Working with shell application")
                else:
                    print("❓ FEDERATION AWARENESS: Not clear if federation-aware")
        else:
            print(f"Result: {result}")
            
    except Exception as e:
        print(f"❌ Error testing frontend agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_federation_awareness() 