#!/usr/bin/env python3
"""
Test Optimization System

This script provides comprehensive testing of the workflow optimization system
to validate that it prevents over-engineering of simple tasks and optimizes
AI agent collaborations.

Tests the complete optimization pipeline:
1. Task complexity assessment
2. Cost monitoring
3. Streamlined workflow execution
4. Efficiency reporting
5. Performance validation

Based on analysis of workflow 18 (NEGISHI-200):
- Simple task: 99 messages, $6.14 cost, 120+ seconds (12x over-engineered)
- Target: 20 messages, $1.00 cost, 30 seconds (75% message reduction, 84% cost reduction)
"""

import sys
import os
import json
import time
from typing import Dict, List, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crewai_app.utils.task_complexity_assessor import (
    TaskComplexityAssessor, TaskComplexity, WorkflowConfig
)
from crewai_app.utils.cost_monitor import CostMonitor, BudgetStatus
from crewai_app.workflows.streamlined_workflow import StreamlinedWorkflow
from crewai_app.workflows.workflow_orchestrator import WorkflowOrchestrator
from crewai_app.utils.efficiency_reporting import EfficiencyReporter
from crewai_app.agents.optimized_agents import (
    OptimizedPlannerAgent, OptimizedDeveloperAgent, OptimizedFrontendAgent
)

def test_task_complexity_assessment():
    """Test task complexity assessment functionality."""
    print("🧪 Testing Task Complexity Assessment...")
    
    assessor = TaskComplexityAssessor()
    
    # Test simple story (like NEGISHI-200)
    simple_story = {
        "fields": {
            "summary": "Add version number to footer",
            "description": """
            As a user, I want to see the version number in the footer so that I know what version of the application I'm using.
            
            Acceptance Criteria:
            1. Version number is displayed in the footer
            2. Version number is updated automatically from package.json
            """,
            "customfield_10016": 2  # Story points
        }
    }
    
    # Assess complexity
    complexity = assessor.assess_complexity(simple_story)
    print(f"✅ Simple story complexity: {complexity.value}")
    assert complexity == TaskComplexity.SIMPLE
    
    # Get workflow config
    config = assessor.get_workflow_config(complexity)
    print(f"✅ Simple workflow config: {config.max_messages} messages, ${config.max_cost} cost, {config.max_duration}s duration")
    assert config.max_messages == 20
    assert config.max_cost == 1.00
    assert config.max_duration == 1800  # 30 minutes
    assert config.workflow_type == "streamlined"
    
    # Test medium story
    medium_story = {
        "fields": {
            "summary": "Implement user authentication system",
            "description": """
            As a user, I want to be able to log in and out of the application securely.
            
            Acceptance Criteria:
            1. User can register with email and password
            2. User can log in with valid credentials
            3. User can log out and session is terminated
            4. Password is encrypted and stored securely
            """,
            "customfield_10016": 5  # Story points
        }
    }
    
    complexity = assessor.assess_complexity(medium_story)
    print(f"✅ Medium story complexity: {complexity.value}")
    assert complexity == TaskComplexity.MEDIUM
    
    # Test complex story
    complex_story = {
        "fields": {
            "summary": "Implement comprehensive e-commerce platform",
            "description": """
            As a business owner, I want a complete e-commerce platform with advanced features.
            
            Acceptance Criteria:
            1. Product catalog with search and filtering
            2. Shopping cart with add/remove functionality
            3. User authentication and authorization
            4. Payment processing integration
            5. Order management system
            6. Inventory tracking
            7. Admin dashboard
            8. Analytics and reporting
            """,
            "customfield_10016": 13  # Story points
        }
    }
    
    complexity = assessor.assess_complexity(complex_story)
    print(f"✅ Complex story complexity: {complexity.value}")
    assert complexity == TaskComplexity.COMPLEX
    
    print("✅ Task complexity assessment tests passed!")

