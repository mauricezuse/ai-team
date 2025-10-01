#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crewai_app.agents.frontend import FrontendAgent
from crewai_app.services.openai_service import OpenAIService

def test_intelligent_modifications():
    print("Testing Intelligent File Modifications...")
    
    # Create a simple task that should modify existing files
    task = {
        'title': 'Add Search Functionality to Existing Component',
        'description': 'Add search and filtering capabilities to an existing Angular component',
        'acceptance_criteria': [
            'Component has search input field',
            'Component supports filtering by skills',
            'Component displays filtered results'
        ],
        'type': 'frontend'
    }
    
    # Create a simple plan
    plan = [
        {
            'title': 'Extend Existing Component',
            'description': 'Add search functionality to existing component',
            'acceptance_criteria': ['Component has search capabilities'],
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
    
    # Create a codebase index with existing files
    codebase_index = {
        'frontend/projects/freelancer/profile/src/app/app.module.ts': {
            'content': 'import { NgModule } from \'@angular/core\';\nimport { BrowserModule } from \'@angular/platform-browser\';\nimport { AppComponent } from \'./app.component\';\n\n@NgModule({\n  declarations: [\n    AppComponent\n  ],\n  imports: [\n    BrowserModule\n  ],\n  providers: [],\n  bootstrap: [AppComponent]\n})\nexport class AppModule { }',
            'summary': 'Angular app module'
        },
        'frontend/projects/freelancer/profile/src/app/app.component.ts': {
            'content': 'import { Component } from \'@angular/core\';\n\n@Component({\n  selector: \'app-root\',\n  templateUrl: \'./app.component.html\',\n  styleUrls: [\'./app.component.scss\']\n})\nexport class AppComponent {\n  title = \'Freelancer Platform\';\n}',
            'summary': 'Main app component'
        }
    }
    
    print("Testing Frontend Agent with existing files...")
    
    # Initialize frontend agent with OpenAI service
    openai_service = OpenAIService()
    frontend_agent = FrontendAgent(openai_service)
    
    try:
        # Test modifying an existing file
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
                print(f"Code preview: {file_entry.get('code', '')[:300]}...")
                
                # Check if it's an intelligent modification
                code = file_entry.get('code', '')
                if 'import { Component }' in code and 'export class AppComponent' in code:
                    print("✅ INTELLIGENT MODIFICATION: Preserved existing component structure")
                elif 'import { Component }' in code:
                    print("✅ INTELLIGENT MODIFICATION: Preserved existing imports")
                else:
                    print("❌ REPLACEMENT: Completely replaced file content")
        else:
            print(f"Result: {result}")
            
    except Exception as e:
        print(f"❌ Error testing frontend agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_intelligent_modifications() 