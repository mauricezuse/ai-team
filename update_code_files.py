#!/usr/bin/env python3
"""
Script to update existing conversations with code files
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crewai_app.database import get_db, Conversation, CodeFile, Workflow

def update_conversations_with_code_files():
    """Update existing conversations with code files based on their steps"""
    
    # Get database session
    db = next(get_db())
    
    # Get workflow 12 (NEGISHI-165)
    workflow = db.query(Workflow).filter(Workflow.id == 12).first()
    if not workflow:
        print("Workflow 12 not found")
        return
    
    print(f"Updating conversations for workflow: {workflow.name}")
    
    # Get all conversations for this workflow
    conversations = db.query(Conversation).filter(Conversation.workflow_id == 12).all()
    
    # Step to code files mapping
    step_code_files = {
        'story_retrieved_and_analyzed': [],
        'codebase_indexed': [],
        'implementation_plan_generated': ['docs/architecture/implementation-plan.md'],
        'tasks_broken_down_with_collaboration': ['docs/tasks/task-breakdown.md'],
        'tasks_executed_with_escalation': ['backend/routes/job_offer.py', 'backend/models/job_offer.py'],
        'frontend_implementation': ['frontend/src/app/features/job-offers/job-offers-list.component.ts', 'frontend/src/app/features/job-offers/job-offer-detail.component.ts'],
        'pr_skipped': [],
        'final_review_and_testing_completed': ['tests/test_job_offer.py', 'tests/e2e/job-offer.spec.ts']
    }
    
    for conversation in conversations:
        print(f"Processing conversation: {conversation.step}")
        
        # Check if conversation already has code files
        existing_files = db.query(CodeFile).filter(CodeFile.conversation_id == conversation.id).all()
        if existing_files:
            print(f"  Conversation {conversation.id} already has {len(existing_files)} code files")
            continue
        
        # Add code files based on step
        code_files = step_code_files.get(conversation.step, [])
        for file_path in code_files:
            code_file = CodeFile(
                workflow_id=conversation.workflow_id,
                conversation_id=conversation.id,
                filename=file_path.split('/')[-1],
                file_path=file_path,
                file_type='generated'
            )
            db.add(code_file)
            print(f"  Added code file: {file_path}")
    
    # Commit changes
    db.commit()
    print("Code files added successfully!")

if __name__ == "__main__":
    update_conversations_with_code_files()