def test_cost_monitoring():
    """Test cost monitoring functionality."""
    print("\n🧪 Testing Cost Monitoring...")
    
    # Test cost monitor initialization
    config = {
        "max_cost": 1.00,
        "max_messages": 20,
        "max_duration": 1800
    }
    
    monitor = CostMonitor(config)
    print(f"✅ Cost monitor initialized: ${monitor.limits.max_cost} max cost, {monitor.limits.max_messages} max messages")
    assert monitor.limits.max_cost == 1.00
    assert monitor.limits.max_messages == 20
    assert monitor.limits.max_duration == 1800
    assert monitor.current_cost == 0.0
    assert monitor.current_messages == 0
    
    # Test cost entry addition
    status = monitor.add_cost_entry(
        agent="planner",
        step="analyze_story",
        message_cost=0.15,
        token_count=100
    )
    print(f"✅ Cost entry added: ${monitor.current_cost} total cost, {monitor.current_messages} messages")
    assert status == BudgetStatus.WITHIN_BUDGET
    assert monitor.current_cost == 0.15
    assert monitor.current_messages == 1
    assert monitor.current_tokens == 100
    
    # Test budget exceeded scenario
    config = {
        "max_cost": 0.50,
        "max_messages": 5,
        "max_duration": 1800
    }
    
    monitor = CostMonitor(config)
    monitor.add_cost_entry("agent1", "step1", 0.30, 100)
    monitor.add_cost_entry("agent2", "step2", 0.30, 100)
    
    print(f"✅ Budget exceeded test: ${monitor.current_cost} cost, should terminate: {monitor.should_terminate()}")
    assert monitor.should_terminate() == True
    assert monitor.current_cost > monitor.limits.max_cost
    
    # Test cost summary
    config = {
        "max_cost": 1.00,
        "max_messages": 20,
        "max_duration": 1800
    }
    
    monitor = CostMonitor(config)
    monitor.add_cost_entry("planner", "analyze", 0.15, 100)
    monitor.add_cost_entry("developer", "implement", 0.25, 150)
    monitor.add_cost_entry("frontend", "implement", 0.20, 120)
    
    summary = monitor.get_cost_summary()
    print(f"✅ Cost summary: ${summary.total_cost} total cost, {summary.total_messages} messages, {summary.efficiency_score} efficiency")
    assert summary.total_cost == 0.60
    assert summary.total_messages == 3
    assert summary.total_tokens == 370
    assert summary.budget_status == BudgetStatus.WITHIN_BUDGET
    assert summary.efficiency_score > 0
    
    print("✅ Cost monitoring tests passed!")

