#!/usr/bin/env python3
"""
Script to add sample LLM call data to existing conversations
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crewai_app.database import get_db, Conversation, LLMCall
from datetime import datetime
import json

def add_sample_llm_calls():
    """Add sample LLM call data to existing conversations"""
    
    # Get database session
    db = next(get_db())
    
    # Get workflow 12 (NEGISHI-165)
    conversations = db.query(Conversation).filter(Conversation.workflow_id == 12).all()
    
    print(f"Found {len(conversations)} conversations to update")
    
    # Sample LLM call data for different agents (using actual database agent names)
    sample_llm_calls = {
        'pm': [
            {
                'model': 'gpt-4',
                'prompt_tokens': 150,
                'completion_tokens': 200,
                'total_tokens': 350,
                'cost': '0.0105',
                'response_time_ms': 1200,
                'timestamp': datetime.utcnow().isoformat(),
                'request_data': {
                    'messages': [
                        {'role': 'system', 'content': 'You are a Product Manager analyzing user stories...'},
                        {'role': 'user', 'content': 'Analyze the NEGISHI-165 story requirements...'}
                    ]
                },
                'response_data': {
                    'content': 'Based on the story analysis, I have identified key requirements...',
                    'usage': {'prompt_tokens': 150, 'completion_tokens': 200, 'total_tokens': 350}
                }
            }
        ],
        'architect': [
            {
                'model': 'gpt-4',
                'prompt_tokens': 200,
                'completion_tokens': 300,
                'total_tokens': 500,
                'cost': '0.0150',
                'response_time_ms': 1800,
                'timestamp': datetime.utcnow().isoformat(),
                'request_data': {
                    'messages': [
                        {'role': 'system', 'content': 'You are a Solution Architect designing system architecture...'},
                        {'role': 'user', 'content': 'Create a comprehensive implementation plan...'}
                    ]
                },
                'response_data': {
                    'content': 'Here is the implementation plan with clear steps...',
                    'usage': {'prompt_tokens': 200, 'completion_tokens': 300, 'total_tokens': 500}
                }
            }
        ],
        'developer': [
            {
                'model': 'gpt-4',
                'prompt_tokens': 180,
                'completion_tokens': 250,
                'total_tokens': 430,
                'cost': '0.0129',
                'response_time_ms': 1500,
                'timestamp': datetime.utcnow().isoformat(),
                'request_data': {
                    'messages': [
                        {'role': 'system', 'content': 'You are a Backend Developer implementing APIs...'},
                        {'role': 'user', 'content': 'Implement the backend functionality for job offers...'}
                    ]
                },
                'response_data': {
                    'content': 'I have implemented the backend API endpoints...',
                    'usage': {'prompt_tokens': 180, 'completion_tokens': 250, 'total_tokens': 430}
                }
            }
        ],
        'frontend': [
            {
                'model': 'gpt-4',
                'prompt_tokens': 160,
                'completion_tokens': 220,
                'total_tokens': 380,
                'cost': '0.0114',
                'response_time_ms': 1400,
                'timestamp': datetime.utcnow().isoformat(),
                'request_data': {
                    'messages': [
                        {'role': 'system', 'content': 'You are a Frontend Developer creating user interfaces...'},
                        {'role': 'user', 'content': 'Implement the user interface for job offer viewing...'}
                    ]
                },
                'response_data': {
                    'content': 'I have created the frontend components for job offer display...',
                    'usage': {'prompt_tokens': 160, 'completion_tokens': 220, 'total_tokens': 380}
                }
            }
        ],
        'tester': [
            {
                'model': 'gpt-4',
                'prompt_tokens': 140,
                'completion_tokens': 180,
                'total_tokens': 320,
                'cost': '0.0096',
                'response_time_ms': 1100,
                'timestamp': datetime.utcnow().isoformat(),
                'request_data': {
                    'messages': [
                        {'role': 'system', 'content': 'You are a QA Tester creating comprehensive tests...'},
                        {'role': 'user', 'content': 'Create tests for the job offer functionality...'}
                    ]
                },
                'response_data': {
                    'content': 'I have created comprehensive test cases covering...',
                    'usage': {'prompt_tokens': 140, 'completion_tokens': 180, 'total_tokens': 320}
                }
            }
        ]
    }
    
    for conversation in conversations:
        print(f"Updating conversation: {conversation.step} ({conversation.agent})")
        
        # Get sample LLM calls for this agent
        agent_calls = sample_llm_calls.get(conversation.agent, [])
        
        if agent_calls:
            # Update conversation with LLM call data
            conversation.llm_calls = agent_calls
            conversation.total_tokens_used = sum(call['total_tokens'] for call in agent_calls)
            conversation.total_cost = f"{sum(float(call['cost']) for call in agent_calls):.4f}"
            
            # Create LLMCall records
            for call_data in agent_calls:
                llm_call = LLMCall(
                    conversation_id=conversation.id,
                    model=call_data['model'],
                    prompt_tokens=call_data['prompt_tokens'],
                    completion_tokens=call_data['completion_tokens'],
                    total_tokens=call_data['total_tokens'],
                    cost=call_data['cost'],
                    response_time_ms=call_data['response_time_ms'],
                    request_data=call_data['request_data'],
                    response_data=call_data['response_data']
                )
                db.add(llm_call)
            
            print(f"  Added {len(agent_calls)} LLM calls, {conversation.total_tokens_used} tokens, ${conversation.total_cost}")
    
    # Commit changes
    db.commit()
    print("LLM call data added successfully!")

if __name__ == "__main__":
    add_sample_llm_calls()
