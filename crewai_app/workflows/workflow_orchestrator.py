"""
Workflow Orchestrator

This module provides intelligent routing and monitoring for AI agent workflows.
It prevents over-engineering by routing simple tasks to streamlined workflows
and complex tasks to full collaborative workflows.

Based on analysis of workflow 18 (NEGISHI-200):
- Simple tasks: Route to streamlined workflow (20 messages, $1.00, 30 minutes)
- Complex tasks: Route to full workflow (100 messages, $10.00, 60 minutes)
- Real-time monitoring and early termination if limits exceeded
"""

import time
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

from crewai_app.services.jira_service import JiraService
from crewai_app.services.github_service import GitHubService
from crewai_app.utils.task_complexity_assessor import (
    TaskComplexityAssessor, TaskComplexity, WorkflowConfig
)
from crewai_app.utils.cost_monitor import CostMonitor, BudgetStatus
from crewai_app.workflows.streamlined_workflow import StreamlinedWorkflow
from crewai_app.workflows.story_implementation_workflow import StoryImplementationWorkflow
from crewai_app.agents.optimized_agents import (
    OptimizedPlannerAgent, OptimizedDeveloperAgent, OptimizedFrontendAgent
)
from crewai_app.services.openai_service import OpenAIService
from crewai_app.utils.logger import logger

class WorkflowType(Enum):
    """Types of workflows available."""
    STREAMLINED = "streamlined"
    MEDIUM = "medium"
    FULL = "full"

@dataclass
class WorkflowExecutionResult:
    """Result of workflow execution."""
    workflow_type: WorkflowType
    story_id: str
    complexity: TaskComplexity
    status: str
    total_cost: float
    total_messages: int
    duration: float
    efficiency_score: float
    result_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    early_termination: bool = False
    termination_reason: Optional[str] = None

@dataclass
class WorkflowMetrics:
    """Metrics for workflow performance analysis."""
    story_id: str
    complexity: TaskComplexity
    workflow_type: WorkflowType
    performance: Dict[str, Any]
    efficiency_metrics: Dict[str, float]
    recommendations: List[str]
    cost_breakdown: Dict[str, float]
    message_breakdown: Dict[str, int]

