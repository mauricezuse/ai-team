import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock, mock_open
from fastapi.testclient import TestClient
from crewai_app.main import app

client = TestClient(app)

class TestAgentCollaboration:
    """Tests for agent collaboration and escalation features."""

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

    def test_agent_escalation_workflow(self, workflow_results_dir):
        """Test workflow with agent escalations."""
        escalation_data = {
            "workflow_log": [
                {
                    "step": "developer_task",
                    "timestamp": "2024-07-20T10:00:05.000Z",
                    "agent": "developer",
                    "status": "escalated",
                    "details": "Developer encountered complex implementation issue",
                    "output": "def complex_function(): ...",
                    "code_files": ["backend/complex.py"],
                    "escalations": [
                        {
                            "from_agent": "developer",
                            "to_agent": "architect",
                            "reason": "Complex database schema design needed",
                            "status": "pending"
                        }
                    ],
                    "collaborations": []
                },
                {
                    "step": "architect_review",
                    "timestamp": "2024-07-20T10:05:00.000Z",
                    "agent": "architect",
                    "status": "completed",
                    "details": "Architect provided schema design guidance",
                    "output": "Schema design: user_profiles table with indexes",
                    "code_files": ["backend/schema.sql"],
                    "escalations": [],
                    "collaborations": []
                }
            ],
            "timestamp": "2024-07-20T10:00:00.000Z",
            "collaboration_queue": [],
            "escalation_queue": [
                {
                    "from_agent": "developer",
                    "to_agent": "architect",
                    "reason": "Complex database schema design needed",
                    "status": "pending",
                    "timestamp": "2024-07-20T10:00:05.000Z"
                }
            ]
        }
        
        file_path = os.path.join(workflow_results_dir, "escalation_workflow_checkpoint.json")
        with open(file_path, 'w') as f:
            json.dump(escalation_data, f)

        with patch('os.path.exists', return_value=True), \
             patch('glob.glob', return_value=[file_path]), \
             patch('builtins.open', mock_open(read_data=json.dumps(escalation_data))):
            
            # Test workflow list
            response = client.get("/workflows")
            assert response.status_code == 200
            workflows = response.json()
            assert len(workflows) == 1
            assert workflows[0]["id"] == "escalation_workflow"
            assert "developer" in workflows[0]["agents"]
            assert "architect" in workflows[0]["agents"]
            
            # Test workflow detail
            response = client.get("/workflows/escalation_workflow")
            assert response.status_code == 200
            workflow = response.json()
            assert len(workflow["conversations"]) == 2
            assert len(workflow["escalation_queue"]) == 1
            
            # Check escalation details
            dev_conversation = workflow["conversations"][0]
            assert dev_conversation["agent"] == "developer"
            assert len(dev_conversation["escalations"]) == 1
            assert dev_conversation["escalations"][0]["reason"] == "Complex database schema design needed"
            assert dev_conversation["escalations"][0]["status"] == "pending"

    def test_agent_collaboration_workflow(self, workflow_results_dir):
        """Test workflow with agent collaborations."""
        collaboration_data = {
            "workflow_log": [
                {
                    "step": "developer_implementation",
                    "timestamp": "2024-07-20T10:00:05.000Z",
                    "agent": "developer",
                    "status": "completed",
                    "details": "Backend API implemented",
                    "output": "def api_endpoint(): ...",
                    "code_files": ["backend/api.py"],
                    "escalations": [],
                    "collaborations": [
                        {
                            "from_agent": "developer",
                            "to_agent": "frontend",
                            "request_type": "API Contract",
                            "status": "pending"
                        }
                    ]
                },
                {
                    "step": "frontend_implementation",
                    "timestamp": "2024-07-20T10:05:00.000Z",
                    "agent": "frontend",
                    "status": "completed",
                    "details": "Frontend component implemented using API contract",
                    "output": "<app-component></app-component>",
                    "code_files": ["frontend/component.ts"],
                    "escalations": [],
                    "collaborations": []
                }
            ],
            "timestamp": "2024-07-20T10:00:00.000Z",
            "collaboration_queue": [
                {
                    "from_agent": "developer",
                    "to_agent": "frontend",
                    "request_type": "API Contract",
                    "status": "pending",
                    "timestamp": "2024-07-20T10:00:05.000Z"
                }
            ],
            "escalation_queue": []
        }
        
        file_path = os.path.join(workflow_results_dir, "collaboration_workflow_checkpoint.json")
        with open(file_path, 'w') as f:
            json.dump(collaboration_data, f)

        with patch('os.path.exists', return_value=True), \
             patch('glob.glob', return_value=[file_path]), \
             patch('builtins.open', mock_open(read_data=json.dumps(collaboration_data))):
            
            # Test workflow list
            response = client.get("/workflows")
            assert response.status_code == 200
            workflows = response.json()
            assert len(workflows) == 1
            assert workflows[0]["id"] == "collaboration_workflow"
            assert "developer" in workflows[0]["agents"]
            assert "frontend" in workflows[0]["agents"]
            
            # Test workflow detail
            response = client.get("/workflows/collaboration_workflow")
            assert response.status_code == 200
            workflow = response.json()
            assert len(workflow["conversations"]) == 2
            assert len(workflow["collaboration_queue"]) == 1
            
            # Check collaboration details
            dev_conversation = workflow["conversations"][0]
            assert dev_conversation["agent"] == "developer"
            assert len(dev_conversation["collaborations"]) == 1
            assert dev_conversation["collaborations"][0]["request_type"] == "API Contract"
            assert dev_conversation["collaborations"][0]["status"] == "pending"

    def test_complex_agent_interactions(self, workflow_results_dir):
        """Test workflow with complex agent interactions including both escalations and collaborations."""
        complex_data = {
            "workflow_log": [
                {
                    "step": "developer_implementation",
                    "timestamp": "2024-07-20T10:00:05.000Z",
                    "agent": "developer",
                    "status": "completed",
                    "details": "Developer implemented backend with some challenges",
                    "output": "def complex_api(): ...",
                    "code_files": ["backend/api.py", "backend/models.py"],
                    "escalations": [
                        {
                            "from_agent": "developer",
                            "to_agent": "architect",
                            "reason": "Performance optimization needed for large datasets",
                            "status": "resolved"
                        }
                    ],
                    "collaborations": [
                        {
                            "from_agent": "developer",
                            "to_agent": "frontend",
                            "request_type": "API Contract",
                            "status": "completed"
                        },
                        {
                            "from_agent": "developer",
                            "to_agent": "tester",
                            "request_type": "Test Data",
                            "status": "pending"
                        }
                    ]
                },
                {
                    "step": "architect_guidance",
                    "timestamp": "2024-07-20T10:02:00.000Z",
                    "agent": "architect",
                    "status": "completed",
                    "details": "Architect provided performance optimization guidance",
                    "output": "Use database indexes and caching strategy",
                    "code_files": ["backend/optimization.py"],
                    "escalations": [],
                    "collaborations": []
                },
                {
                    "step": "frontend_implementation",
                    "timestamp": "2024-07-20T10:05:00.000Z",
                    "agent": "frontend",
                    "status": "completed",
                    "details": "Frontend implemented using provided API contract",
                    "output": "<app-dashboard></app-dashboard>",
                    "code_files": ["frontend/dashboard.component.ts"],
                    "escalations": [],
                    "collaborations": []
                },
                {
                    "step": "tester_tests",
                    "timestamp": "2024-07-20T10:10:00.000Z",
                    "agent": "tester",
                    "status": "completed",
                    "details": "Comprehensive test suite generated",
                    "output": "test_api.py, test_frontend.spec.ts",
                    "code_files": ["tests/test_api.py", "tests/test_frontend.spec.ts"],
                    "escalations": [],
                    "collaborations": []
                }
            ],
            "timestamp": "2024-07-20T10:00:00.000Z",
            "collaboration_queue": [
                {
                    "from_agent": "developer",
                    "to_agent": "tester",
                    "request_type": "Test Data",
                    "status": "pending",
                    "timestamp": "2024-07-20T10:00:05.000Z"
                }
            ],
            "escalation_queue": []
        }
        
        file_path = os.path.join(workflow_results_dir, "complex_workflow_checkpoint.json")
        with open(file_path, 'w') as f:
            json.dump(complex_data, f)

        with patch('os.path.exists', return_value=True), \
             patch('glob.glob', return_value=[file_path]), \
             patch('builtins.open', mock_open(read_data=json.dumps(complex_data))):
            
            # Test workflow list
            response = client.get("/workflows")
            assert response.status_code == 200
            workflows = response.json()
            assert len(workflows) == 1
            assert workflows[0]["id"] == "complex_workflow"
            agents = workflows[0]["agents"]
            assert "developer" in agents
            assert "architect" in agents
            assert "frontend" in agents
            assert "tester" in agents
            
            # Test workflow detail
            response = client.get("/workflows/complex_workflow")
            assert response.status_code == 200
            workflow = response.json()
            assert len(workflow["conversations"]) == 4
            assert len(workflow["collaboration_queue"]) == 1
            assert len(workflow["escalation_queue"]) == 0
            
            # Check developer conversation with multiple interactions
            dev_conversation = workflow["conversations"][0]
            assert dev_conversation["agent"] == "developer"
            assert len(dev_conversation["escalations"]) == 1
            assert len(dev_conversation["collaborations"]) == 2
            
            # Check escalation details
            escalation = dev_conversation["escalations"][0]
            assert escalation["reason"] == "Performance optimization needed for large datasets"
            assert escalation["status"] == "resolved"
            
            # Check collaboration details
            collaborations = dev_conversation["collaborations"]
            assert len(collaborations) == 2
            assert any(c["to_agent"] == "frontend" and c["status"] == "completed" for c in collaborations)
            assert any(c["to_agent"] == "tester" and c["status"] == "pending" for c in collaborations)

    def test_agent_status_tracking(self, workflow_results_dir):
        """Test tracking of agent status throughout workflow."""
        status_data = {
            "workflow_log": [
                {
                    "step": "story_retrieved",
                    "timestamp": "2024-07-20T10:00:05.000Z",
                    "agent": "pm",
                    "status": "completed",
                    "details": "Story retrieved successfully",
                    "output": "Story: Implement user authentication",
                    "code_files": [],
                    "escalations": [],
                    "collaborations": []
                },
                {
                    "step": "architect_plan",
                    "timestamp": "2024-07-20T10:01:00.000Z",
                    "agent": "architect",
                    "status": "completed",
                    "details": "Architecture plan generated",
                    "output": "Plan: JWT authentication with refresh tokens",
                    "code_files": ["backend/auth_schema.py"],
                    "escalations": [],
                    "collaborations": []
                },
                {
                    "step": "developer_implementation",
                    "timestamp": "2024-07-20T10:05:00.000Z",
                    "agent": "developer",
                    "status": "in_progress",
                    "details": "Backend implementation in progress",
                    "output": "def login(): ... def refresh_token(): ...",
                    "code_files": ["backend/auth.py"],
                    "escalations": [],
                    "collaborations": []
                }
            ],
            "timestamp": "2024-07-20T10:00:00.000Z",
            "collaboration_queue": [],
            "escalation_queue": []
        }
        
        file_path = os.path.join(workflow_results_dir, "status_workflow_checkpoint.json")
        with open(file_path, 'w') as f:
            json.dump(status_data, f)

        with patch('os.path.exists', return_value=True), \
             patch('glob.glob', return_value=[file_path]), \
             patch('builtins.open', mock_open(read_data=json.dumps(status_data))):
            
            response = client.get("/workflows/status_workflow")
            assert response.status_code == 200
            workflow = response.json()
            assert len(workflow["conversations"]) == 3
            
            # Check status progression
            pm_conversation = workflow["conversations"][0]
            assert pm_conversation["status"] == "completed"
            
            architect_conversation = workflow["conversations"][1]
            assert architect_conversation["status"] == "completed"
            
            dev_conversation = workflow["conversations"][2]
            assert dev_conversation["status"] == "in_progress"

    def test_agent_code_file_tracking(self, workflow_results_dir):
        """Test tracking of code files generated by each agent."""
        code_tracking_data = {
            "workflow_log": [
                {
                    "step": "architect_plan",
                    "timestamp": "2024-07-20T10:01:00.000Z",
                    "agent": "architect",
                    "status": "completed",
                    "details": "Architecture plan with schema design",
                    "output": "Database schema and API design",
                    "code_files": [
                        "backend/schema.sql",
                        "backend/api_design.md",
                        "backend/models.py"
                    ],
                    "escalations": [],
                    "collaborations": []
                },
                {
                    "step": "developer_implementation",
                    "timestamp": "2024-07-20T10:05:00.000Z",
                    "agent": "developer",
                    "status": "completed",
                    "details": "Backend implementation completed",
                    "output": "def api_endpoint(): ...",
                    "code_files": [
                        "backend/api.py",
                        "backend/services.py",
                        "backend/utils.py",
                        "backend/config.py"
                    ],
                    "escalations": [],
                    "collaborations": []
                },
                {
                    "step": "frontend_implementation",
                    "timestamp": "2024-07-20T10:10:00.000Z",
                    "agent": "frontend",
                    "status": "completed",
                    "details": "Frontend components implemented",
                    "output": "<app-component></app-component>",
                    "code_files": [
                        "frontend/component.ts",
                        "frontend/component.html",
                        "frontend/component.scss",
                        "frontend/service.ts"
                    ],
                    "escalations": [],
                    "collaborations": []
                },
                {
                    "step": "tester_tests",
                    "timestamp": "2024-07-20T10:15:00.000Z",
                    "agent": "tester",
                    "status": "completed",
                    "details": "Comprehensive test suite generated",
                    "output": "Unit, integration, and E2E tests",
                    "code_files": [
                        "tests/unit/test_api.py",
                        "tests/integration/test_flow.py",
                        "tests/e2e/test_user_journey.spec.ts",
                        "tests/performance/test_load.py"
                    ],
                    "escalations": [],
                    "collaborations": []
                }
            ],
            "timestamp": "2024-07-20T10:00:00.000Z",
            "collaboration_queue": [],
            "escalation_queue": []
        }
        
        file_path = os.path.join(workflow_results_dir, "code_tracking_workflow_checkpoint.json")
        with open(file_path, 'w') as f:
            json.dump(code_tracking_data, f)

        with patch('os.path.exists', return_value=True), \
             patch('glob.glob', return_value=[file_path]), \
             patch('builtins.open', mock_open(read_data=json.dumps(code_tracking_data))):
            
            response = client.get("/workflows/code_tracking_workflow")
            assert response.status_code == 200
            workflow = response.json()
            assert len(workflow["conversations"]) == 4
            
            # Check architect code files
            architect_conversation = workflow["conversations"][0]
            assert len(architect_conversation["code_files"]) == 3
            assert "backend/schema.sql" in architect_conversation["code_files"]
            assert "backend/models.py" in architect_conversation["code_files"]
            
            # Check developer code files
            dev_conversation = workflow["conversations"][1]
            assert len(dev_conversation["code_files"]) == 4
            assert "backend/api.py" in dev_conversation["code_files"]
            assert "backend/services.py" in dev_conversation["code_files"]
            
            # Check frontend code files
            frontend_conversation = workflow["conversations"][2]
            assert len(frontend_conversation["code_files"]) == 4
            assert "frontend/component.ts" in frontend_conversation["code_files"]
            assert "frontend/component.html" in frontend_conversation["code_files"]
            
            # Check tester code files
            tester_conversation = workflow["conversations"][3]
            assert len(tester_conversation["code_files"]) == 4
            assert "tests/unit/test_api.py" in tester_conversation["code_files"]
            assert "tests/e2e/test_user_journey.spec.ts" in tester_conversation["code_files"]