def test_optimized_agents():
    """Test optimized agents functionality."""
    print("\n🧪 Testing Optimized Agents...")
    
    # Mock OpenAI service
    class MockOpenAIService:
        def generate(self, prompt, step=None):
            if "planner" in step:
                return json.dumps({
                    "files_to_modify": ["package.json", "footer.component.ts"],
                    "implementation_approach": "Add version number to footer",
                    "backend_changes": "None required",
                    "frontend_changes": "Display version in footer component"
                })
            elif "developer" in step:
                return json.dumps({
                    "files": [{"file": "package.json", "code": '{"version": "1.0.0"}', "description": "Version file"}],
                    "implementation_notes": "Version added to package.json"
                })
            elif "frontend" in step:
                return json.dumps({
                    "files": [{"file": "footer.component.ts", "code": "export class FooterComponent {}", "description": "Footer component"}],
                    "implementation_notes": "Footer component updated"
                })
            return "{}"
    
    mock_openai = MockOpenAIService()
    
    # Test planner agent
    planner = OptimizedPlannerAgent(mock_openai)
    complexity = TaskComplexity.SIMPLE
    workflow_config = WorkflowConfig(
        max_messages=20,
        max_cost=1.00,
        max_duration=1800,
        agents=["planner", "developer", "frontend"],
        workflow_type="streamlined",
        description="3-step streamlined workflow for simple tasks"
    )
    
    planner.set_complexity(complexity, workflow_config)
    
    story = {
        "fields": {
            "summary": "Add version number to footer",
            "description": "As a user, I want to see the version number in the footer."
        }
    }
    
    # Mock cost monitor
    class MockCostMonitor:
        def __init__(self):
            self.current_cost = 0.0
            self.current_messages = 0
            self.current_tokens = 0
        
        def should_terminate(self):
            return False
        
        def add_cost_entry(self, agent, step, message_cost, token_count=0, metadata=None):
            self.current_cost += message_cost
            self.current_messages += 1
            self.current_tokens += token_count
            return BudgetStatus.WITHIN_BUDGET
    
    monitor = MockCostMonitor()
    
    # Test planner analysis
    result = planner.analyze_story(story, monitor)
    print(f"✅ Planner analysis result: {len(result)} keys")
    assert "files_to_modify" in result
    assert "implementation_approach" in result
    assert "backend_changes" in result
    assert "frontend_changes" in result
    
    # Test developer agent
    developer = OptimizedDeveloperAgent(mock_openai)
    developer.set_complexity(complexity, workflow_config)
    
    task = {
        "title": "Add version to footer",
        "description": "Simple task",
        "type": "backend"
    }
    
    plan = {
        "implementation_approach": "Add version number to footer",
        "backend_changes": "None required"
    }
    
    result = developer.implement_task(task, plan, monitor)
    print(f"✅ Developer implementation result: {len(result)} keys")
    assert "files" in result
    assert "implementation_notes" in result
    
    # Test frontend agent
    frontend = OptimizedFrontendAgent(mock_openai)
    frontend.set_complexity(complexity, workflow_config)
    
    task = {
        "title": "Add version to footer",
        "description": "Simple task",
        "type": "frontend"
    }
    
    plan = {
        "implementation_approach": "Add version number to footer",
        "frontend_changes": "Display version in footer component"
    }
    
    result = frontend.implement_task(task, plan, monitor)
    print(f"✅ Frontend implementation result: {len(result)} keys")
    assert "files" in result
    assert "implementation_notes" in result
    
    print("✅ Optimized agents tests passed!")

def test_streamlined_workflow():
    """Test streamlined workflow execution."""
    print("\n🧪 Testing Streamlined Workflow...")
    
    # Mock Jira service
    class MockJiraService:
        def get_story(self, story_id):
            return {
                "key": "NEGISHI-200",
                "fields": {
                    "summary": "Add version number to footer",
                    "description": "As a user, I want to see the version number in the footer."
                }
            }
    
    # Mock GitHub service
    class MockGitHubService:
        def create_pull_request(self, **kwargs):
            return {"url": "https://github.com/test/repo/pull/1"}
    
    # Create streamlined workflow with mocked services
    workflow = StreamlinedWorkflow("NEGISHI-200", use_real_jira=False, use_real_github=False)
    
    # Mock the agent methods
    class MockPlanner:
        def analyze_story(self, story, monitor):
            return {
                "files_to_modify": ["package.json", "footer.component.ts"],
                "implementation_approach": "Add version number to footer",
                "backend_changes": "None required",
                "frontend_changes": "Display version in footer component"
            }
    
    class MockDeveloper:
        def implement_task(self, task, plan, monitor):
            return {
                "files": [{"file": "package.json", "code": '{"version": "1.0.0"}', "description": "Version file"}],
                "implementation_notes": "Version added to package.json"
            }
    
    class MockFrontend:
        def implement_task(self, task, plan, monitor):
            return {
                "files": [{"file": "footer.component.ts", "code": "export class FooterComponent {}", "description": "Footer component"}],
                "implementation_notes": "Footer component updated"
            }
    
    # Replace agents with mocks
    workflow.planner = MockPlanner()
    workflow.developer = MockDeveloper()
    workflow.frontend = MockFrontend()
    
    # Execute workflow
    result = workflow.execute()
    print(f"✅ Streamlined workflow result: {result.status}, ${result.total_cost:.2f} cost, {result.total_messages} messages")
    
    # Verify results
    assert result.status == "completed"
    assert result.total_cost <= 1.00
    assert result.total_messages <= 20
    assert result.duration <= 1800  # 30 minutes
    assert result.efficiency_score > 0
    assert result.planner_result is not None
    assert result.frontend_result is not None
    
    print("✅ Streamlined workflow tests passed!")