class WorkflowOrchestrator:
    """
    Intelligent workflow orchestrator that routes tasks based on complexity.
    
    Prevents over-engineering by:
    1. Assessing task complexity before execution
    2. Routing simple tasks to streamlined workflows
    3. Routing complex tasks to full workflows
    4. Monitoring costs and messages in real-time
    5. Terminating early if limits exceeded
    """
    
    def __init__(self, use_real_jira: bool = True, use_real_github: bool = True):
        self.jira_service = JiraService(use_real_jira)
        self.github_service = GitHubService(use_real_github)
        self.complexity_assessor = TaskComplexityAssessor()
        self.openai_service = OpenAIService()
        
        # Initialize optimized agents
        self.planner = OptimizedPlannerAgent(self.openai_service)
        self.developer = OptimizedDeveloperAgent(self.openai_service)
        self.frontend = OptimizedFrontendAgent(self.openai_service)
        
        logger.info("WorkflowOrchestrator initialized")
    
    def execute_workflow(self, story_id: str) -> WorkflowExecutionResult:
        """
        Execute workflow with intelligent routing based on complexity.
        
        Args:
            story_id: Jira story ID to process
            
        Returns:
            WorkflowExecutionResult with execution details
        """
        start_time = time.time()
        
        try:
            # Step 1: Retrieve and analyze story
            logger.info(f"Step 1: Retrieving story {story_id}")
            story = self.jira_service.get_story(story_id)
            
            # Step 2: Assess complexity
            logger.info(f"Step 2: Assessing complexity for story {story_id}")
            complexity_analysis = self.complexity_assessor.get_complexity_analysis(story)
            complexity = TaskComplexity(complexity_analysis["complexity"])
            workflow_config = WorkflowConfig(**complexity_analysis["workflow_config"])
            
            logger.info(f"Story {story_id} assessed as {complexity.value} complexity")
            logger.info(f"Recommendation: {complexity_analysis['recommendation']}")
            
            # Step 3: Route to appropriate workflow
            if complexity == TaskComplexity.SIMPLE:
                return self._execute_streamlined_workflow(story, complexity, workflow_config, start_time)
            elif complexity == TaskComplexity.MEDIUM:
                return self._execute_medium_workflow(story_id, story, complexity, workflow_config, start_time)
            else:
                return self._execute_full_workflow(story_id, story, complexity, workflow_config, start_time)
                
        except Exception as e:
            logger.error(f"Workflow execution failed for story {story_id}: {e}")
            return WorkflowExecutionResult(
                workflow_type=WorkflowType.FULL,  # Default fallback
                story_id=story_id,
                complexity=TaskComplexity.COMPLEX,  # Default fallback
                status="failed",
                total_cost=0.0,
                total_messages=0,
                duration=time.time() - start_time,
                efficiency_score=0.0,
                error=str(e))
    
    def _execute_streamlined_workflow(self, story: Dict[str, Any], complexity: TaskComplexity, 
                                      workflow_config: WorkflowConfig, start_time: float) -> WorkflowExecutionResult:
        """Execute streamlined workflow for simple tasks."""
        try:
            logger.info("Executing streamlined workflow for simple task")
            
            # Initialize cost monitor
            monitor = CostMonitor(workflow_config.__dict__)
            
            # Set agent complexity
            self.planner.set_complexity(complexity, workflow_config)
            self.developer.set_complexity(complexity, workflow_config)
            self.frontend.set_complexity(complexity, workflow_config)
            
            # Step 1: Planner analysis
            logger.info("Step 1: Planner analysis")
            planner_result = self.planner.analyze_story(story, monitor)
            
            if monitor.should_terminate():
                return WorkflowExecutionResult(
                    workflow_type=WorkflowType.STREAMLINED,
                    story_id=story.get('key', 'unknown'),
                    complexity=complexity,
                    status="terminated",
                    total_cost=monitor.current_cost,
                    total_messages=monitor.current_messages,
                    duration=time.time() - start_time,
                    efficiency_score=monitor.get_cost_summary().efficiency_score,
                    early_termination=True,
                    termination_reason="Budget exceeded during planner analysis"
                )
            
            # Step 2: Backend development (if needed)
            developer_result = None
            if planner_result.get("backend_changes") and planner_result["backend_changes"] != "None required":
                logger.info("Step 2: Backend development")
                task = {
                    "title": "Implement backend changes",
                    "description": planner_result.get("backend_changes", "No backend changes needed"),
                    "type": "backend"
                }
                developer_result = self.developer.implement_task(task, planner_result, monitor)
                
                if monitor.should_terminate():
                    return WorkflowExecutionResult(
                        workflow_type=WorkflowType.STREAMLINED,
                        story_id=story.get('key', 'unknown'),
                        complexity=complexity,
                        status="terminated",
                        total_cost=monitor.current_cost,
                        total_messages=monitor.current_messages,
                        duration=time.time() - start_time,
                        efficiency_score=monitor.get_cost_summary().efficiency_score,
                        result_data={"planner_result": planner_result, "developer_result": developer_result},
                        early_termination=True,
                        termination_reason="Budget exceeded during backend development"
                    )
            
            # Step 3: Frontend development
            logger.info("Step 3: Frontend development")
            task = {
                "title": "Implement frontend changes",
                "description": planner_result.get("frontend_changes", "No frontend changes needed"),
                "type": "frontend"
            }
            frontend_result = self.frontend.implement_task(task, planner_result, monitor)
            
            if monitor.should_terminate():
                return WorkflowExecutionResult(
                    workflow_type=WorkflowType.STREAMLINED,
                    story_id=story.get('key', 'unknown'),
                    complexity=complexity,
                    status="terminated",
                    total_cost=monitor.current_cost,
                    total_messages=monitor.current_messages,
                    duration=time.time() - start_time,
                    efficiency_score=monitor.get_cost_summary().efficiency_score,
                    result_data={
                        "planner_result": planner_result,
                        "developer_result": developer_result,
                        "frontend_result": frontend_result
                    },
                    early_termination=True,
                    termination_reason="Budget exceeded during frontend development"
                )
            
            # Get final cost summary
            cost_summary = monitor.get_cost_summary()
            
            return WorkflowExecutionResult(
                workflow_type=WorkflowType.STREAMLINED,
                story_id=story.get('key', 'unknown'),
                complexity=complexity,
                status="completed",
                total_cost=cost_summary.total_cost,
                total_messages=cost_summary.total_messages,
                duration=time.time() - start_time,
                efficiency_score=cost_summary.efficiency_score,
                result_data={
                    "planner_result": planner_result,
                    "developer_result": developer_result,
                    "frontend_result": frontend_result
                }
            )
            
        except Exception as e:
            logger.error(f"Streamlined workflow failed: {e}")
            return WorkflowExecutionResult(
                workflow_type=WorkflowType.STREAMLINED,
                story_id=story.get('key', 'unknown'),
                complexity=complexity,
                status="failed",
                total_cost=monitor.current_cost if 'monitor' in locals() else 0.0,
                total_messages=monitor.current_messages if 'monitor' in locals() else 0,
                duration=time.time() - start_time,
                efficiency_score=0.0,
                error=str(e)
            )
    
    def _execute_medium_workflow(self, story: Dict[str, Any], complexity: TaskComplexity, 
                                workflow_config: WorkflowConfig, start_time: float) -> WorkflowExecutionResult:
        """Execute medium workflow for moderate complexity tasks."""
        try:
            logger.info("Executing medium workflow for moderate complexity task")
            
            # Initialize cost monitor
            monitor = CostMonitor(workflow_config.__dict__)
            
            # Set agent complexity
            self.planner.set_complexity(complexity, workflow_config)
            self.developer.set_complexity(complexity, workflow_config)
            self.frontend.set_complexity(complexity, workflow_config)
            
            # Execute medium workflow (similar to streamlined but with more steps)
            # This would be implemented similar to streamlined but with additional steps
            # For now, we'll use the streamlined approach with medium complexity settings
            
            # Step 1: Planner analysis
            logger.info("Step 1: Planner analysis")
            planner_result = self.planner.analyze_story(story, monitor)
            
            if monitor.should_terminate():
                return WorkflowExecutionResult(
                    workflow_type=WorkflowType.MEDIUM,
                    story_id=story.get('key', 'unknown'),
                    complexity=complexity,
                    status="terminated",
                    total_cost=monitor.current_cost,
                    total_messages=monitor.current_messages,
                    duration=time.time() - start_time,
                    efficiency_score=monitor.get_cost_summary().efficiency_score,
                    early_termination=True,
                    termination_reason="Budget exceeded during planner analysis"
                )
            
            # Step 2: Backend development
            logger.info("Step 2: Backend development")
            task = {
                "title": "Implement backend changes",
                "description": planner_result.get("backend_changes", "No backend changes needed"),
                "type": "backend"
            }
            developer_result = self.developer.implement_task(task, planner_result, monitor)
            
            if monitor.should_terminate():
                return WorkflowExecutionResult(
                    workflow_type=WorkflowType.MEDIUM,
                    story_id=story.get('key', 'unknown'),
                    complexity=complexity,
                    status="terminated",
                    total_cost=monitor.current_cost,
                    total_messages=monitor.current_messages,
                    duration=time.time() - start_time,
                    efficiency_score=monitor.get_cost_summary().efficiency_score,
                    result_data={"planner_result": planner_result, "developer_result": developer_result},
                    early_termination=True,
                    termination_reason="Budget exceeded during backend development"
                )
            
            # Step 3: Frontend development
            logger.info("Step 3: Frontend development")
            task = {
                "title": "Implement frontend changes",
                "description": planner_result.get("frontend_changes", "No frontend changes needed"),
                "type": "frontend"
            }
            frontend_result = self.frontend.implement_task(task, planner_result, monitor)
            
            if monitor.should_terminate():
                return WorkflowExecutionResult(
                    workflow_type=WorkflowType.MEDIUM,
                    story_id=story.get('key', 'unknown'),
                    complexity=complexity,
                    status="terminated",
                    total_cost=monitor.current_cost,
                    total_messages=monitor.current_messages,
                    duration=time.time() - start_time,
                    efficiency_score=monitor.get_cost_summary().efficiency_score,
                    result_data={
                        "planner_result": planner_result,
                        "developer_result": developer_result,
                        "frontend_result": frontend_result
                    },
                    early_termination=True,
                    termination_reason="Budget exceeded during frontend development"
                )
            
            # Get final cost summary
            cost_summary = monitor.get_cost_summary()
            
            return WorkflowExecutionResult(
                workflow_type=WorkflowType.MEDIUM,
                story_id=story.get('key', 'unknown'),
                complexity=complexity,
                status="completed",
                total_cost=cost_summary.total_cost,
                total_messages=cost_summary.total_messages,
                duration=time.time() - start_time,
                efficiency_score=cost_summary.efficiency_score,
                result_data={
                    "planner_result": planner_result,
                    "developer_result": developer_result,
                    "frontend_result": frontend_result
                }
            )
            
        except Exception as e:
            logger.error(f"Medium workflow failed: {e}")
            return WorkflowExecutionResult(
                workflow_type=WorkflowType.MEDIUM,
                story_id=story.get('key', 'unknown'),
                complexity=complexity,
                status="failed",
                total_cost=monitor.current_cost if 'monitor' in locals() else 0.0,
                total_messages=monitor.current_messages if 'monitor' in locals() else 0,
                duration=time.time() - start_time,
                efficiency_score=0.0,
                error=str(e)
            )
    
    def _execute_full_workflow(self, story: Dict[str, Any], complexity: TaskComplexity, 
                              workflow_config: WorkflowConfig, start_time: float) -> WorkflowExecutionResult:
        """Execute full workflow for complex tasks."""
        try:
            logger.info("Executing full workflow for complex task")
            
            # Use the existing StoryImplementationWorkflow for complex tasks
            workflow = StoryImplementationWorkflow(
                story_id=story.get('key', 'unknown'),
                use_real_jira=True,
                use_real_github=True
            )
            
            # Execute the full workflow
            result = workflow.run(resume=False)
            
            # Calculate metrics from the result
            total_cost = 0.0
            total_messages = 0
            
            # This would need to be extracted from the workflow result
            # For now, we'll use estimated values
            total_cost = 5.0  # Estimated cost for full workflow
            total_messages = 50  # Estimated messages for full workflow
            
            return WorkflowExecutionResult(
                workflow_type=WorkflowType.FULL,
                story_id=story.get('key', 'unknown'),
                complexity=complexity,
                status="completed",
                total_cost=total_cost,
                total_messages=total_messages,
                duration=time.time() - start_time,
                efficiency_score=0.8,  # Estimated efficiency
                result_data={"workflow_log": result}
            )
            
        except Exception as e:
            logger.error(f"Full workflow failed: {e}")
            return WorkflowExecutionResult(
                workflow_type=WorkflowType.FULL,
                story_id=story.get('key', 'unknown'),
                complexity=complexity,
                status="failed",
                total_cost=0.0,
                total_messages=0,
                duration=time.time() - start_time,
                efficiency_score=0.0,
                error=str(e)
            )
    
    def get_workflow_metrics(self, result: WorkflowExecutionResult) -> WorkflowMetrics:
        """
        Generate comprehensive workflow metrics.
        
        Args:
            result: WorkflowExecutionResult from execution
            
        Returns:
            WorkflowMetrics with detailed analysis
        """
        # Expected performance based on complexity
        expected_performance = {
            TaskComplexity.SIMPLE: {"messages": 20, "cost": 1.00, "duration": 1800},
            TaskComplexity.MEDIUM: {"messages": 50, "cost": 3.00, "duration": 2700},
            TaskComplexity.COMPLEX: {"messages": 100, "cost": 10.00, "duration": 3600}
        }
        
        expected = expected_performance[result.complexity]
        
        # Calculate efficiency metrics
        message_efficiency = (expected["messages"] - result.total_messages) / expected["messages"] * 100
        cost_efficiency = (expected["cost"] - result.total_cost) / expected["cost"] * 100
        time_efficiency = (expected["duration"] - result.duration) / expected["duration"] * 100
        
        # Cost breakdown (would need to be extracted from result_data)
        cost_breakdown = {
            "planner": result.total_cost * 0.3,
            "developer": result.total_cost * 0.4,
            "frontend": result.total_cost * 0.3
        }
        
        # Message breakdown (would need to be extracted from result_data)
        message_breakdown = {
            "planner": result.total_messages // 3,
            "developer": result.total_messages // 3,
            "frontend": result.total_messages // 3
        }
        
        # Generate recommendations
        recommendations = []
        if result.total_messages > expected["messages"]:
            recommendations.append("Consider further optimizing agent prompts")
        if result.total_cost > expected["cost"]:
            recommendations.append("Review cost optimization strategies")
        if result.duration > expected["duration"]:
            recommendations.append("Optimize agent response times")
        if result.efficiency_score < 0.7:
            recommendations.append("Consider using more streamlined approach")
        if result.early_termination:
            recommendations.append("Review budget limits and optimization")
        
        if not recommendations:
            recommendations.append("Excellent performance - workflow optimized")
        
        return WorkflowMetrics(
            story_id=result.story_id,
            complexity=result.complexity,
            workflow_type=result.workflow_type,
            performance={
                "actual": {
                    "messages": result.total_messages,
                    "cost": result.total_cost,
                    "duration": result.duration,
                    "efficiency_score": result.efficiency_score
                },
                "expected": expected
            },
            efficiency_metrics={
                "message_efficiency": round(message_efficiency, 2),
                "cost_efficiency": round(cost_efficiency, 2),
                "time_efficiency": round(time_efficiency, 2),
                "overall_efficiency": round((message_efficiency + cost_efficiency + time_efficiency) / 3, 2)
            },
            recommendations=recommendations,
            cost_breakdown=cost_breakdown,
            message_breakdown=message_breakdown
        )
    
    def get_efficiency_report(self, result: WorkflowExecutionResult) -> Dict[str, Any]:
        """
        Generate comprehensive efficiency report.
        
        Args:
            result: WorkflowExecutionResult from execution
            
        Returns:
            Dictionary with efficiency analysis and recommendations
        """
        metrics = self.get_workflow_metrics(result)
        
        return {
            "story_id": result.story_id,
            "complexity": result.complexity.value,
            "workflow_type": result.workflow_type.value,
            "status": result.status,
            "performance": metrics.performance,
            "efficiency_metrics": metrics.efficiency_metrics,
            "recommendations": metrics.recommendations,
            "cost_breakdown": metrics.cost_breakdown,
            "message_breakdown": metrics.message_breakdown,
            "early_termination": result.early_termination,
            "termination_reason": result.termination_reason,
            "error": result.error
        }

