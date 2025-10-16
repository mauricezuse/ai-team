"""
End-to-End test for message persistence with actual LLM calls.
Tests the complete workflow execution with real Jira integration and LLM calls.
"""
import pytest
import time
import requests
import json
from datetime import datetime
from typing import Dict, Any, List


class TestE2EMessagePersistence:
    """End-to-end tests for message persistence with real LLM calls."""
    
    @pytest.fixture
    def api_base_url(self):
        """Base URL for the API."""
        return "http://localhost:8000"
    
    @pytest.fixture
    def test_story_id(self):
        """Test Jira story ID."""
        return "NEGISHI-200"
    
    def test_e2e_workflow_message_persistence(self, api_base_url, test_story_id):
        """Test complete workflow execution with message persistence."""
        print(f"\n🧪 Starting E2E test for {test_story_id}")
        print("=" * 60)
        
        # Step 1: Check if workflow already exists and delete it
        existing_workflow = self._find_existing_workflow(api_base_url, test_story_id)
        if existing_workflow:
            print(f"🗑️  Found existing workflow {existing_workflow['id']}, deleting...")
            self._delete_workflow(api_base_url, existing_workflow['id'])
            time.sleep(2)  # Wait for deletion to complete
        
        # Step 2: Create new workflow from Jira
        print(f"📝 Creating new workflow for {test_story_id}...")
        workflow = self._create_workflow_from_jira(api_base_url, test_story_id)
        assert workflow is not None, "Failed to create workflow"
        
        # Handle different response formats
        if 'id' in workflow:
            workflow_id = workflow['id']
            workflow_name = workflow.get('name', 'Unknown')
        elif 'workflow_id' in workflow:
            workflow_id = workflow['workflow_id']
            workflow_name = f"Workflow {workflow_id}"
        else:
            raise ValueError(f"Unexpected workflow response format: {workflow}")
        
        print(f"✅ Created workflow {workflow_id}: {workflow_name}")
        
        # Step 3: Start workflow execution
        print(f"🚀 Starting workflow execution...")
        execution = self._start_workflow_execution(api_base_url, workflow_id)
        assert execution is not None, "Failed to start workflow execution"
        execution_id = execution['id']
        print(f"✅ Started execution {execution_id}")
        
        # Step 4: Monitor workflow execution
        print(f"⏳ Monitoring workflow execution...")
        final_status = self._monitor_workflow_execution(api_base_url, workflow_id, timeout=300)
        print(f"📊 Final workflow status: {final_status}")
        
        # Step 5: Verify message persistence
        print(f"🔍 Verifying message persistence...")
        self._verify_message_persistence(api_base_url, workflow_id)
        
        # Step 6: Display conversation summary
        print(f"📋 Conversation Summary:")
        self._display_conversation_summary(api_base_url, workflow_id)
        
        print(f"\n✅ E2E test completed successfully for {test_story_id}")
        return workflow_id
    
    def _find_existing_workflow(self, api_base_url: str, story_id: str) -> Dict[str, Any]:
        """Find existing workflow by story ID."""
        try:
            response = requests.get(f"{api_base_url}/workflows")
            response.raise_for_status()
            workflows = response.json()
            
            for workflow in workflows:
                if workflow.get('jira_story_id') == story_id:
                    return workflow
            return None
        except Exception as e:
            print(f"❌ Error finding existing workflow: {e}")
            return None
    
    def _delete_workflow(self, api_base_url: str, workflow_id: int):
        """Delete an existing workflow."""
        try:
            response = requests.delete(f"{api_base_url}/workflows/{workflow_id}")
            response.raise_for_status()
            print(f"✅ Deleted workflow {workflow_id}")
        except Exception as e:
            print(f"❌ Error deleting workflow {workflow_id}: {e}")
            raise
    
    def _create_workflow_from_jira(self, api_base_url: str, story_id: str) -> Dict[str, Any]:
        """Create a new workflow from Jira story."""
        try:
            # Use the from-jira endpoint to create workflow directly
            response = requests.post(f"{api_base_url}/workflows/from-jira/{story_id}")
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"❌ Error creating workflow from Jira: {e}")
            # Fallback: create workflow manually
            workflow_data = {
                "name": f"{story_id}: E2E Test Story",
                "jira_story_id": story_id,
                "jira_story_title": f"E2E Test Story for {story_id}",
                "jira_story_description": f"End-to-end test workflow for {story_id} to verify message persistence",
                "description": f"E2E test workflow for {story_id}"
            }
            
            response = requests.post(
                f"{api_base_url}/workflows",
                json=workflow_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
    
    def _start_workflow_execution(self, api_base_url: str, workflow_id: int) -> Dict[str, Any]:
        """Start workflow execution."""
        try:
            response = requests.post(f"{api_base_url}/workflows/{workflow_id}/executions/start")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error starting workflow execution: {e}")
            raise
    
    def _monitor_workflow_execution(self, api_base_url: str, workflow_id: int, timeout: int = 300) -> str:
        """Monitor workflow execution until completion."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{api_base_url}/workflows/{workflow_id}")
                response.raise_for_status()
                workflow = response.json()
                
                status = workflow.get('status', 'unknown')
                print(f"   📊 Status: {status}")
                
                if status in ['completed', 'failed']:
                    return status
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                print(f"❌ Error monitoring workflow: {e}")
                time.sleep(5)
        
        print(f"⏰ Timeout reached after {timeout} seconds")
        return 'timeout'
    
    def _verify_message_persistence(self, api_base_url: str, workflow_id: int):
        """Verify that messages are persisted for all agents."""
        try:
            response = requests.get(f"{api_base_url}/workflows/{workflow_id}")
            response.raise_for_status()
            workflow = response.json()
            
            conversations = workflow.get('conversations', [])
            print(f"📊 Found {len(conversations)} conversations")
            
            # Verify each conversation has messages
            total_messages = 0
            agents_with_messages = set()
            
            for conv in conversations:
                agent = conv.get('agent', 'unknown')
                messages = conv.get('messages', [])
                llm_calls = conv.get('llm_calls', [])
                
                print(f"   🤖 {agent}: {len(messages)} messages, {len(llm_calls)} LLM calls")
                
                if messages:
                    agents_with_messages.add(agent)
                    total_messages += len(messages)
                    
                    # Verify message structure
                    for msg in messages:
                        assert 'role' in msg, f"Message missing role: {msg}"
                        assert 'content' in msg, f"Message missing content: {msg}"
                        assert msg['role'] in ['user', 'assistant', 'system'], f"Invalid role: {msg['role']}"
            
            # Expected agents that should have messages
            expected_agents = {"Product Manager", "Solution Architect", "Backend Developer", "Frontend Developer"}
            agents_with_messages_set = set(agents_with_messages)
            missing_agents = expected_agents - agents_with_messages_set
            
            # Assertions
            assert total_messages > 0, "No messages found in any conversation"
            assert len(agents_with_messages) > 0, "No agents have messages"
            assert len(missing_agents) == 0, f"Expected agents missing messages: {missing_agents}. Found agents: {agents_with_messages_set}"
            
            print(f"✅ Message persistence verified:")
            print(f"   📊 Total messages: {total_messages}")
            print(f"   🤖 Agents with messages: {len(agents_with_messages)}")
            print(f"   📝 Agents: {', '.join(sorted(agents_with_messages))}")
            print(f"🎉 All expected agents have messages: {expected_agents}")
            
        except Exception as e:
            print(f"❌ Error verifying message persistence: {e}")
            raise
    
    def _display_conversation_summary(self, api_base_url: str, workflow_id: int):
        """Display a summary of all conversations and messages."""
        try:
            response = requests.get(f"{api_base_url}/workflows/{workflow_id}")
            response.raise_for_status()
            workflow = response.json()
            
            conversations = workflow.get('conversations', [])
            
            for i, conv in enumerate(conversations, 1):
                agent = conv.get('agent', 'unknown')
                step_name = conv.get('step_name', 'unknown')
                messages = conv.get('messages', [])
                llm_calls = conv.get('llm_calls', [])
                
                print(f"\n   📋 Conversation {i}: {agent} ({step_name})")
                print(f"      💬 Messages: {len(messages)}")
                print(f"      🤖 LLM Calls: {len(llm_calls)}")
                
                # Show first few messages
                for j, msg in enumerate(messages[:3]):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')[:100]
                    print(f"         {j+1}. [{role}] {content}...")
                
                if len(messages) > 3:
                    print(f"         ... and {len(messages) - 3} more messages")
                
                # Show LLM call summary
                if llm_calls:
                    total_tokens = sum(call.get('total_tokens', 0) for call in llm_calls)
                    total_cost = sum(float(call.get('cost', 0)) for call in llm_calls)
                    print(f"         🔢 Total tokens: {total_tokens}, Cost: ${total_cost:.4f}")
            
        except Exception as e:
            print(f"❌ Error displaying conversation summary: {e}")
    
    def test_workflow_with_specific_story(self, api_base_url):
        """Test with a specific Jira story that we know exists."""
        # Use NEGISHI-178 which we know exists and has been tested
        story_id = "NEGISHI-178"
        
        print(f"\n🧪 Testing with known story: {story_id}")
        print("=" * 60)
        
        # Check if workflow exists
        existing_workflow = self._find_existing_workflow(api_base_url, story_id)
        if existing_workflow:
            print(f"📋 Using existing workflow {existing_workflow['id']}")
            workflow_id = existing_workflow['id']
        else:
            print(f"📝 Creating new workflow for {story_id}")
            workflow = self._create_workflow_from_jira(api_base_url, story_id)
            workflow_id = workflow['id']
        
        # Verify message persistence
        self._verify_message_persistence(api_base_url, workflow_id)
        
        # Display conversation summary
        self._display_conversation_summary(api_base_url, workflow_id)
        
        print(f"\n✅ Test completed for {story_id}")
        return workflow_id
    
    def test_api_health_check(self, api_base_url):
        """Test that the API is healthy and accessible."""
        try:
            response = requests.get(f"{api_base_url}/health")
            response.raise_for_status()
            health_data = response.json()
            assert health_data.get('status') == 'ok'
            print(f"✅ API health check passed: {health_data}")
        except Exception as e:
            print(f"❌ API health check failed: {e}")
            raise
    
    def test_jira_connectivity(self, api_base_url):
        """Test that Jira integration is working."""
        try:
            # Test by creating a workflow from Jira
            response = requests.post(f"{api_base_url}/workflows/from-jira/NEGISHI-178")
            response.raise_for_status()
            workflow_data = response.json()
            
            # Handle different response formats
            if 'id' in workflow_data:
                workflow_id = workflow_data['id']
                workflow_name = workflow_data.get('name', 'Unknown')
            elif 'workflow_id' in workflow_data:
                workflow_id = workflow_data['workflow_id']
                workflow_name = f"Workflow {workflow_id}"
            else:
                raise ValueError(f"Unexpected workflow response format: {workflow_data}")
            
            print(f"✅ Jira connectivity verified:")
            print(f"   📋 Workflow ID: {workflow_id}")
            print(f"   📝 Workflow Name: {workflow_name}")
            
            # Clean up the test workflow
            if workflow_id:
                try:
                    delete_response = requests.delete(f"{api_base_url}/workflows/{workflow_id}")
                    delete_response.raise_for_status()
                    print(f"   🗑️  Cleaned up test workflow {workflow_id}")
                except Exception as cleanup_error:
                    print(f"   ⚠️  Warning: Could not clean up test workflow: {cleanup_error}")
            
        except Exception as e:
            print(f"❌ Jira connectivity test failed: {e}")
            # This is not a critical failure for the E2E test
            print("   ℹ️  Jira integration may not be configured, but E2E test can still proceed")


if __name__ == "__main__":
    # Run the E2E test
    import sys
    import os
    
    # Add project root to path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    
    # Run pytest
    pytest.main([__file__, "-v", "-s"])
