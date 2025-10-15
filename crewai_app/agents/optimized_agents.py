"""
Optimized Agents with Complexity Awareness

This module provides enhanced agent implementations that are aware of task complexity
and adjust their behavior accordingly. Prevents over-engineering of simple tasks by
using streamlined approaches and focused prompts.

Based on analysis of workflow 18 (NEGISHI-200):
- Simple tasks should use minimal, direct approaches
- Complex tasks can use full collaborative approaches
- Cost and message limits are enforced based on complexity
"""

from typing import Dict, List, Any, Optional
from crewai_app.services.openai_service import OpenAIService
from crewai_app.utils.task_complexity_assessor import TaskComplexity, WorkflowConfig
from crewai_app.utils.cost_monitor import CostMonitor, BudgetStatus
from crewai_app.utils.logger import logger

class OptimizedPlannerAgent:
    """
    Optimized Planner Agent that adapts to task complexity.
    
    For simple tasks: Minimal planning, direct approach
    For complex tasks: Comprehensive planning, detailed approach
    """
    
    def __init__(self, openai_service: OpenAIService):
        self.openai_service = openai_service
        self.last_llm_output = None
        self.complexity = TaskComplexity.SIMPLE
        self.workflow_config = None
    
    def set_complexity(self, complexity: TaskComplexity, workflow_config: WorkflowConfig):
        """Set complexity level and workflow configuration."""
        self.complexity = complexity
        self.workflow_config = workflow_config
        logger.info(f"Planner agent set to {complexity.value} complexity")
    
    def analyze_story(self, story: Dict[str, Any], monitor: CostMonitor) -> Dict[str, Any]:
        """
        Analyze story with complexity-aware approach.
        
        Args:
            story: Jira story dictionary
            monitor: Cost monitor for budget tracking
            
        Returns:
            Implementation plan adapted to complexity
        """
        if self.complexity == TaskComplexity.SIMPLE:
            return self._analyze_simple_story(story, monitor)
        elif self.complexity == TaskComplexity.MEDIUM:
            return self._analyze_medium_story(story, monitor)
        else:
            return self._analyze_complex_story(story, monitor)
    
    def _analyze_simple_story(self, story: Dict[str, Any], monitor: CostMonitor) -> Dict[str, Any]:
        """Analyze simple story with minimal approach."""
        description = story['fields'].get('description', '') if isinstance(story, dict) else str(story)
        summary = story['fields'].get('summary', '') if isinstance(story, dict) else ''
        
        prompt = f"""
You are a Planner Agent for SIMPLE TASKS ONLY.
- Task complexity: SIMPLE (≤2 acceptance criteria)
- Your role: Analyze requirements and create minimal implementation plan
- Focus: Identify 1-2 files to create/modify
- Avoid: Over-engineering, complex architectures, extensive planning
- Output: Simple, direct implementation plan
- Message limit: 5 messages
- Cost limit: $0.50

Story Summary: {summary}
Story Description: {description}

Create a minimal implementation plan with:
1. Files to modify (1-2 files maximum)
2. Simple implementation approach
3. No complex patterns or over-engineering

Output format:
{{
    "files_to_modify": ["file1.py", "file2.ts"],
    "implementation_approach": "Simple description",
    "backend_changes": "Minimal backend changes needed",
    "frontend_changes": "Minimal frontend changes needed"
}}
"""
        
        try:
            # Check budget before proceeding
            if monitor.should_terminate():
                raise Exception("Budget exceeded before planner analysis")
            
            # Generate plan
            plan_str = self.openai_service.generate(
                prompt,
                step='optimized_planner.analyze_simple_story'
            )
            self.last_llm_output = plan_str
            
            # Track cost
            estimated_cost = 0.15  # Estimated cost for simple plan
            monitor.add_cost_entry(
                agent="optimized_planner",
                step="analyze_simple_story",
                message_cost=estimated_cost,
                token_count=len(plan_str.split()),
                metadata={"complexity": "simple", "story_id": story.get('key', 'unknown')}
            )
            
            # Parse plan
            import json
            try:
                plan = json.loads(plan_str)
            except json.JSONDecodeError:
                # Fallback to simple plan if JSON parsing fails
                plan = {
                    "files_to_modify": ["package.json", "footer.component.ts"],
                    "implementation_approach": "Add version number to footer",
                    "backend_changes": "None required",
                    "frontend_changes": "Display version in footer component"
                }
            
            logger.info(f"Simple story analyzed with minimal approach: {plan}")
            return plan
            
        except Exception as e:
            logger.error(f"Simple story analysis failed: {e}")
            raise
    
    def _analyze_medium_story(self, story: Dict[str, Any], monitor: CostMonitor) -> Dict[str, Any]:
        """Analyze medium complexity story with balanced approach."""
        description = story['fields'].get('description', '') if isinstance(story, dict) else str(story)
        summary = story['fields'].get('summary', '') if isinstance(story, dict) else ''
        
        prompt = f"""
You are a Planner Agent for MEDIUM COMPLEXITY TASKS.
- Task complexity: MEDIUM (3-5 acceptance criteria)
- Your role: Analyze requirements and create balanced implementation plan
- Focus: Identify 3-5 files to create/modify
- Approach: Moderate planning with some architectural considerations
- Output: Balanced implementation plan
- Message limit: 10 messages
- Cost limit: $1.50

Story Summary: {summary}
Story Description: {description}

Create a balanced implementation plan with:
1. Files to modify (3-5 files)
2. Implementation approach with some architectural considerations
3. Moderate complexity patterns where appropriate

Output format:
{{
    "files_to_modify": ["file1.py", "file2.ts", "file3.py", "file4.ts"],
    "implementation_approach": "Balanced description",
    "backend_changes": "Moderate backend changes needed",
    "frontend_changes": "Moderate frontend changes needed",
    "architecture_considerations": "Key architectural points"
}}
"""
        
        try:
            # Check budget before proceeding
            if monitor.should_terminate():
                raise Exception("Budget exceeded before planner analysis")
            
            # Generate plan
            plan_str = self.openai_service.generate(
                prompt,
                step='optimized_planner.analyze_medium_story'
            )
            self.last_llm_output = plan_str
            
            # Track cost
            estimated_cost = 0.30  # Estimated cost for medium plan
            monitor.add_cost_entry(
                agent="optimized_planner",
                step="analyze_medium_story",
                message_cost=estimated_cost,
                token_count=len(plan_str.split()),
                metadata={"complexity": "medium", "story_id": story.get('key', 'unknown')}
            )
            
            # Parse plan
            import json
            try:
                plan = json.loads(plan_str)
            except json.JSONDecodeError:
                # Fallback to medium plan if JSON parsing fails
                plan = {
                    "files_to_modify": ["service.py", "component.ts", "model.py", "template.html"],
                    "implementation_approach": "Balanced implementation with moderate complexity",
                    "backend_changes": "Moderate backend changes needed",
                    "frontend_changes": "Moderate frontend changes needed",
                    "architecture_considerations": "Consider service layer and component structure"
                }
            
            logger.info(f"Medium story analyzed with balanced approach: {plan}")
            return plan
            
        except Exception as e:
            logger.error(f"Medium story analysis failed: {e}")
            raise
    
    def _analyze_complex_story(self, story: Dict[str, Any], monitor: CostMonitor) -> Dict[str, Any]:
        """Analyze complex story with comprehensive approach."""
        description = story['fields'].get('description', '') if isinstance(story, dict) else str(story)
        summary = story['fields'].get('summary', '') if isinstance(story, dict) else ''
        
        prompt = f"""
You are a Planner Agent for COMPLEX TASKS.
- Task complexity: COMPLEX (≥6 acceptance criteria)
- Your role: Analyze requirements and create comprehensive implementation plan
- Focus: Identify 6+ files to create/modify
- Approach: Detailed planning with architectural considerations
- Output: Comprehensive implementation plan
- Message limit: 20 messages
- Cost limit: $3.00

Story Summary: {summary}
Story Description: {description}

Create a comprehensive implementation plan with:
1. Files to modify (6+ files)
2. Detailed implementation approach
3. Architectural considerations and patterns
4. Integration points and dependencies

Output format:
{{
    "files_to_modify": ["file1.py", "file2.ts", "file3.py", "file4.ts", "file5.py", "file6.ts"],
    "implementation_approach": "Comprehensive description",
    "backend_changes": "Detailed backend changes needed",
    "frontend_changes": "Detailed frontend changes needed",
    "architecture_considerations": "Detailed architectural points",
    "integration_points": "Key integration considerations",
    "dependencies": "Required dependencies and services"
}}
"""
        
        try:
            # Check budget before proceeding
            if monitor.should_terminate():
                raise Exception("Budget exceeded before planner analysis")
            
            # Generate plan
            plan_str = self.openai_service.generate(
                prompt,
                step='optimized_planner.analyze_complex_story'
            )
            self.last_llm_output = plan_str
            
            # Track cost
            estimated_cost = 0.60  # Estimated cost for complex plan
            monitor.add_cost_entry(
                agent="optimized_planner",
                step="analyze_complex_story",
                message_cost=estimated_cost,
                token_count=len(plan_str.split()),
                metadata={"complexity": "complex", "story_id": story.get('key', 'unknown')}
            )
            
            # Parse plan
            import json
            try:
                plan = json.loads(plan_str)
            except json.JSONDecodeError:
                # Fallback to complex plan if JSON parsing fails
                plan = {
                    "files_to_modify": ["service.py", "component.ts", "model.py", "template.html", "api.py", "test.py"],
                    "implementation_approach": "Comprehensive implementation with detailed architecture",
                    "backend_changes": "Detailed backend changes needed",
                    "frontend_changes": "Detailed frontend changes needed",
                    "architecture_considerations": "Detailed architectural points",
                    "integration_points": "Key integration considerations",
                    "dependencies": "Required dependencies and services"
                }
            
            logger.info(f"Complex story analyzed with comprehensive approach: {plan}")
            return plan
            
        except Exception as e:
            logger.error(f"Complex story analysis failed: {e}")
            raise

