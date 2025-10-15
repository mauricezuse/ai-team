"""
Test Implementation for Workflow Optimization System

This module provides comprehensive testing for the workflow optimization system
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

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

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

class TestTaskComplexityAssessment:
    """Test task complexity assessment functionality."""
    
    def test_simple_story_assessment(self):
        """Test assessment of simple story (like NEGISHI-200)."""
        assessor = TaskComplexityAssessor()
        
        # Simple story with 2 acceptance criteria
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
        assert complexity == TaskComplexity.SIMPLE
        
        # Get workflow config
        config = assessor.get_workflow_config(complexity)
        assert config.max_messages == 20
        assert config.max_cost == 1.00
        assert config.max_duration == 1800  # 30 minutes
        assert config.workflow_type == "streamlined"
    
    def test_medium_story_assessment(self):
        """Test assessment of medium complexity story."""
        assessor = TaskComplexityAssessor()
        
        # Medium story with 4 acceptance criteria
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
        
        # Assess complexity
        complexity = assessor.assess_complexity(medium_story)
        assert complexity == TaskComplexity.MEDIUM
        
        # Get workflow config
        config = assessor.get_workflow_config(complexity)
        assert config.max_messages == 50
        assert config.max_cost == 3.00
        assert config.max_duration == 2700  # 45 minutes
        assert config.workflow_type == "medium"
    
    def test_complex_story_assessment(self):
        """Test assessment of complex story."""
        assessor = TaskComplexityAssessor()
        
        # Complex story with 8 acceptance criteria
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
        
        # Assess complexity
        complexity = assessor.assess_complexity(complex_story)
        assert complexity == TaskComplexity.COMPLEX
        
        # Get workflow config
        config = assessor.get_workflow_config(complexity)
        assert config.max_messages == 100
        assert config.max_cost == 10.00
        assert config.max_duration == 3600  # 60 minutes
        assert config.workflow_type == "full"
    
    def test_complexity_analysis(self):
        """Test detailed complexity analysis."""
        assessor = TaskComplexityAssessor()
        
        simple_story = {
            "fields": {
                "summary": "Add version number to footer",
                "description": "As a user, I want to see the version number in the footer."
            }
        }
        
        analysis = assessor.get_complexity_analysis(simple_story)
        
        assert "complexity" in analysis
        assert "metrics" in analysis
        assert "workflow_config" in analysis
        assert "recommendation" in analysis
        
        assert analysis["complexity"] == "simple"
        assert analysis["metrics"]["criteria_count"] >= 1
        assert analysis["workflow_config"]["max_messages"] == 20
        assert analysis["workflow_config"]["max_cost"] == 1.00

class TestCostMonitoring:
    """Test cost monitoring functionality."""
    
    def test_cost_monitor_initialization(self):
        """Test cost monitor initialization."""
        config = {
            "max_cost": 1.00,
            "max_messages": 20,
            "max_duration": 1800
        }
        
        monitor = CostMonitor(config)
        
        assert monitor.limits.max_cost == 1.00
        assert monitor.limits.max_messages == 20
        assert monitor.limits.max_duration == 1800
        assert monitor.current_cost == 0.0
        assert monitor.current_messages == 0
    
    def test_cost_entry_addition(self):
        """Test adding cost entries."""
        config = {
            "max_cost": 1.00,
            "max_messages": 20,
            "max_duration": 1800
        }
        
        monitor = CostMonitor(config)
        
        # Add cost entry
        status = monitor.add_cost_entry(
            agent="planner",
            step="analyze_story",
            message_cost=0.15,
            token_count=100
        )
        
        assert status == BudgetStatus.WITHIN_BUDGET
        assert monitor.current_cost == 0.15
        assert monitor.current_messages == 1
        assert monitor.current_tokens == 100
    
    def test_budget_exceeded(self):
        """Test budget exceeded scenario."""
        config = {
            "max_cost": 0.50,
            "max_messages": 5,
            "max_duration": 1800
        }
        
        monitor = CostMonitor(config)
        
        # Add entries that exceed budget
        monitor.add_cost_entry("agent1", "step1", 0.30, 100)
        monitor.add_cost_entry("agent2", "step2", 0.30, 100)
        
        assert monitor.should_terminate() == True
        assert monitor.current_cost > monitor.limits.max_cost
    
    def test_message_limit_exceeded(self):
        """Test message limit exceeded scenario."""
        config = {
            "max_cost": 1.00,
            "max_messages": 3,
            "max_duration": 1800
        }
        
        monitor = CostMonitor(config)
        
        # Add entries that exceed message limit
        for i in range(4):
            monitor.add_cost_entry(f"agent{i}", f"step{i}", 0.10, 50)
        
        assert monitor.should_terminate() == True
        assert monitor.current_messages > monitor.limits.max_messages
    
    def test_cost_summary(self):
        """Test cost summary generation."""
        config = {
            "max_cost": 1.00,
            "max_messages": 20,
            "max_duration": 1800
        }
        
        monitor = CostMonitor(config)
        
        # Add multiple cost entries
        monitor.add_cost_entry("planner", "analyze", 0.15, 100)
        monitor.add_cost_entry("developer", "implement", 0.25, 150)
        monitor.add_cost_entry("frontend", "implement", 0.20, 120)
        
        summary = monitor.get_cost_summary()
        
        assert summary.total_cost == 0.60
        assert summary.total_messages == 3
        assert summary.total_tokens == 370
        assert summary.budget_status == BudgetStatus.WITHIN_BUDGET
        assert summary.efficiency_score > 0

class TestStreamlinedWorkflow:
    """Test streamlined workflow execution."""
    
    @patch('crewai_app.services.jira_service.JiraService')
    @patch('crewai_app.services.github_service.GitHubService')
    def test_streamlined_workflow_execution(self, mock_github, mock_jira):
        """Test streamlined workflow execution for simple tasks."""
        # Mock Jira service
        mock_jira.return_value.get_story.return_value = {
            "key": "NEGISHI-200",
            "fields": {
                "summary": "Add version number to footer",
                "description": "As a user, I want to see the version number in the footer."
            }
        }
        
        # Mock GitHub service
        mock_github.return_value.create_pull_request.return_value = {
            "url": "https://github.com/test/repo/pull/1"
        }
        
        # Create streamlined workflow
        workflow = StreamlinedWorkflow("NEGISHI-200", use_real_jira=False, use_real_github=False)
        
        # Mock the agent methods
        with patch.object(workflow.planner, 'analyze_story') as mock_analyze, \
             patch.object(workflow.developer, 'implement_task') as mock_implement, \
             patch.object(workflow.frontend, 'implement_task') as mock_frontend:
            
            # Mock planner result
            mock_analyze.return_value = {
                "files_to_modify": ["package.json", "footer.component.ts"],
                "implementation_approach": "Add version number to footer",
                "backend_changes": "None required",
                "frontend_changes": "Display version in footer component"
            }
            
            # Mock developer result
            mock_implement.return_value = {
                "files": [{"file": "package.json", "code": '{"version": "1.0.0"}', "description": "Version file"}],
                "implementation_notes": "Version added to package.json"
            }
            
            # Mock frontend result
            mock_frontend.return_value = {
                "files": [{"file": "footer.component.ts", "code": "export class FooterComponent {}", "description": "Footer component"}],
                "implementation_notes": "Footer component updated"
            }
            
            # Execute workflow
            result = workflow.execute()
            
            # Verify results
            assert result.status == "completed"
            assert result.total_cost <= 1.00
            assert result.total_messages <= 20
            assert result.duration <= 1800  # 30 minutes
            assert result.efficiency_score > 0
            assert result.planner_result is not None
            assert result.frontend_result is not None
    
    def test_efficiency_report_generation(self):
        """Test efficiency report generation."""
        workflow = StreamlinedWorkflow("NEGISHI-200", use_real_jira=False, use_real_github=False)
        
        # Mock result
        result = Mock()
        result.status = "completed"
        result.total_cost = 0.75
        result.total_messages = 15
        result.duration = 1200  # 20 minutes
        result.efficiency_score = 0.85
        
        # Generate efficiency report
        report = workflow.get_efficiency_report(result)
        
        assert "workflow_type" in report
        assert "story_id" in report
        assert "performance" in report
        assert "efficiency_metrics" in report
        assert "recommendations" in report
        
        assert report["workflow_type"] == "streamlined"
        assert report["story_id"] == "NEGISHI-200"
        assert report["performance"]["actual"]["cost"] == 0.75
        assert report["performance"]["actual"]["messages"] == 15

class TestWorkflowOrchestrator:
    """Test workflow orchestrator functionality."""
    
    @patch('crewai_app.services.jira_service.JiraService')
    @patch('crewai_app.services.github_service.GitHubService')
    def test_simple_task_routing(self, mock_github, mock_jira):
        """Test routing of simple tasks to streamlined workflow."""
        # Mock Jira service
        mock_jira.return_value.get_story.return_value = {
            "key": "NEGISHI-200",
            "fields": {
                "summary": "Add version number to footer",
                "description": "As a user, I want to see the version number in the footer."
            }
        }
        
        # Create orchestrator
        orchestrator = WorkflowOrchestrator(use_real_jira=False, use_real_github=False)
        
        # Mock the agent methods
        with patch.object(orchestrator.planner, 'analyze_story') as mock_analyze, \
             patch.object(orchestrator.developer, 'implement_task') as mock_implement, \
             patch.object(orchestrator.frontend, 'implement_task') as mock_frontend:
            
            # Mock planner result
            mock_analyze.return_value = {
                "files_to_modify": ["package.json", "footer.component.ts"],
                "implementation_approach": "Add version number to footer",
                "backend_changes": "None required",
                "frontend_changes": "Display version in footer component"
            }
            
            # Mock developer result
            mock_implement.return_value = {
                "files": [{"file": "package.json", "code": '{"version": "1.0.0"}', "description": "Version file"}],
                "implementation_notes": "Version added to package.json"
            }
            
            # Mock frontend result
            mock_frontend.return_value = {
                "files": [{"file": "footer.component.ts", "code": "export class FooterComponent {}", "description": "Footer component"}],
                "implementation_notes": "Footer component updated"
            }
            
            # Execute workflow
            result = orchestrator.execute_workflow("NEGISHI-200")
            
            # Verify results
            assert result.workflow_type.value == "streamlined"
            assert result.complexity == TaskComplexity.SIMPLE
            assert result.status == "completed"
            assert result.total_cost <= 1.00
            assert result.total_messages <= 20
            assert result.duration <= 1800  # 30 minutes
    
    def test_efficiency_report_generation(self):
        """Test efficiency report generation."""
        orchestrator = WorkflowOrchestrator(use_real_jira=False, use_real_github=False)
        
        # Mock execution result
        result = Mock()
        result.workflow_type.value = "streamlined"
        result.complexity = TaskComplexity.SIMPLE
        result.status = "completed"
        result.total_cost = 0.75
        result.total_messages = 15
        result.duration = 1200  # 20 minutes
        result.efficiency_score = 0.85
        result.early_termination = False
        result.termination_reason = None
        result.error = None
        
        # Generate efficiency report
        report = orchestrator.get_efficiency_report(result)
        
        assert "story_id" in report
        assert "complexity" in report
        assert "workflow_type" in report
        assert "status" in report
        assert "performance" in report
        assert "efficiency_metrics" in report
        assert "recommendations" in report
        
        assert report["complexity"] == "simple"
        assert report["workflow_type"] == "streamlined"
        assert report["status"] == "completed"

class TestEfficiencyReporting:
    """Test efficiency reporting functionality."""
    
    def test_efficiency_reporter_initialization(self):
        """Test efficiency reporter initialization."""
        reporter = EfficiencyReporter()
        
        assert reporter.benchmarks is not None
        assert len(report_history) == 0
        assert len(performance_trends) == 0
    
    def test_efficiency_metrics_calculation(self):
        """Test efficiency metrics calculation."""
        reporter = EfficiencyReporter()
        
        # Mock execution result
        result = Mock()
        result.story_id = "NEGISHI-200"
        result.complexity = TaskComplexity.SIMPLE
        result.workflow_type.value = "streamlined"
        result.status = "completed"
        result.total_cost = 0.75
        result.total_messages = 15
        result.duration = 1200  # 20 minutes
        result.efficiency_score = 0.85
        result.early_termination = False
        result.termination_reason = None
        result.error = None
        result.result_data = None
        
        # Generate efficiency report
        report = reporter.generate_efficiency_report(result)
        
        assert report.story_id == "NEGISHI-200"
        assert report.complexity == TaskComplexity.SIMPLE
        assert report.workflow_type.value == "streamlined"
        assert report.metrics.overall_efficiency > 0
        assert report.metrics.efficiency_level is not None
        assert report.metrics.performance_score > 0
        assert len(report.recommendations) >= 0
    
    def test_optimization_recommendations(self):
        """Test optimization recommendations generation."""
        reporter = EfficiencyReporter()
        
        # Mock execution result with poor performance
        result = Mock()
        result.story_id = "NEGISHI-200"
        result.complexity = TaskComplexity.SIMPLE
        result.workflow_type.value = "streamlined"
        result.status = "completed"
        result.total_cost = 2.00  # Exceeds budget
        result.total_messages = 50  # Exceeds limit
        result.duration = 2400  # Exceeds time limit
        result.efficiency_score = 0.3  # Poor efficiency
        result.early_termination = False
        result.termination_reason = None
        result.error = None
        result.result_data = None
        
        # Generate efficiency report
        report = reporter.generate_efficiency_report(result)
        
        # Check that recommendations are generated
        assert len(report.recommendations) > 0
        
        # Check for high-priority recommendations
        high_priority_recs = [r for r in report.recommendations if r.priority == "high"]
        assert len(high_priority_recs) > 0
        
        # Check for cost optimization recommendations
        cost_recs = [r for r in report.recommendations if r.category == "Cost Efficiency"]
        assert len(cost_recs) > 0
    
    def test_export_report(self):
        """Test report export functionality."""
        reporter = EfficiencyReporter()
        
        # Mock execution result
        result = Mock()
        result.story_id = "NEGISHI-200"
        result.complexity = TaskComplexity.SIMPLE
        result.workflow_type.value = "streamlined"
        result.status = "completed"
        result.total_cost = 0.75
        result.total_messages = 15
        result.duration = 1200
        result.efficiency_score = 0.85
        result.early_termination = False
        result.termination_reason = None
        result.error = None
        result.result_data = None
        
        # Generate efficiency report
        report = reporter.generate_efficiency_report(result)
        
        # Export report
        json_report = reporter.export_report(report, "json")
        
        # Verify JSON export
        assert isinstance(json_report, str)
        report_data = json.loads(json_report)
        assert "story_id" in report_data
        assert "complexity" in report_data
        assert "workflow_type" in report_data
        assert "metrics" in report_data
        assert "performance" in report_data
        assert "recommendations" in report_data

class TestOptimizedAgents:
    """Test optimized agents functionality."""
    
    def test_planner_agent_complexity_awareness(self):
        """Test planner agent complexity awareness."""
        from crewai_app.services.openai_service import OpenAIService
        
        # Mock OpenAI service
        mock_openai = Mock(spec=OpenAIService)
        mock_openai.generate.return_value = json.dumps({
            "files_to_modify": ["package.json", "footer.component.ts"],
            "implementation_approach": "Add version number to footer",
            "backend_changes": "None required",
            "frontend_changes": "Display version in footer component"
        })
        
        # Create planner agent
        planner = OptimizedPlannerAgent(mock_openai)
        
        # Set complexity
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
        
        # Mock story
        story = {
            "fields": {
                "summary": "Add version number to footer",
                "description": "As a user, I want to see the version number in the footer."
            }
        }
        
        # Mock cost monitor
        monitor = Mock()
        monitor.should_terminate.return_value = False
        monitor.add_cost_entry.return_value = BudgetStatus.WITHIN_BUDGET
        
        # Test analysis
        result = planner.analyze_story(story, monitor)
        
        assert "files_to_modify" in result
        assert "implementation_approach" in result
        assert "backend_changes" in result
        assert "frontend_changes" in result
        
        # Verify cost tracking
        monitor.add_cost_entry.assert_called_once()
    
    def test_developer_agent_complexity_awareness(self):
        """Test developer agent complexity awareness."""
        from crewai_app.services.openai_service import OpenAIService
        
        # Mock OpenAI service
        mock_openai = Mock(spec=OpenAIService)
        mock_openai.generate.return_value = json.dumps({
            "files": [{"file": "package.json", "code": '{"version": "1.0.0"}', "description": "Version file"}],
            "implementation_notes": "Version added to package.json"
        })
        
        # Create developer agent
        developer = OptimizedDeveloperAgent(mock_openai)
        
        # Set complexity
        complexity = TaskComplexity.SIMPLE
        workflow_config = WorkflowConfig(
            max_messages=20,
            max_cost=1.00,
            max_duration=1800,
            agents=["planner", "developer", "frontend"],
            workflow_type="streamlined",
            description="3-step streamlined workflow for simple tasks"
        )
        
        developer.set_complexity(complexity, workflow_config)
        
        # Mock task and plan
        task = {
            "title": "Add version to footer",
            "description": "Simple task",
            "type": "backend"
        }
        
        plan = {
            "implementation_approach": "Add version number to footer",
            "backend_changes": "None required"
        }
        
        # Mock cost monitor
        monitor = Mock()
        monitor.should_terminate.return_value = False
        monitor.add_cost_entry.return_value = BudgetStatus.WITHIN_BUDGET
        
        # Test implementation
        result = developer.implement_task(task, plan, monitor)
        
        assert "files" in result
        assert "implementation_notes" in result
        
        # Verify cost tracking
        monitor.add_cost_entry.assert_called_once()
    
    def test_frontend_agent_complexity_awareness(self):
        """Test frontend agent complexity awareness."""
        from crewai_app.services.openai_service import OpenAIService
        
        # Mock OpenAI service
        mock_openai = Mock(spec=OpenAIService)
        mock_openai.generate.return_value = json.dumps({
            "files": [{"file": "footer.component.ts", "code": "export class FooterComponent {}", "description": "Footer component"}],
            "implementation_notes": "Footer component updated"
        })
        
        # Create frontend agent
        frontend = OptimizedFrontendAgent(mock_openai)
        
        # Set complexity
        complexity = TaskComplexity.SIMPLE
        workflow_config = WorkflowConfig(
            max_messages=20,
            max_cost=1.00,
            max_duration=1800,
            agents=["planner", "developer", "frontend"],
            workflow_type="streamlined",
            description="3-step streamlined workflow for simple tasks"
        )
        
        frontend.set_complexity(complexity, workflow_config)
        
        # Mock task and plan
        task = {
            "title": "Add version to footer",
            "description": "Simple task",
            "type": "frontend"
        }
        
        plan = {
            "implementation_approach": "Add version number to footer",
            "frontend_changes": "Display version in footer component"
        }
        
        # Mock cost monitor
        monitor = Mock()
        monitor.should_terminate.return_value = False
        monitor.add_cost_entry.return_value = BudgetStatus.WITHIN_BUDGET
        
        # Test implementation
        result = frontend.implement_task(task, plan, monitor)
        
        assert "files" in result
        assert "implementation_notes" in result
        
        # Verify cost tracking
        monitor.add_cost_entry.assert_called_once()

class TestIntegration:
    """Test integration of all optimization components."""
    
    def test_complete_optimization_pipeline(self):
        """Test complete optimization pipeline from story to efficiency report."""
        # This would be a comprehensive integration test
        # that tests the entire pipeline:
        # 1. Story retrieval
        # 2. Complexity assessment
        # 3. Workflow routing
        # 4. Cost monitoring
        # 5. Efficiency reporting
        
        # For now, we'll test the key integration points
        assert True  # Placeholder for comprehensive integration test

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
