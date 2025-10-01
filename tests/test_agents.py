import pytest
from unittest.mock import MagicMock
from crewai_app.agents.base import BaseAgent
from crewai_app.agents.developer import DeveloperAgent
from crewai_app.agents.frontend import FrontendAgent

class DummyLLMService:
    def generate(self, prompt, step=None, **kwargs):
        return '{"result": "ok"}'

def test_base_agent_llm_interaction():
    agent = BaseAgent(DummyLLMService(), name="test", role="Test", goal="Goal", backstory="Backstory")
    result = agent._run_llm("prompt")
    assert result == '{"result": "ok"}'

def test_base_agent_parse_output_json():
    agent = BaseAgent(DummyLLMService(), name="test", role="Test", goal="Goal", backstory="Backstory")
    output = '{"foo": 1}'
    parsed = agent.parse_output(output, parse_type="json")
    assert parsed == {"foo": 1}

def test_base_agent_shared_context():
    agent = BaseAgent(DummyLLMService(), name="test", role="Test", goal="Goal", backstory="Backstory")
    agent.update_shared_context("key", 123)
    assert agent.get_shared_context("key") == 123

def test_base_agent_escalate_logs(caplog):
    agent = BaseAgent(DummyLLMService(), name="test", role="Test", goal="Goal", backstory="Backstory")
    with caplog.at_level("INFO"):
        agent.escalate("reason", to_agent="frontend", context={"foo": "bar"})
    assert any("Escalating to frontend" in m for m in caplog.messages)

def test_developer_agent_instantiation():
    agent = DeveloperAgent(DummyLLMService())
    assert agent.name == "developer"
    assert agent.role == "Backend Developer"
    assert hasattr(agent, "escalate_to_frontend")

def test_frontend_agent_instantiation():
    agent = FrontendAgent(DummyLLMService())
    assert agent.name == "frontend"
    assert agent.role == "Frontend Developer"
    assert hasattr(agent, "escalate_to_backend") 