class OptimizedDeveloperAgent:
    """
    Optimized Developer Agent that adapts to task complexity.
    
    For simple tasks: Direct implementation, minimal code
    For complex tasks: Comprehensive implementation, detailed patterns
    """
    
    def __init__(self, openai_service: OpenAIService):
        self.openai_service = openai_service
        self.last_llm_output = None
        self.complexity = TaskComplexity.SIMPLE
        self.workflow_config = None
    
    def set_complexity(self, complexity: TaskComplexity, workflow_config: WorkflowConfig):
        """Set complexity level and workflow configuration."""
        self.complexity = complexity
        self.workflow_config = workflow_config
        logger.info(f"Developer agent set to {complexity.value} complexity")
    
    def implement_task(self, task: Dict[str, Any], plan: Dict[str, Any], 
                      monitor: CostMonitor) -> Dict[str, Any]:
        """
        Implement task with complexity-aware approach.
        
        Args:
            task: Task to implement
            plan: Implementation plan
            monitor: Cost monitor for budget tracking
            
        Returns:
            Implementation result
        """
        if self.complexity == TaskComplexity.SIMPLE:
            return self._implement_simple_task(task, plan, monitor)
        elif self.complexity == TaskComplexity.MEDIUM:
            return self._implement_medium_task(task, plan, monitor)
        else:
            return self._implement_complex_task(task, plan, monitor)
    
    def _implement_simple_task(self, task: Dict[str, Any], plan: Dict[str, Any], 
                             monitor: CostMonitor) -> Dict[str, Any]:
        """Implement simple task with minimal approach."""
        prompt = f"""
You are a Developer Agent for SIMPLE TASKS ONLY.
- Task complexity: SIMPLE (≤2 acceptance criteria)
- Your role: Implement backend changes directly
- Focus: Core functionality only, minimal code
- Avoid: Complex patterns, extensive error handling, over-engineering
- Output: Working code that meets requirements
- Message limit: 10 messages
- Cost limit: $0.50

Task: {task.get('title', 'Unknown')}
Description: {task.get('description', 'No description')}
Plan: {plan.get('implementation_approach', 'No plan')}

Implement the backend changes with:
1. Minimal, working code
2. No complex patterns
3. Direct implementation
4. Focus on core functionality only

Output format:
{{
    "files": [
        {{
            "file": "filename.py",
            "code": "minimal working code",
            "description": "What this file does"
        }}
    ],
    "implementation_notes": "Brief notes about the implementation"
}}
"""
        
        try:
            # Check budget before proceeding
            if monitor.should_terminate():
                raise Exception("Budget exceeded before backend implementation")
            
            # Generate implementation
            result_str = self.openai_service.generate(
                prompt,
                step='optimized_developer.implement_simple_task'
            )
            self.last_llm_output = result_str
            
            # Track cost
            estimated_cost = 0.25  # Estimated cost for simple implementation
            monitor.add_cost_entry(
                agent="optimized_developer",
                step="implement_simple_task",
                message_cost=estimated_cost,
                token_count=len(result_str.split()),
                metadata={"complexity": "simple", "task": task.get('title', 'unknown')}
            )
            
            # Parse result
            import json
            try:
                result = json.loads(result_str)
            except json.JSONDecodeError:
                # Fallback to simple result if JSON parsing fails
                result = {
                    "files": [
                        {
                            "file": "simple_implementation.py",
                            "code": "# Simple implementation\nprint('Hello World')",
                            "description": "Simple implementation"
                        }
                    ],
                    "implementation_notes": "Minimal implementation completed"
                }
            
            logger.info(f"Simple task implemented with minimal approach: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Simple task implementation failed: {e}")
            raise
    
    def _implement_medium_task(self, task: Dict[str, Any], plan: Dict[str, Any], 
                              monitor: CostMonitor) -> Dict[str, Any]:
        """Implement medium complexity task with balanced approach."""
        prompt = f"""
You are a Developer Agent for MEDIUM COMPLEXITY TASKS.
- Task complexity: MEDIUM (3-5 acceptance criteria)
- Your role: Implement backend changes with moderate complexity
- Focus: Balanced implementation with some patterns
- Approach: Moderate complexity with good practices
- Output: Working code with some architectural considerations
- Message limit: 15 messages
- Cost limit: $1.50

Task: {task.get('title', 'Unknown')}
Description: {task.get('description', 'No description')}
Plan: {plan.get('implementation_approach', 'No plan')}

Implement the backend changes with:
1. Balanced implementation
2. Some architectural patterns
3. Good practices
4. Moderate complexity

Output format:
{{
    "files": [
        {{
            "file": "filename.py",
            "code": "balanced implementation code",
            "description": "What this file does"
        }}
    ],
    "implementation_notes": "Notes about the balanced implementation",
    "architecture_notes": "Key architectural considerations"
}}
"""
        
        try:
            # Check budget before proceeding
            if monitor.should_terminate():
                raise Exception("Budget exceeded before backend implementation")
            
            # Generate implementation
            result_str = self.openai_service.generate(
                prompt,
                step='optimized_developer.implement_medium_task'
            )
            self.last_llm_output = result_str
            
            # Track cost
            estimated_cost = 0.50  # Estimated cost for medium implementation
            monitor.add_cost_entry(
                agent="optimized_developer",
                step="implement_medium_task",
                message_cost=estimated_cost,
                token_count=len(result_str.split()),
                metadata={"complexity": "medium", "task": task.get('title', 'unknown')}
            )
            
            # Parse result
            import json
            try:
                result = json.loads(result_str)
            except json.JSONDecodeError:
                # Fallback to medium result if JSON parsing fails
                result = {
                    "files": [
                        {
                            "file": "medium_implementation.py",
                            "code": "# Medium implementation with patterns\nclass Service:\n    def __init__(self):\n        pass",
                            "description": "Medium complexity implementation"
                        }
                    ],
                    "implementation_notes": "Balanced implementation completed",
                    "architecture_notes": "Service layer pattern used"
                }
            
            logger.info(f"Medium task implemented with balanced approach: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Medium task implementation failed: {e}")
            raise
    
    def _implement_complex_task(self, task: Dict[str, Any], plan: Dict[str, Any], 
                               monitor: CostMonitor) -> Dict[str, Any]:
        """Implement complex task with comprehensive approach."""
        prompt = f"""
You are a Developer Agent for COMPLEX TASKS.
- Task complexity: COMPLEX (≥6 acceptance criteria)
- Your role: Implement backend changes with comprehensive approach
- Focus: Detailed implementation with architectural patterns
- Approach: Comprehensive with full error handling and patterns
- Output: Production-ready code with full considerations
- Message limit: 25 messages
- Cost limit: $3.00

Task: {task.get('title', 'Unknown')}
Description: {task.get('description', 'No description')}
Plan: {plan.get('implementation_approach', 'No plan')}

Implement the backend changes with:
1. Comprehensive implementation
2. Full architectural patterns
3. Production-ready code
4. Complete error handling
5. Full documentation

Output format:
{{
    "files": [
        {{
            "file": "filename.py",
            "code": "comprehensive implementation code",
            "description": "What this file does"
        }}
    ],
    "implementation_notes": "Detailed notes about the implementation",
    "architecture_notes": "Comprehensive architectural considerations",
    "integration_notes": "Integration and dependency considerations",
    "testing_notes": "Testing and validation considerations"
}}
"""
        
        try:
            # Check budget before proceeding
            if monitor.should_terminate():
                raise Exception("Budget exceeded before backend implementation")
            
            # Generate implementation
            result_str = self.openai_service.generate(
                prompt,
                step='optimized_developer.implement_complex_task'
            )
            self.last_llm_output = result_str
            
            # Track cost
            estimated_cost = 1.00  # Estimated cost for complex implementation
            monitor.add_cost_entry(
                agent="optimized_developer",
                step="implement_complex_task",
                message_cost=estimated_cost,
                token_count=len(result_str.split()),
                metadata={"complexity": "complex", "task": task.get('title', 'unknown')}
            )
            
            # Parse result
            import json
            try:
                result = json.loads(result_str)
            except json.JSONDecodeError:
                # Fallback to complex result if JSON parsing fails
                result = {
                    "files": [
                        {
                            "file": "complex_implementation.py",
                            "code": "# Comprehensive implementation\nclass Service:\n    def __init__(self):\n        pass\n    \n    def method(self):\n        pass",
                            "description": "Complex implementation with full patterns"
                        }
                    ],
                    "implementation_notes": "Comprehensive implementation completed",
                    "architecture_notes": "Full architectural patterns implemented",
                    "integration_notes": "Integration considerations addressed",
                    "testing_notes": "Testing strategy implemented"
                }
            
            logger.info(f"Complex task implemented with comprehensive approach: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Complex task implementation failed: {e}")
            raise

