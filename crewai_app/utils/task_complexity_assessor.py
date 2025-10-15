"""
Task Complexity Assessment System

This module provides functionality to analyze Jira stories and determine their complexity
to optimize AI agent collaboration workflows. It prevents over-engineering of simple tasks
by routing them to streamlined workflows.

Based on analysis of workflow 18 (NEGISHI-200):
- Simple task: 2 acceptance criteria → 99 messages, $6.14 cost, 120+ seconds
- Target: 20 messages, $1.00 cost, 30 seconds (75% message reduction, 84% cost reduction)
"""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class TaskComplexity(Enum):
    """Task complexity levels based on acceptance criteria count and other factors."""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"

@dataclass
class ComplexityMetrics:
    """Metrics for task complexity assessment."""
    criteria_count: int
    story_points: Optional[int]
    has_technical_requirements: bool
    has_ui_requirements: bool
    has_integration_requirements: bool
    estimated_files: int
    complexity_score: float

@dataclass
class WorkflowConfig:
    """Configuration for workflow execution based on complexity."""
    max_messages: int
    max_cost: float
    max_duration: int  # seconds
    agents: List[str]
    workflow_type: str
    description: str

class TaskComplexityAssessor:
    """
    Analyzes Jira stories to determine complexity and recommend appropriate workflow.
    
    Prevents over-engineering by routing simple tasks to streamlined workflows
    and complex tasks to full collaborative workflows.
    """
    
    def __init__(self):
        self.complexity_thresholds = {
            "simple": {"max_criteria": 2, "max_points": 3},
            "medium": {"max_criteria": 5, "max_points": 8},
            "complex": {"max_criteria": float('inf'), "max_points": float('inf')}
        }
        
        self.workflow_configs = {
            TaskComplexity.SIMPLE: WorkflowConfig(
                max_messages=20,
                max_cost=1.00,
                max_duration=1800,  # 30 minutes
                agents=["planner", "developer", "frontend"],
                workflow_type="streamlined",
                description="3-step streamlined workflow for simple tasks"
            ),
            TaskComplexity.MEDIUM: WorkflowConfig(
                max_messages=50,
                max_cost=3.00,
                max_duration=2700,  # 45 minutes
                agents=["pm", "architect", "developer", "frontend", "tester"],
                workflow_type="medium",
                description="5-step medium workflow for moderate complexity"
            ),
            TaskComplexity.COMPLEX: WorkflowConfig(
                max_messages=100,
                max_cost=10.00,
                max_duration=3600,  # 60 minutes
                agents=["pm", "architect", "developer", "frontend", "tester", "reviewer"],
                workflow_type="full",
                description="6-step full collaborative workflow for complex tasks"
            )
        }
    
    def assess_complexity(self, story: Dict[str, Any]) -> TaskComplexity:
        """
        Assess the complexity of a Jira story based on multiple factors.
        
        Args:
            story: Jira story dictionary with fields and metadata
            
        Returns:
            TaskComplexity enum value
        """
        metrics = self._extract_complexity_metrics(story)
        
        # Primary factor: acceptance criteria count
        if metrics.criteria_count <= 2:
            return TaskComplexity.SIMPLE
        elif metrics.criteria_count <= 5:
            return TaskComplexity.MEDIUM
        else:
            return TaskComplexity.COMPLEX
    
    def get_workflow_config(self, complexity: TaskComplexity) -> WorkflowConfig:
        """
        Get workflow configuration for the given complexity level.
        
        Args:
            complexity: Task complexity level
            
        Returns:
            WorkflowConfig with limits and agent assignments
        """
        return self.workflow_configs[complexity]
    
    def _extract_complexity_metrics(self, story: Dict[str, Any]) -> ComplexityMetrics:
        """
        Extract complexity metrics from a Jira story.
        
        Args:
            story: Jira story dictionary
            
        Returns:
            ComplexityMetrics with extracted data
        """
        fields = story.get('fields', {})
        
        # Extract acceptance criteria
        criteria_count = self._count_acceptance_criteria(fields)
        
        # Extract story points
        story_points = self._extract_story_points(fields)
        
        # Analyze requirements
        description = fields.get('description', '') or ''
        summary = fields.get('summary', '') or ''
        full_text = f"{summary} {description}".lower()
        
        has_technical_requirements = self._has_technical_requirements(full_text)
        has_ui_requirements = self._has_ui_requirements(full_text)
        has_integration_requirements = self._has_integration_requirements(full_text)
        
        # Estimate files to be modified
        estimated_files = self._estimate_files_to_modify(full_text)
        
        # Calculate complexity score
        complexity_score = self._calculate_complexity_score(
            criteria_count, story_points, has_technical_requirements,
            has_ui_requirements, has_integration_requirements, estimated_files
        )
        
        return ComplexityMetrics(
            criteria_count=criteria_count,
            story_points=story_points,
            has_technical_requirements=has_technical_requirements,
            has_ui_requirements=has_ui_requirements,
            has_integration_requirements=has_integration_requirements,
            estimated_files=estimated_files,
            complexity_score=complexity_score
        )
    
    def _count_acceptance_criteria(self, fields: Dict[str, Any]) -> int:
        """Count acceptance criteria in the story."""
        # Look for acceptance criteria in custom fields or description
        description = fields.get('description', '') or ''
        
        # First, look for numbered lists (most common format)
        numbered_items = re.findall(r'^\s*\d+\.\s+', description, re.MULTILINE)
        if numbered_items:
            return len(numbered_items)
        
        # Common patterns for acceptance criteria
        criteria_patterns = [
            r'given\s+.*?\s+when\s+.*?\s+then\s+.*?',  # GWT format
            r'as a\s+.*?\s+i want\s+.*?\s+so that\s+.*?',  # User story format
            r'acceptance criteria:',  # Explicit mention
            r'ac:\s*',  # AC: prefix
            r'criteria:\s*',  # Criteria: prefix
        ]
        
        count = 0
        for pattern in criteria_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE | re.DOTALL)
            count += len(matches)
        
        # If no patterns found, assume 1 criteria
        return max(count, 1)  # At least 1 criteria assumed
    
    def _extract_story_points(self, fields: Dict[str, Any]) -> Optional[int]:
        """Extract story points from the story."""
        # Look for story points in custom fields
        for field_name, field_value in fields.items():
            if 'story' in field_name.lower() and 'point' in field_name.lower():
                try:
                    return int(field_value)
                except (ValueError, TypeError):
                    continue
        
        # Look for story points in description
        description = fields.get('description', '') or ''
        points_match = re.search(r'story points?:\s*(\d+)', description, re.IGNORECASE)
        if points_match:
            return int(points_match.group(1))
        
        return None
    
    def _has_technical_requirements(self, text: str) -> bool:
        """Check if story has technical requirements."""
        technical_keywords = [
            'api', 'database', 'backend', 'server', 'endpoint', 'service',
            'integration', 'authentication', 'authorization', 'security',
            'performance', 'scalability', 'architecture', 'design pattern'
        ]
        return any(keyword in text for keyword in technical_keywords)
    
    def _has_ui_requirements(self, text: str) -> bool:
        """Check if story has UI requirements."""
        ui_keywords = [
            'ui', 'user interface', 'frontend', 'component', 'page',
            'button', 'form', 'modal', 'dialog', 'layout', 'design',
            'responsive', 'mobile', 'desktop', 'styling', 'css'
        ]
        return any(keyword in text for keyword in ui_keywords)
    
    def _has_integration_requirements(self, text: str) -> bool:
        """Check if story has integration requirements."""
        integration_keywords = [
            'integrate', 'connect', 'api call', 'external service',
            'third party', 'webhook', 'callback', 'sync', 'async',
            'real-time', 'streaming', 'queue', 'message'
        ]
        return any(keyword in text for keyword in integration_keywords)
    
    def _estimate_files_to_modify(self, text: str) -> int:
        """Estimate number of files that need to be modified."""
        file_indicators = [
            'component', 'service', 'controller', 'model', 'view',
            'template', 'style', 'test', 'spec', 'config'
        ]
        
        count = 0
        for indicator in file_indicators:
            if indicator in text:
                count += 1
        
        return max(count, 1)  # At least 1 file assumed
    
    def _calculate_complexity_score(self, criteria_count: int, story_points: Optional[int],
                                  has_technical: bool, has_ui: bool, has_integration: bool,
                                  estimated_files: int) -> float:
        """Calculate overall complexity score."""
        score = criteria_count * 0.4  # 40% weight to criteria count
        
        if story_points:
            score += story_points * 0.2  # 20% weight to story points
        
        # 10% weight each for requirement types
        if has_technical:
            score += 0.1
        if has_ui:
            score += 0.1
        if has_integration:
            score += 0.1
        
        # 10% weight for estimated files
        score += estimated_files * 0.1
        
        return round(score, 2)
    
    def get_complexity_analysis(self, story: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed complexity analysis for a story.
        
        Args:
            story: Jira story dictionary
            
        Returns:
            Dictionary with complexity analysis details
        """
        complexity = self.assess_complexity(story)
        metrics = self._extract_complexity_metrics(story)
        config = self.get_workflow_config(complexity)
        
        return {
            "complexity": complexity.value,
            "metrics": {
                "criteria_count": metrics.criteria_count,
                "story_points": metrics.story_points,
                "has_technical_requirements": metrics.has_technical_requirements,
                "has_ui_requirements": metrics.has_ui_requirements,
                "has_integration_requirements": metrics.has_integration_requirements,
                "estimated_files": metrics.estimated_files,
                "complexity_score": metrics.complexity_score
            },
            "workflow_config": {
                "max_messages": config.max_messages,
                "max_cost": config.max_cost,
                "max_duration": config.max_duration,
                "agents": config.agents,
                "workflow_type": config.workflow_type,
                "description": config.description
            },
            "recommendation": self._get_recommendation(complexity, metrics)
        }
    
    def _get_recommendation(self, complexity: TaskComplexity, metrics: ComplexityMetrics) -> str:
        """Get recommendation based on complexity analysis."""
        if complexity == TaskComplexity.SIMPLE:
            return (
                f"Simple task detected ({metrics.criteria_count} criteria). "
                f"Use streamlined workflow to prevent over-engineering. "
                f"Expected: ≤20 messages, ≤$1.00 cost, ≤30 minutes."
            )
        elif complexity == TaskComplexity.MEDIUM:
            return (
                f"Medium complexity task ({metrics.criteria_count} criteria). "
                f"Use medium workflow for balanced approach. "
                f"Expected: ≤50 messages, ≤$3.00 cost, ≤45 minutes."
            )
        else:
            return (
                f"Complex task detected ({metrics.criteria_count} criteria). "
                f"Use full collaborative workflow for comprehensive implementation. "
                f"Expected: ≤100 messages, ≤$10.00 cost, ≤60 minutes."
            )

# Example usage and testing
if __name__ == "__main__":
    # Test with a simple story (like NEGISHI-200)
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
    
    assessor = TaskComplexityAssessor()
    analysis = assessor.get_complexity_analysis(simple_story)
    
    print("Complexity Analysis:")
    print(f"Complexity: {analysis['complexity']}")
    print(f"Criteria Count: {analysis['metrics']['criteria_count']}")
    print(f"Recommendation: {analysis['recommendation']}")
    print(f"Workflow Type: {analysis['workflow_config']['workflow_type']}")
    print(f"Max Messages: {analysis['workflow_config']['max_messages']}")
    print(f"Max Cost: ${analysis['workflow_config']['max_cost']}")
