import pytest
import json
import os
import tempfile
from unittest.mock import patch, mock_open
from fastapi.testclient import TestClient
from crewai_app.main import app

client = TestClient(app)

class TestWorkflowDataParsing:
    """Tests for workflow data parsing and error handling."""

    @pytest.fixture(scope="module")
    def workflow_results_dir(self):
        """Fixture to create a temporary directory for workflow results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_dir = os.environ.get("WORKFLOW_RESULTS_DIR")
            os.environ["WORKFLOW_RESULTS_DIR"] = tmpdir
            yield tmpdir
            if original_dir:
                os.environ["WORKFLOW_RESULTS_DIR"] = original_dir
            else:
                del os.environ["WORKFLOW_RESULTS_DIR"]

    def test_workflow_data_with_valid_structure(self, workflow_results_dir):
        """Test parsing workflow data with valid structure."""
        valid_data = {
            "workflow_log": [
                {
                    "step": "story_retrieved",
                    "timestamp": "2024-07-20T10:00:05.000Z",
                    "agent": "pm",
                    "status": "completed",
                    "details": "Story retrieved successfully",
                    "output": "Story details",
                    "code_files": ["file1.py"],
                    "escalations": [],
                    "collaborations": []
                }
            ],
            "timestamp": "2024-07-20T10:00:00.000Z",
            "collaboration_queue": [],
            "escalation_queue": []
        }
        
        file_path = os.path.join(workflow_results_dir, "test_workflow_checkpoint.json")
        with open(file_path, 'w') as f:
            json.dump(valid_data, f)

        with patch('os.path.exists', return_value=True), \
             patch('glob.glob', return_value=[file_path]), \
             patch('builtins.open', mock_open(read_data=json.dumps(valid_data))):
            
            response = client.get("/workflows")
            assert response.status_code == 200
            workflows = response.json()
            assert len(workflows) == 1
            assert workflows[0]["id"] == "test_workflow"
            assert workflows[0]["status"] == "completed"
            assert "pm" in workflows[0]["agents"]

    def test_workflow_data_with_list_workflow_log(self, workflow_results_dir):
        """Test parsing workflow data where workflow_log is a list of strings."""
        list_data = {
            "workflow_log": ["step1", "step2", "step3"],
            "timestamp": "2024-07-20T10:00:00.000Z"
        }
        
        file_path = os.path.join(workflow_results_dir, "list_workflow_checkpoint.json")
        with open(file_path, 'w') as f:
            json.dump(list_data, f)

        with patch('os.path.exists', return_value=True), \
             patch('glob.glob', return_value=[file_path]), \
             patch('builtins.open', mock_open(read_data=json.dumps(list_data))):
            
            response = client.get("/workflows")
            assert response.status_code == 200
            workflows = response.json()
            assert len(workflows) == 1
            assert workflows[0]["status"] == "completed"
            assert workflows[0]["agents"] == []

    def test_workflow_data_with_empty_workflow_log(self, workflow_results_dir):
        """Test parsing workflow data with empty workflow_log."""
        empty_data = {
            "workflow_log": [],
            "timestamp": "2024-07-20T10:00:00.000Z"
        }
        
        file_path = os.path.join(workflow_results_dir, "empty_workflow_checkpoint.json")
        with open(file_path, 'w') as f:
            json.dump(empty_data, f)

        with patch('os.path.exists', return_value=True), \
             patch('glob.glob', return_value=[file_path]), \
             patch('builtins.open', mock_open(read_data=json.dumps(empty_data))):
            
            response = client.get("/workflows")
            assert response.status_code == 200
            workflows = response.json()
            assert len(workflows) == 1
            assert workflows[0]["status"] == "pending"
            assert workflows[0]["agents"] == []

    def test_workflow_data_with_missing_workflow_log(self, workflow_results_dir):
        """Test parsing workflow data with missing workflow_log field."""
        missing_data = {
            "timestamp": "2024-07-20T10:00:00.000Z"
        }
        
        file_path = os.path.join(workflow_results_dir, "missing_workflow_checkpoint.json")
        with open(file_path, 'w') as f:
            json.dump(missing_data, f)

        with patch('os.path.exists', return_value=True), \
             patch('glob.glob', return_value=[file_path]), \
             patch('builtins.open', mock_open(read_data=json.dumps(missing_data))):
            
            response = client.get("/workflows")
            assert response.status_code == 200
            workflows = response.json()
            assert len(workflows) == 1
            assert workflows[0]["status"] == "pending"
            assert workflows[0]["agents"] == []

    def test_workflow_data_with_mixed_workflow_log(self, workflow_results_dir):
        """Test parsing workflow data with mixed content in workflow_log."""
        mixed_data = {
            "workflow_log": [
                {
                    "step": "story_retrieved",
                    "agent": "pm",
                    "status": "completed"
                },
                "invalid_entry",
                {
                    "step": "architect_plan",
                    "agent": "architect",
                    "status": "completed"
                }
            ],
            "timestamp": "2024-07-20T10:00:00.000Z"
        }
        
        file_path = os.path.join(workflow_results_dir, "mixed_workflow_checkpoint.json")
        with open(file_path, 'w') as f:
            json.dump(mixed_data, f)

        with patch('os.path.exists', return_value=True), \
             patch('glob.glob', return_value=[file_path]), \
             patch('builtins.open', mock_open(read_data=json.dumps(mixed_data))):
            
            response = client.get("/workflows")
            assert response.status_code == 200
            workflows = response.json()
            assert len(workflows) == 1
            assert workflows[0]["status"] == "completed"
            assert set(workflows[0]["agents"]) == {"pm", "architect"}

    def test_workflow_data_with_non_dict_entries(self, workflow_results_dir):
        """Test parsing workflow data with non-dict entries in workflow_log."""
        non_dict_data = {
            "workflow_log": [
                "step1",
                {"step": "step2", "agent": "pm"},
                None,
                {"step": "step3", "agent": "architect"}
            ],
            "timestamp": "2024-07-20T10:00:00.000Z"
        }
        
        file_path = os.path.join(workflow_results_dir, "non_dict_workflow_checkpoint.json")
        with open(file_path, 'w') as f:
            json.dump(non_dict_data, f)

        with patch('os.path.exists', return_value=True), \
             patch('glob.glob', return_value=[file_path]), \
             patch('builtins.open', mock_open(read_data=json.dumps(non_dict_data))):
            
            response = client.get("/workflows")
            assert response.status_code == 200
            workflows = response.json()
            assert len(workflows) == 1
            assert workflows[0]["status"] == "completed"
            assert set(workflows[0]["agents"]) == {"pm", "architect"}

    def test_workflow_data_with_corrupted_json(self, workflow_results_dir):
        """Test handling of corrupted JSON files."""
        corrupted_file = os.path.join(workflow_results_dir, "corrupted_workflow_checkpoint.json")
        with open(corrupted_file, 'w') as f:
            f.write('{"invalid": json}')  # Invalid JSON

        with patch('os.path.exists', return_value=True), \
             patch('glob.glob', return_value=[corrupted_file]):
            
            response = client.get("/workflows")
            assert response.status_code == 200
            workflows = response.json()
            assert len(workflows) == 0  # Corrupted file should be skipped

    def test_workflow_data_with_malformed_structure(self, workflow_results_dir):
        """Test handling of malformed workflow data structure."""
        malformed_data = {
            "workflow_log": "not_a_list",
            "timestamp": "2024-07-20T10:00:00.000Z"
        }
        
        file_path = os.path.join(workflow_results_dir, "malformed_workflow_checkpoint.json")
        with open(file_path, 'w') as f:
            json.dump(malformed_data, f)

        with patch('os.path.exists', return_value=True), \
             patch('glob.glob', return_value=[file_path]), \
             patch('builtins.open', mock_open(read_data=json.dumps(malformed_data))):
            
            response = client.get("/workflows")
            assert response.status_code == 200
            workflows = response.json()
            assert len(workflows) == 1
            assert workflows[0]["status"] == "pending"  # Should default to pending for malformed data

    def test_workflow_detail_parsing(self, workflow_results_dir):
        """Test parsing workflow detail with various data structures."""
        detail_data = {
            "workflow_log": [
                {
                    "step": "story_retrieved",
                    "timestamp": "2024-07-20T10:00:05.000Z",
                    "agent": "pm",
                    "status": "completed",
                    "details": "Story retrieved successfully",
                    "output": "Story details",
                    "code_files": ["file1.py", "file2.py"],
                    "escalations": [
                        {
                            "from_agent": "pm",
                            "to_agent": "architect",
                            "reason": "Complex requirements",
                            "status": "resolved"
                        }
                    ],
                    "collaborations": [
                        {
                            "from_agent": "pm",
                            "to_agent": "developer",
                            "request_type": "Clarification",
                            "status": "pending"
                        }
                    ]
                }
            ],
            "timestamp": "2024-07-20T10:00:00.000Z",
            "collaboration_queue": [],
            "escalation_queue": []
        }
        
        file_path = os.path.join(workflow_results_dir, "detail_workflow_checkpoint.json")
        with open(file_path, 'w') as f:
            json.dump(detail_data, f)

        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(detail_data))):
            
            response = client.get("/workflows/detail_workflow")
            assert response.status_code == 200
            workflow = response.json()
            assert workflow["id"] == "detail_workflow"
            assert len(workflow["conversations"]) == 1
            
            conversation = workflow["conversations"][0]
            assert conversation["agent"] == "pm"
            assert conversation["step"] == "story_retrieved"
            assert len(conversation["code_files"]) == 2
            assert len(conversation["escalations"]) == 1
            assert len(conversation["collaborations"]) == 1
            assert conversation["escalations"][0]["reason"] == "Complex requirements"
            assert conversation["collaborations"][0]["request_type"] == "Clarification"

    def test_workflow_detail_with_mixed_data(self, workflow_results_dir):
        """Test parsing workflow detail with mixed valid and invalid entries."""
        mixed_detail_data = {
            "workflow_log": [
                {
                    "step": "story_retrieved",
                    "agent": "pm",
                    "status": "completed"
                },
                "invalid_entry",
                {
                    "step": "architect_plan",
                    "agent": "architect",
                    "status": "completed",
                    "details": "Plan generated"
                }
            ],
            "timestamp": "2024-07-20T10:00:00.000Z",
            "collaboration_queue": [],
            "escalation_queue": []
        }
        
        file_path = os.path.join(workflow_results_dir, "mixed_detail_workflow_checkpoint.json")
        with open(file_path, 'w') as f:
            json.dump(mixed_detail_data, f)

        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(mixed_detail_data))):
            
            response = client.get("/workflows/mixed_detail_workflow")
            assert response.status_code == 200
            workflow = response.json()
            assert len(workflow["conversations"]) == 2  # Only valid entries should be included
            assert workflow["conversations"][0]["agent"] == "pm"
            assert workflow["conversations"][1]["agent"] == "architect"

    def test_workflow_detail_with_missing_fields(self, workflow_results_dir):
        """Test parsing workflow detail with missing optional fields."""
        minimal_data = {
            "workflow_log": [
                {
                    "step": "story_retrieved",
                    "agent": "pm"
                    # Missing timestamp, status, details, etc.
                }
            ],
            "timestamp": "2024-07-20T10:00:00.000Z"
        }
        
        file_path = os.path.join(workflow_results_dir, "minimal_workflow_checkpoint.json")
        with open(file_path, 'w') as f:
            json.dump(minimal_data, f)

        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(minimal_data))):
            
            response = client.get("/workflows/minimal_workflow")
            assert response.status_code == 200
            workflow = response.json()
            assert len(workflow["conversations"]) == 1
            
            conversation = workflow["conversations"][0]
            assert conversation["agent"] == "pm"
            assert conversation["step"] == "story_retrieved"
            assert conversation["timestamp"] == ""  # Should default to empty string
            assert conversation["status"] == ""  # Should default to empty string
            assert conversation["details"] == ""  # Should default to empty string
            assert conversation["output"] == ""  # Should default to empty string
            assert conversation["code_files"] == []  # Should default to empty list
            assert conversation["escalations"] == []  # Should default to empty list
            assert conversation["collaborations"] == []  # Should default to empty list