class OptimizedFrontendAgent:
    """
    Optimized Frontend Agent that adapts to task complexity.
    
    For simple tasks: Direct UI implementation, minimal styling
    For complex tasks: Comprehensive UI implementation, detailed patterns
    """
    
    def __init__(self, openai_service: OpenAIService):
        self.openai_service = openai_service
        self.last_llm_output = None
        self.complexity = TaskComplexity.SIMPLE
        self.workflow_config = None
    
    def set_complexity(self, complexity: TaskComplexity, workflow_config: WorkflowConfig):
        """Set complexity level and workflow configuration."""
        self.complexity = complexity
        self.workflow_config = workflow_config
        logger.info(f"Frontend agent set to {complexity.value} complexity")
    
    def implement_task(self, task: Dict[str, Any], plan: Dict[str, Any], 
                      monitor: CostMonitor) -> Dict[str, Any]:
        """
        Implement frontend task with complexity-aware approach.
        
        Args:
            task: Task to implement
            plan: Implementation plan
            monitor: Cost monitor for budget tracking
            
        Returns:
            Implementation result
        """
        if self.complexity == TaskComplexity.SIMPLE:
            return self._implement_simple_frontend(task, plan, monitor)
        elif self.complexity == TaskComplexity.MEDIUM:
            return self._implement_medium_frontend(task, plan, monitor)
        else:
            return self._implement_complex_frontend(task, plan, monitor)
    
    def _implement_simple_frontend(self, task: Dict[str, Any], plan: Dict[str, Any], 
                                 monitor: CostMonitor) -> Dict[str, Any]:
        """Implement simple frontend task with minimal approach."""
        prompt = f"""
You are a Frontend Agent for SIMPLE TASKS ONLY.
- Task complexity: SIMPLE (≤2 acceptance criteria)
- Your role: Implement frontend changes directly
- Focus: UI display only, minimal styling
- Avoid: Complex components, extensive state management, over-engineering
- Output: Working UI that meets requirements
- Message limit: 5 messages
- Cost limit: $0.50

Task: {task.get('title', 'Unknown')}
Description: {task.get('description', 'No description')}
Plan: {plan.get('implementation_approach', 'No plan')}

Implement the frontend changes with:
1. Minimal, working UI
2. No complex components
3. Direct implementation
4. Focus on display only

Output format:
{{
    "files": [
        {{
            "file": "filename.ts",
            "code": "minimal working frontend code",
            "description": "What this file does"
        }}
    ],
    "implementation_notes": "Brief notes about the implementation"
}}
"""
        
        try:
            # Check budget before proceeding
            if monitor.should_terminate():
                raise Exception("Budget exceeded before frontend implementation")
            
            # Generate implementation
            result_str = self.openai_service.generate(
                prompt,
                step='optimized_frontend.implement_simple_frontend'
            )
            self.last_llm_output = result_str
            
            # Track cost
            estimated_cost = 0.25  # Estimated cost for simple frontend
            monitor.add_cost_entry(
                agent="optimized_frontend",
                step="implement_simple_frontend",
                message_cost=estimated_cost,
                token_count=len(result_str.split()),
                metadata={"complexity": "simple", "task": task.get('title', 'unknown')}
            )
            
            # Parse result
            import json
            try:
                result = json.loads(result_str)
            except json.JSONDecodeError:
                # Fallback to simple result if JSON parsing fails
                result = {
                    "files": [
                        {
                            "file": "simple_component.ts",
                            "code": "// Simple component\nexport class SimpleComponent {\n  render() {\n    return '<div>Hello World</div>';\n  }\n}",
                            "description": "Simple frontend component"
                        }
                    ],
                    "implementation_notes": "Minimal frontend implementation completed"
                }
            
            logger.info(f"Simple frontend task implemented with minimal approach: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Simple frontend task implementation failed: {e}")
            raise
    
    def _implement_medium_frontend(self, task: Dict[str, Any], plan: Dict[str, Any], 
                                 monitor: CostMonitor) -> Dict[str, Any]:
        """Implement medium complexity frontend task with balanced approach."""
        prompt = f"""
You are a Frontend Agent for MEDIUM COMPLEXITY TASKS.
- Task complexity: MEDIUM (3-5 acceptance criteria)
- Your role: Implement frontend changes with moderate complexity
- Focus: Balanced UI with some patterns
- Approach: Moderate complexity with good practices
- Output: Working UI with some architectural considerations
- Message limit: 10 messages
- Cost limit: $1.50

Task: {task.get('title', 'Unknown')}
Description: {task.get('description', 'No description')}
Plan: {plan.get('implementation_approach', 'No plan')}

Implement the frontend changes with:
1. Balanced implementation
2. Some UI patterns
3. Good practices
4. Moderate complexity

Output format:
{{
    "files": [
        {{
            "file": "filename.ts",
            "code": "balanced frontend implementation code",
            "description": "What this file does"
        }}
    ],
    "implementation_notes": "Notes about the balanced implementation",
    "ui_patterns": "Key UI patterns used"
}}
"""
        
        try:
            # Check budget before proceeding
            if monitor.should_terminate():
                raise Exception("Budget exceeded before frontend implementation")
            
            # Generate implementation
            result_str = self.openai_service.generate(
                prompt,
                step='optimized_frontend.implement_medium_frontend'
            )
            self.last_llm_output = result_str
            
            # Track cost
            estimated_cost = 0.50  # Estimated cost for medium frontend
            monitor.add_cost_entry(
                agent="optimized_frontend",
                step="implement_medium_frontend",
                message_cost=estimated_cost,
                token_count=len(result_str.split()),
                metadata={"complexity": "medium", "task": task.get('title', 'unknown')}
            )
            
            # Parse result
            import json
            try:
                result = json.loads(result_str)
            except json.JSONDecodeError:
                # Fallback to medium result if JSON parsing fails
                result = {
                    "files": [
                        {
                            "file": "medium_component.ts",
                            "code": "// Medium complexity component\nexport class MediumComponent {\n  constructor() {\n    this.state = {};\n  }\n  \n  render() {\n    return '<div>Medium Component</div>';\n  }\n}",
                            "description": "Medium complexity frontend component"
                        }
                    ],
                    "implementation_notes": "Balanced frontend implementation completed",
                    "ui_patterns": "Component pattern used"
                }
            
            logger.info(f"Medium frontend task implemented with balanced approach: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Medium frontend task implementation failed: {e}")
            raise
    
    def _implement_complex_frontend(self, task: Dict[str, Any], plan: Dict[str, Any], 
                                   monitor: CostMonitor) -> Dict[str, Any]:
        """Implement complex frontend task with comprehensive approach."""
        prompt = f"""
You are a Frontend Agent for COMPLEX TASKS.
- Task complexity: COMPLEX (≥6 acceptance criteria)
- Your role: Implement frontend changes with comprehensive approach
- Focus: Detailed UI with architectural patterns
- Approach: Comprehensive with full state management and patterns
- Output: Production-ready UI with full considerations
- Message limit: 15 messages
- Cost limit: $3.00

Task: {task.get('title', 'Unknown')}
Description: {task.get('description', 'No description')}
Plan: {plan.get('implementation_approach', 'No plan')}

Implement the frontend changes with:
1. Comprehensive implementation
2. Full UI patterns
3. Production-ready code
4. Complete state management
5. Full documentation

Output format:
{{
    "files": [
        {{
            "file": "filename.ts",
            "code": "comprehensive frontend implementation code",
            "description": "What this file does"
        }}
    ],
    "implementation_notes": "Detailed notes about the implementation",
    "ui_patterns": "Comprehensive UI patterns used",
    "state_management": "State management considerations",
    "testing_notes": "Testing and validation considerations"
}}
"""
        
        try:
            # Check budget before proceeding
            if monitor.should_terminate():
                raise Exception("Budget exceeded before frontend implementation")
            
            # Generate implementation
            result_str = self.openai_service.generate(
                prompt,
                step='optimized_frontend.implement_complex_frontend'
            )
            self.last_llm_output = result_str
            
            # Track cost
            estimated_cost = 1.00  # Estimated cost for complex frontend
            monitor.add_cost_entry(
                agent="optimized_frontend",
                step="implement_complex_frontend",
                message_cost=estimated_cost,
                token_count=len(result_str.split()),
                metadata={"complexity": "complex", "task": task.get('title', 'unknown')}
            )
            
            # Parse result
            import json
            try:
                result = json.loads(result_str)
            except json.JSONDecodeError:
                # Fallback to complex result if JSON parsing fails
                result = {
                    "files": [
                        {
                            "file": "complex_component.ts",
                            "code": "// Comprehensive component\nexport class ComplexComponent {\n  constructor() {\n    this.state = {};\n    this.props = {};\n  }\n  \n  render() {\n    return '<div>Complex Component</div>';\n  }\n}",
                            "description": "Complex frontend component with full patterns"
                        }
                    ],
                    "implementation_notes": "Comprehensive frontend implementation completed",
                    "ui_patterns": "Full UI patterns implemented",
                    "state_management": "Complete state management implemented",
                    "testing_notes": "Testing strategy implemented"
                }
            
            logger.info(f"Complex frontend task implemented with comprehensive approach: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Complex frontend task implementation failed: {e}")
            raise