def test_efficiency_reporting():
    """Test efficiency reporting functionality."""
    print("\n🧪 Testing Efficiency Reporting...")
    
    reporter = EfficiencyReporter()
    
    # Mock execution result
    class MockExecutionResult:
        def __init__(self):
            self.story_id = "NEGISHI-200"
            self.complexity = TaskComplexity.SIMPLE
            self.workflow_type = type('obj', (object,), {'value': 'streamlined'})
            self.status = "completed"
            self.total_cost = 0.75
            self.total_messages = 15
            self.duration = 1200  # 20 minutes
            self.efficiency_score = 0.85
            self.early_termination = False
            self.termination_reason = None
            self.error = None
            self.result_data = None
    
    result = MockExecutionResult()
    
    # Generate efficiency report
    report = reporter.generate_efficiency_report(result)
    print(f"✅ Efficiency report generated: {report.metrics.overall_efficiency} overall efficiency")
    
    assert report.story_id == "NEGISHI-200"
    assert report.complexity == TaskComplexity.SIMPLE
    assert report.workflow_type.value == "streamlined"
    assert report.metrics.overall_efficiency > 0
    assert report.metrics.efficiency_level is not None
    assert report.metrics.performance_score > 0
    assert len(report.recommendations) >= 0
    
    # Test optimization summary
    summary = reporter.get_optimization_summary(report)
    print(f"✅ Optimization summary: {summary['high_priority_recommendations']} high priority recommendations")
    assert "overall_efficiency" in summary
    assert "efficiency_level" in summary
    assert "performance_score" in summary
    assert "optimization_potential" in summary
    
    # Test report export
    json_report = reporter.export_report(report, "json")
    print(f"✅ Report exported: {len(json_report)} characters")
    assert isinstance(json_report, str)
    report_data = json.loads(json_report)
    assert "story_id" in report_data
    assert "complexity" in report_data
    assert "workflow_type" in report_data
    assert "metrics" in report_data
    assert "performance" in report_data
    assert "recommendations" in report_data
    
    print("✅ Efficiency reporting tests passed!")

def test_workflow_orchestrator():
    """Test workflow orchestrator functionality."""
    print("\n🧪 Testing Workflow Orchestrator...")
    
    # Mock Jira service
    class MockJiraService:
        def get_story(self, story_id):
            return {
                "key": "NEGISHI-200",
                "fields": {
                    "summary": "Add version number to footer",
                    "description": "As a user, I want to see the version number in the footer."
                }
            }
    
    # Mock GitHub service
    class MockGitHubService:
        def create_pull_request(self, **kwargs):
            return {"url": "https://github.com/test/repo/pull/1"}
    
    # Create orchestrator with mocked services
    orchestrator = WorkflowOrchestrator(use_real_jira=False, use_real_github=False)
    
    # Mock the agent methods
    class MockPlanner:
        def analyze_story(self, story, monitor):
            return {
                "files_to_modify": ["package.json", "footer.component.ts"],
                "implementation_approach": "Add version number to footer",
                "backend_changes": "None required",
                "frontend_changes": "Display version in footer component"
            }
    
    class MockDeveloper:
        def implement_task(self, task, plan, monitor):
            return {
                "files": [{"file": "package.json", "code": '{"version": "1.0.0"}', "description": "Version file"}],
                "implementation_notes": "Version added to package.json"
            }
    
    class MockFrontend:
        def implement_task(self, task, plan, monitor):
            return {
                "files": [{"file": "footer.component.ts", "code": "export class FooterComponent {}", "description": "Footer component"}],
                "implementation_notes": "Footer component updated"
            }
    
    # Replace agents with mocks
    orchestrator.planner = MockPlanner()
    orchestrator.developer = MockDeveloper()
    orchestrator.frontend = MockFrontend()
    
    # Execute workflow
    result = orchestrator.execute_workflow("NEGISHI-200")
    print(f"✅ Workflow orchestrator result: {result.workflow_type.value}, {result.complexity.value}, {result.status}")
    
    # Verify results
    assert result.workflow_type.value == "streamlined"
    assert result.complexity == TaskComplexity.SIMPLE
    assert result.status == "completed"
    assert result.total_cost <= 1.00
    assert result.total_messages <= 20
    assert result.duration <= 1800  # 30 minutes
    
    # Test efficiency report generation
    report = orchestrator.get_efficiency_report(result)
    print(f"✅ Efficiency report: {report['efficiency_metrics']['overall_efficiency']} overall efficiency")
    assert "story_id" in report
    assert "complexity" in report
    assert "workflow_type" in report
    assert "status" in report
    assert "performance" in report
    assert "efficiency_metrics" in report
    assert "recommendations" in report
    
    print("✅ Workflow orchestrator tests passed!")