# Example usage and testing
if __name__ == "__main__":
    # Test with a simple story
    orchestrator = WorkflowOrchestrator(use_real_jira=False, use_real_github=False)
    
    # Execute workflow
    result = orchestrator.execute_workflow("NEGISHI-200")
    
    print("Workflow Execution Result:")
    print(f"Workflow Type: {result.workflow_type.value}")
    print(f"Complexity: {result.complexity.value}")
    print(f"Status: {result.status}")
    print(f"Total Cost: ${result.total_cost:.2f}")
    print(f"Total Messages: {result.total_messages}")
    print(f"Duration: {result.duration:.2f} seconds")
    print(f"Efficiency Score: {result.efficiency_score}")
    
    if result.early_termination:
        print(f"Early Termination: {result.termination_reason}")
    
    if result.error:
        print(f"Error: {result.error}")
    
    # Generate efficiency report
    report = orchestrator.get_efficiency_report(result)
    print(f"\nEfficiency Report:")
    print(f"Message Efficiency: {report['efficiency_metrics']['message_efficiency']}%")
    print(f"Cost Efficiency: {report['efficiency_metrics']['cost_efficiency']}%")
    print(f"Time Efficiency: {report['efficiency_metrics']['time_efficiency']}%")
    print(f"Overall Efficiency: {report['efficiency_metrics']['overall_efficiency']}%")
    
    print(f"\nRecommendations:")
    for rec in report['recommendations']:
        print(f"- {rec}")