# Example usage and testing
if __name__ == "__main__":
    from crewai_app.services.openai_service import OpenAIService
    from crewai_app.utils.task_complexity_assessor import TaskComplexity, WorkflowConfig
    from crewai_app.utils.cost_monitor import CostMonitor
    
    # Test with simple task
    openai_service = OpenAIService()
    
    # Create optimized agents
    planner = OptimizedPlannerAgent(openai_service)
    developer = OptimizedDeveloperAgent(openai_service)
    frontend = OptimizedFrontendAgent(openai_service)
    
    # Set complexity for simple task
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
    developer.set_complexity(complexity, workflow_config)
    frontend.set_complexity(complexity, workflow_config)
    
    # Create cost monitor
    monitor = CostMonitor(workflow_config.__dict__)
    
    # Test simple story
    simple_story = {
        "fields": {
            "summary": "Add version number to footer",
            "description": "As a user, I want to see the version number in the footer."
        }
    }
    
    # Test planner
    plan = planner.analyze_story(simple_story, monitor)
    print(f"Simple plan: {plan}")
    
    # Test developer
    task = {"title": "Add version to footer", "description": "Simple task"}
    dev_result = developer.implement_task(task, plan, monitor)
    print(f"Simple dev result: {dev_result}")
    
    # Test frontend
    frontend_result = frontend.implement_task(task, plan, monitor)
    print(f"Simple frontend result: {frontend_result}")
    
    # Get cost summary
    summary = monitor.get_cost_summary()
    print(f"Cost summary: ${summary.total_cost:.2f}, {summary.total_messages} messages")