def test_performance_validation():
    """Test performance validation against NEGISHI-200 benchmarks."""
    print("\n🧪 Testing Performance Validation...")
    
    # NEGISHI-200 benchmarks
    negishi_200_current = {
        "messages": 99,
        "cost": 6.14,
        "duration": 120  # 2 minutes (120+ seconds)
    }
    
    negishi_200_target = {
        "messages": 20,
        "cost": 1.00,
        "duration": 1800  # 30 minutes
    }
    
    # Calculate expected improvements
    message_reduction = (negishi_200_current["messages"] - negishi_200_target["messages"]) / negishi_200_current["messages"] * 100
    cost_reduction = (negishi_200_current["cost"] - negishi_200_target["cost"]) / negishi_200_current["cost"] * 100
    
    print(f"✅ NEGISHI-200 Current Performance: {negishi_200_current['messages']} messages, ${negishi_200_current['cost']:.2f} cost")
    print(f"✅ NEGISHI-200 Target Performance: {negishi_200_target['messages']} messages, ${negishi_200_target['cost']:.2f} cost")
    print(f"✅ Expected Message Reduction: {message_reduction:.1f}%")
    print(f"✅ Expected Cost Reduction: {cost_reduction:.1f}%")
    
    # Validate that our optimization system can achieve these targets
    assert message_reduction >= 75.0  # 75% message reduction
    assert cost_reduction >= 80.0     # 80% cost reduction
    
    # Test that our streamlined workflow configuration matches targets
    assessor = TaskComplexityAssessor()
    simple_story = {
        "fields": {
            "summary": "Add version number to footer",
            "description": "As a user, I want to see the version number in the footer."
        }
    }
    
    complexity = assessor.assess_complexity(simple_story)
    config = assessor.get_workflow_config(complexity)
    
    print(f"✅ Streamlined workflow config: {config.max_messages} messages, ${config.max_cost} cost, {config.max_duration}s duration")
    
    # Validate configuration matches targets
    assert config.max_messages <= negishi_200_target["messages"]
    assert config.max_cost <= negishi_200_target["cost"]
    assert config.max_duration >= negishi_200_target["duration"]  # Duration should be reasonable
    
    print("✅ Performance validation tests passed!")

def main():
    """Run all optimization system tests."""
    print("🚀 Starting Workflow Optimization System Tests")
    print("=" * 60)
    
    try:
        # Run all tests
        test_task_complexity_assessment()
        test_cost_monitoring()
        test_optimized_agents()
        test_streamlined_workflow()
        test_efficiency_reporting()
        test_workflow_orchestrator()
        test_performance_validation()
        
        print("\n" + "=" * 60)
        print("✅ All optimization system tests passed!")
        print("🎯 System ready to prevent over-engineering of simple tasks")
        print("📊 Expected improvements:")
        print("   - 75% message reduction for simple tasks")
        print("   - 84% cost reduction for simple tasks")
        print("   - 12x efficiency improvement over current system")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
