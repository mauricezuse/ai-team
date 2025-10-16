"""
Efficiency Reporting and Metrics System

This module provides comprehensive efficiency reporting and metrics analysis
for AI agent workflows. It tracks performance, identifies optimization opportunities,
and generates actionable recommendations.

Based on analysis of workflow 18 (NEGISHI-200):
- Simple task: 99 messages, $6.14 cost, 120+ seconds (12x over-engineered)
- Target: 20 messages, $1.00 cost, 30 seconds (75% message reduction, 84% cost reduction)
"""

import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics

from crewai_app.utils.task_complexity_assessor import TaskComplexity
from crewai_app.utils.cost_monitor import CostMonitor, CostSummary
from crewai_app.workflows.workflow_orchestrator import WorkflowExecutionResult, WorkflowType

class EfficiencyLevel(Enum):
    """Efficiency level classifications."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"

@dataclass
class PerformanceBenchmark:
    """Performance benchmarks for different complexity levels."""
    simple: Dict[str, float] = field(default_factory=lambda: {
        "max_messages": 20,
        "max_cost": 1.00,
        "max_duration": 1800,  # 30 minutes
        "target_efficiency": 0.9
    })
    medium: Dict[str, float] = field(default_factory=lambda: {
        "max_messages": 50,
        "max_cost": 3.00,
        "max_duration": 2700,  # 45 minutes
        "target_efficiency": 0.8
    })
    complex: Dict[str, float] = field(default_factory=lambda: {
        "max_messages": 100,
        "max_cost": 10.00,
        "max_duration": 3600,  # 60 minutes
        "target_efficiency": 0.7
    })

@dataclass
class EfficiencyMetrics:
    """Comprehensive efficiency metrics."""
    message_efficiency: float
    cost_efficiency: float
    time_efficiency: float
    overall_efficiency: float
    efficiency_level: EfficiencyLevel
    performance_score: float
    optimization_potential: float

@dataclass
class OptimizationRecommendation:
    """Optimization recommendation with priority and impact."""
    category: str
    title: str
    description: str
    priority: str  # "high", "medium", "low"
    impact: str   # "high", "medium", "low"
    effort: str   # "high", "medium", "low"
    expected_improvement: float
    implementation_steps: List[str]

@dataclass
class EfficiencyReport:
    """Comprehensive efficiency report."""
    story_id: str
    complexity: TaskComplexity
    workflow_type: WorkflowType
    execution_result: WorkflowExecutionResult
    metrics: EfficiencyMetrics
    benchmarks: PerformanceBenchmark
    recommendations: List[OptimizationRecommendation]
    cost_breakdown: Dict[str, float]
    message_breakdown: Dict[str, int]
    performance_trends: Dict[str, List[float]]
    generated_at: float
    report_version: str = "1.0"

# Shared in-memory history for tests and simple telemetry
report_history: List["EfficiencyReport"] = []  # type: ignore[name-defined]
performance_trends: Dict[str, List[float]] = {}

class EfficiencyReporter:
    """
    Comprehensive efficiency reporting and metrics analysis.
    
    Provides detailed analysis of workflow performance, identifies optimization
    opportunities, and generates actionable recommendations for improvement.
    """
    
    def __init__(self):
        self.benchmarks = PerformanceBenchmark()
        # Use shared module-level history for visibility in tests
        global report_history, performance_trends
        self.report_history = report_history
        self.performance_trends = performance_trends
        
    def generate_efficiency_report(self, execution_result: WorkflowExecutionResult) -> EfficiencyReport:
        """
        Generate comprehensive efficiency report for workflow execution.
        
        Args:
            execution_result: WorkflowExecutionResult from execution
            
        Returns:
            EfficiencyReport with detailed analysis
        """
        # Calculate efficiency metrics
        metrics = self._calculate_efficiency_metrics(execution_result)
        
        # Get performance benchmarks
        benchmarks = self._get_performance_benchmarks(execution_result.complexity)
        
        # Generate optimization recommendations
        recommendations = self._generate_optimization_recommendations(execution_result, metrics)
        
        # Calculate cost and message breakdowns
        cost_breakdown = self._calculate_cost_breakdown(execution_result)
        message_breakdown = self._calculate_message_breakdown(execution_result)
        
        # Get performance trends
        performance_trends = self._get_performance_trends(execution_result.story_id)
        
        # Create efficiency report
        report = EfficiencyReport(
            story_id=execution_result.story_id,
            complexity=execution_result.complexity,
            workflow_type=execution_result.workflow_type,
            execution_result=execution_result,
            metrics=metrics,
            benchmarks=benchmarks,
            recommendations=recommendations,
            cost_breakdown=cost_breakdown,
            message_breakdown=message_breakdown,
            performance_trends=performance_trends,
            generated_at=time.time(),
            report_version="1.0"
        )
        
        # Store report in history
        self.report_history.append(report)
        
        return report
    
    def _calculate_efficiency_metrics(self, result: WorkflowExecutionResult) -> EfficiencyMetrics:
        """Calculate comprehensive efficiency metrics."""
        # Get benchmarks for complexity level
        benchmarks = self._get_performance_benchmarks(result.complexity)
        
        # Calculate efficiency ratios
        message_efficiency = max(0, (benchmarks["max_messages"] - result.total_messages) / benchmarks["max_messages"])
        cost_efficiency = max(0, (benchmarks["max_cost"] - result.total_cost) / benchmarks["max_cost"])
        time_efficiency = max(0, (benchmarks["max_duration"] - result.duration) / benchmarks["max_duration"])
        
        # Calculate overall efficiency
        overall_efficiency = (message_efficiency + cost_efficiency + time_efficiency) / 3
        
        # Determine efficiency level
        if overall_efficiency >= 0.9:
            efficiency_level = EfficiencyLevel.EXCELLENT
        elif overall_efficiency >= 0.8:
            efficiency_level = EfficiencyLevel.GOOD
        elif overall_efficiency >= 0.6:
            efficiency_level = EfficiencyLevel.FAIR
        elif overall_efficiency >= 0.4:
            efficiency_level = EfficiencyLevel.POOR
        else:
            efficiency_level = EfficiencyLevel.CRITICAL
        
        # Calculate performance score
        performance_score = overall_efficiency * 100
        
        # Calculate optimization potential
        optimization_potential = max(0, 1.0 - overall_efficiency)
        
        return EfficiencyMetrics(
            message_efficiency=round(message_efficiency, 3),
            cost_efficiency=round(cost_efficiency, 3),
            time_efficiency=round(time_efficiency, 3),
            overall_efficiency=round(overall_efficiency, 3),
            efficiency_level=efficiency_level,
            performance_score=round(performance_score, 2),
            optimization_potential=round(optimization_potential, 3)
        )
    
    def _get_performance_benchmarks(self, complexity: TaskComplexity) -> Dict[str, float]:
        """Get performance benchmarks for complexity level."""
        if complexity == TaskComplexity.SIMPLE:
            return self.benchmarks.simple
        elif complexity == TaskComplexity.MEDIUM:
            return self.benchmarks.medium
        else:
            return self.benchmarks.complex
    
    def _generate_optimization_recommendations(self, result: WorkflowExecutionResult, 
                                            metrics: EfficiencyMetrics) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations based on performance."""
        recommendations = []
        
        # Message efficiency recommendations
        if metrics.message_efficiency < 0.8:
            recommendations.append(OptimizationRecommendation(
                category="Message Efficiency",
                title="Optimize Agent Prompts",
                description="Reduce message count by optimizing agent prompts and reducing unnecessary iterations",
                priority="high" if metrics.message_efficiency < 0.5 else "medium",
                impact="high",
                effort="medium",
                expected_improvement=0.2,
                implementation_steps=[
                    "Review agent prompts for verbosity",
                    "Implement message compression techniques",
                    "Add early termination conditions",
                    "Optimize agent collaboration patterns"
                ]
            ))
        
        # Cost efficiency recommendations
        if metrics.cost_efficiency < 0.8:
            recommendations.append(OptimizationRecommendation(
                category="Cost Efficiency",
                title="Implement Cost Optimization",
                description="Reduce costs by optimizing token usage and implementing cost-aware prompts",
                priority="high" if metrics.cost_efficiency < 0.5 else "medium",
                impact="high",
                effort="medium",
                expected_improvement=0.3,
                implementation_steps=[
                    "Implement token counting and optimization",
                    "Use cost-aware prompt engineering",
                    "Add cost monitoring and alerts",
                    "Optimize model selection for tasks"
                ]
            ))
        
        # Time efficiency recommendations
        if metrics.time_efficiency < 0.8:
            recommendations.append(OptimizationRecommendation(
                category="Time Efficiency",
                title="Optimize Response Times",
                description="Reduce execution time by optimizing agent response times and parallel processing",
                priority="medium",
                impact="medium",
                effort="high",
                expected_improvement=0.15,
                implementation_steps=[
                    "Implement parallel agent execution",
                    "Optimize API response times",
                    "Add caching for repeated operations",
                    "Streamline workflow steps"
                ]
            ))
        
        # Overall efficiency recommendations
        if metrics.overall_efficiency < 0.7:
            recommendations.append(OptimizationRecommendation(
                category="Overall Efficiency",
                title="Workflow Optimization",
                description="Implement comprehensive workflow optimization for better overall performance",
                priority="high",
                impact="high",
                effort="high",
                expected_improvement=0.25,
                implementation_steps=[
                    "Review and optimize workflow steps",
                    "Implement complexity-aware routing",
                    "Add real-time monitoring and adjustment",
                    "Optimize agent collaboration patterns"
                ]
            ))
        
        # Early termination recommendations
        if result.early_termination:
            recommendations.append(OptimizationRecommendation(
                category="Early Termination",
                title="Budget Management",
                description="Improve budget management to prevent early termination and ensure completion",
                priority="high",
                impact="high",
                effort="medium",
                expected_improvement=0.4,
                implementation_steps=[
                    "Review and adjust budget limits",
                    "Implement dynamic budget allocation",
                    "Add budget monitoring and alerts",
                    "Optimize cost distribution across agents"
                ]
            ))
        
        # Complexity-specific recommendations
        if result.complexity == TaskComplexity.SIMPLE and result.workflow_type != WorkflowType.STREAMLINED:
            recommendations.append(OptimizationRecommendation(
                category="Complexity Routing",
                title="Use Streamlined Workflow",
                description="Route simple tasks to streamlined workflow to prevent over-engineering",
                priority="high",
                impact="high",
                effort="low",
                expected_improvement=0.5,
                implementation_steps=[
                    "Implement complexity assessment",
                    "Route simple tasks to streamlined workflow",
                    "Add complexity-aware agent selection",
                    "Monitor and adjust routing logic"
                ]
            ))
        
        return recommendations
    
    def _calculate_cost_breakdown(self, result: WorkflowExecutionResult) -> Dict[str, float]:
        """Calculate cost breakdown by agent and step."""
        if result.result_data and "cost_breakdown" in result.result_data:
            return result.result_data["cost_breakdown"]
        
        # Estimate cost breakdown based on workflow type
        if result.workflow_type == WorkflowType.STREAMLINED:
            return {
                "planner": result.total_cost * 0.3,
                "developer": result.total_cost * 0.4,
                "frontend": result.total_cost * 0.3
            }
        elif result.workflow_type == WorkflowType.MEDIUM:
            return {
                "planner": result.total_cost * 0.2,
                "developer": result.total_cost * 0.3,
                "frontend": result.total_cost * 0.2,
                "tester": result.total_cost * 0.2,
                "reviewer": result.total_cost * 0.1
            }
        else:
            return {
                "pm": result.total_cost * 0.15,
                "architect": result.total_cost * 0.15,
                "developer": result.total_cost * 0.25,
                "frontend": result.total_cost * 0.15,
                "tester": result.total_cost * 0.15,
                "reviewer": result.total_cost * 0.15
            }
    
    def _calculate_message_breakdown(self, result: WorkflowExecutionResult) -> Dict[str, int]:
        """Calculate message breakdown by agent and step."""
        if result.result_data and "message_breakdown" in result.result_data:
            return result.result_data["message_breakdown"]
        
        # Estimate message breakdown based on workflow type
        if result.workflow_type == WorkflowType.STREAMLINED:
            return {
                "planner": result.total_messages // 3,
                "developer": result.total_messages // 3,
                "frontend": result.total_messages // 3
            }
        elif result.workflow_type == WorkflowType.MEDIUM:
            return {
                "planner": result.total_messages // 5,
                "developer": result.total_messages // 5,
                "frontend": result.total_messages // 5,
                "tester": result.total_messages // 5,
                "reviewer": result.total_messages // 5
            }
        else:
            return {
                "pm": result.total_messages // 6,
                "architect": result.total_messages // 6,
                "developer": result.total_messages // 6,
                "frontend": result.total_messages // 6,
                "tester": result.total_messages // 6,
                "reviewer": result.total_messages // 6
            }
    
    def _get_performance_trends(self, story_id: str) -> Dict[str, List[float]]:
        """Get performance trends for story ID."""
        if story_id in self.performance_trends:
            return self.performance_trends[story_id]
        
        # Return empty trends if no history
        return {
            "efficiency": [],
            "cost": [],
            "messages": [],
            "duration": []
        }
    
    def get_optimization_summary(self, report: EfficiencyReport) -> Dict[str, Any]:
        """Get optimization summary from efficiency report."""
        high_priority_recs = [r for r in report.recommendations if r.priority == "high"]
        medium_priority_recs = [r for r in report.recommendations if r.priority == "medium"]
        
        return {
            "overall_efficiency": report.metrics.overall_efficiency,
            "efficiency_level": report.metrics.efficiency_level.value,
            "performance_score": report.metrics.performance_score,
            "optimization_potential": report.metrics.optimization_potential,
            "high_priority_recommendations": len(high_priority_recs),
            "medium_priority_recommendations": len(medium_priority_recs),
            "total_recommendations": len(report.recommendations),
            "expected_improvement": sum(r.expected_improvement for r in report.recommendations),
            "critical_issues": [
                r.title for r in report.recommendations 
                if r.priority == "high" and r.impact == "high"
            ]
        }
    
    def export_report(self, report: EfficiencyReport, format: str = "json") -> str:
        """Export efficiency report in specified format."""
        if format == "json":
            return json.dumps({
                "story_id": report.story_id,
                "complexity": report.complexity.value,
                "workflow_type": report.workflow_type.value,
                "status": report.execution_result.status,
                "metrics": {
                    "message_efficiency": report.metrics.message_efficiency,
                    "cost_efficiency": report.metrics.cost_efficiency,
                    "time_efficiency": report.metrics.time_efficiency,
                    "overall_efficiency": report.metrics.overall_efficiency,
                    "efficiency_level": report.metrics.efficiency_level.value,
                    "performance_score": report.metrics.performance_score,
                    "optimization_potential": report.metrics.optimization_potential
                },
                "performance": {
                    "total_cost": report.execution_result.total_cost,
                    "total_messages": report.execution_result.total_messages,
                    "duration": report.execution_result.duration,
                    "efficiency_score": report.execution_result.efficiency_score
                },
                "recommendations": [
                    {
                        "category": r.category,
                        "title": r.title,
                        "description": r.description,
                        "priority": r.priority,
                        "impact": r.impact,
                        "effort": r.effort,
                        "expected_improvement": r.expected_improvement,
                        "implementation_steps": r.implementation_steps
                    }
                    for r in report.recommendations
                ],
                "cost_breakdown": report.cost_breakdown,
                "message_breakdown": report.message_breakdown,
                "generated_at": report.generated_at,
                "report_version": report.report_version
            }, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def get_historical_analysis(self, story_id: str) -> Dict[str, Any]:
        """Get historical analysis for story ID."""
        story_reports = [r for r in self.report_history if r.story_id == story_id]
        
        if not story_reports:
            return {"message": "No historical data available"}
        
        # Calculate trends
        efficiency_trends = [r.metrics.overall_efficiency for r in story_reports]
        cost_trends = [r.execution_result.total_cost for r in story_reports]
        message_trends = [r.execution_result.total_messages for r in story_reports]
        duration_trends = [r.execution_result.duration for r in story_reports]
        
        return {
            "total_executions": len(story_reports),
            "average_efficiency": statistics.mean(efficiency_trends),
            "efficiency_trend": "improving" if len(efficiency_trends) > 1 and efficiency_trends[-1] > efficiency_trends[0] else "declining",
            "average_cost": statistics.mean(cost_trends),
            "average_messages": statistics.mean(message_trends),
            "average_duration": statistics.mean(duration_trends),
            "best_performance": max(efficiency_trends),
            "worst_performance": min(efficiency_trends),
            "performance_volatility": statistics.stdev(efficiency_trends) if len(efficiency_trends) > 1 else 0
        }

# Example usage and testing
if __name__ == "__main__":
    from crewai_app.workflows.workflow_orchestrator import WorkflowExecutionResult, WorkflowType
    from crewai_app.utils.task_complexity_assessor import TaskComplexity
    
    # Create test execution result
    test_result = WorkflowExecutionResult(
        workflow_type=WorkflowType.STREAMLINED,
        story_id="NEGISHI-200",
        complexity=TaskComplexity.SIMPLE,
        status="completed",
        total_cost=0.75,
        total_messages=15,
        duration=1200,  # 20 minutes
        efficiency_score=0.85
    )
    
    # Create efficiency reporter
    reporter = EfficiencyReporter()
    
    # Generate efficiency report
    report = reporter.generate_efficiency_report(test_result)
    
    print("Efficiency Report:")
    print(f"Story ID: {report.story_id}")
    print(f"Complexity: {report.complexity.value}")
    print(f"Workflow Type: {report.workflow_type.value}")
    print(f"Overall Efficiency: {report.metrics.overall_efficiency}")
    print(f"Efficiency Level: {report.metrics.efficiency_level.value}")
    print(f"Performance Score: {report.metrics.performance_score}")
    print(f"Optimization Potential: {report.metrics.optimization_potential}")
    
    print(f"\nRecommendations ({len(report.recommendations)}):")
    for rec in report.recommendations:
        print(f"- {rec.title} ({rec.priority} priority, {rec.impact} impact)")
        print(f"  {rec.description}")
        print(f"  Expected Improvement: {rec.expected_improvement}")
    
    # Get optimization summary
    summary = reporter.get_optimization_summary(report)
    print(f"\nOptimization Summary:")
    print(f"High Priority Recommendations: {summary['high_priority_recommendations']}")
    print(f"Medium Priority Recommendations: {summary['medium_priority_recommendations']}")
    print(f"Total Recommendations: {summary['total_recommendations']}")
    print(f"Expected Improvement: {summary['expected_improvement']}")
    
    # Export report
    json_report = reporter.export_report(report, "json")
    print(f"\nJSON Report Length: {len(json_report)} characters")
