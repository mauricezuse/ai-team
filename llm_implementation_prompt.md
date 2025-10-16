# LLM Implementation Prompt: AI Agent Workflow Optimization

You are an expert AI systems architect tasked with implementing workflow optimization for an AI agent collaboration system. Based on analysis of workflow 18 (NEGISHI-200), you need to implement improvements to prevent over-engineering of simple tasks.

## Current Problem
- **Task**: Simple footer version number addition (2 acceptance criteria)
- **Actual Performance**: 99 messages, $6.14 cost, 120+ seconds
- **Expected Performance**: 20 messages, $1.00 cost, 30 seconds
- **Efficiency Loss**: 12x over-engineered

## Your Task
Implement a **Task Complexity Assessment System** and **Streamlined Workflow Engine** to optimize AI agent collaborations for simple tasks.

## Implementation Requirements

### 1. Task Complexity Assessment Module
Create a system that:
- Analyzes Jira stories before workflow execution
- Counts acceptance criteria to determine complexity
- Routes simple tasks (≤2 criteria) to streamlined workflow
- Routes complex tasks (≥3 criteria) to full workflow

**Implementation Details:**
```python
class TaskComplexityAssessor:
    def assess_complexity(self, story):
        criteria_count = len(story.acceptance_criteria)
        if criteria_count <= 2:
            return "simple"
        elif criteria_count <= 5:
            return "medium"
        else:
            return "complex"
    
    def get_workflow_config(self, complexity):
        if complexity == "simple":
            return {
                "max_messages": 20,
                "max_cost": 1.00,
                "max_duration": 1800,  # 30 minutes
                "agents": ["planner", "developer", "frontend"],
                "workflow_type": "streamlined"
            }
        else:
            return {
                "max_messages": 100,
                "max_cost": 10.00,
                "max_duration": 3600,  # 60 minutes
                "agents": ["pm", "architect", "developer", "frontend", "tester", "reviewer"],
                "workflow_type": "full"
            }
```

### 2. Streamlined Workflow Engine
Create a 3-step workflow for simple tasks:

**Step 1: Planner Agent (Combined PM + Architect)**
- Analyze story requirements
- Create minimal implementation plan
- Identify 1-2 files to create/modify
- Message limit: 5 messages
- Cost limit: $0.50

**Step 2: Backend Developer**
- Implement backend changes only
- Focus on core functionality
- Message limit: 10 messages
- Cost limit: $0.50

**Step 3: Frontend Developer**
- Implement frontend changes only
- Focus on UI display
- Message limit: 5 messages
- Cost limit: $0.50

### 3. Cost Monitoring System
Implement real-time cost tracking:
```python
class CostMonitor:
    def __init__(self, workflow_config):
        self.max_cost = workflow_config["max_cost"]
        self.current_cost = 0.0
        self.max_messages = workflow_config["max_messages"]
        self.current_messages = 0
    
    def check_budget(self, message_cost):
        self.current_cost += message_cost
        self.current_messages += 1
        
        if self.current_cost > self.max_cost:
            return "budget_exceeded"
        if self.current_messages > self.max_messages:
            return "message_limit_exceeded"
        return "within_budget"
    
    def should_terminate(self):
        return (self.current_cost > self.max_cost or 
                self.current_messages > self.max_messages)
```

### 4. Enhanced Agent Prompts
Update agent prompts to include complexity awareness:

**Planner Agent Prompt:**
```
You are a Planner Agent for SIMPLE TASKS ONLY.
- Task complexity: SIMPLE (≤2 acceptance criteria)
- Your role: Analyze requirements and create minimal implementation plan
- Focus: Identify 1-2 files to create/modify
- Avoid: Over-engineering, complex architectures, extensive planning
- Output: Simple, direct implementation plan
- Message limit: 5 messages
- Cost limit: $0.50
```

**Developer Agent Prompt:**
```
You are a Developer Agent for SIMPLE TASKS ONLY.
- Task complexity: SIMPLE (≤2 acceptance criteria)
- Your role: Implement backend changes directly
- Focus: Core functionality only, minimal code
- Avoid: Complex patterns, extensive error handling, over-engineering
- Output: Working code that meets requirements
- Message limit: 10 messages
- Cost limit: $0.50
```

**Frontend Agent Prompt:**
```
You are a Frontend Agent for SIMPLE TASKS ONLY.
- Task complexity: SIMPLE (≤2 acceptance criteria)
- Your role: Implement frontend changes directly
- Focus: UI display only, minimal styling
- Avoid: Complex components, extensive state management, over-engineering
- Output: Working UI that meets requirements
- Message limit: 5 messages
- Cost limit: $0.50
```

### 5. Workflow Orchestration
Create a workflow orchestrator that:
- Assesses task complexity first
- Routes to appropriate workflow
- Monitors costs and messages in real-time
- Terminates early if limits exceeded
- Provides efficiency feedback

```python
class WorkflowOrchestrator:
    def execute_workflow(self, story):
        # 1. Assess complexity
        complexity = self.assessor.assess_complexity(story)
        config = self.assessor.get_workflow_config(complexity)
        
        # 2. Initialize monitoring
        monitor = CostMonitor(config)
        
        # 3. Execute appropriate workflow
        if config["workflow_type"] == "streamlined":
            return self.execute_streamlined_workflow(story, monitor)
        else:
            return self.execute_full_workflow(story, monitor)
    
    def execute_streamlined_workflow(self, story, monitor):
        # Step 1: Planner
        planner_result = self.planner_agent.analyze(story, monitor)
        if monitor.should_terminate():
            return self.terminate_early("Budget exceeded")
        
        # Step 2: Developer
        developer_result = self.developer_agent.implement(planner_result, monitor)
        if monitor.should_terminate():
            return self.terminate_early("Budget exceeded")
        
        # Step 3: Frontend
        frontend_result = self.frontend_agent.implement(developer_result, monitor)
        
        return {
            "status": "completed",
            "total_cost": monitor.current_cost,
            "total_messages": monitor.current_messages,
            "efficiency": "optimized"
        }
```

## Expected Outcomes

### For NEGISHI-200 (Simple Task)
- **Current**: 99 messages, $6.14 cost, 120+ seconds
- **Target**: 20 messages, $1.00 cost, 30 seconds
- **Improvement**: 75% message reduction, 84% cost reduction

### For Complex Tasks
- **Current**: Appropriate level of detail
- **Target**: Better collaboration and scope validation
- **Improvement**: Maintained quality with enhanced efficiency

## Implementation Checklist

- [ ] Create TaskComplexityAssessor class
- [ ] Implement CostMonitor system
- [ ] Create streamlined workflow engine
- [ ] Update agent prompts with complexity awareness
- [ ] Implement WorkflowOrchestrator
- [ ] Add real-time monitoring and termination
- [ ] Create efficiency reporting
- [ ] Test with NEGISHI-200 equivalent tasks

## Success Metrics
- Simple tasks complete in ≤20 messages
- Simple tasks cost ≤$1.00
- Simple tasks complete in ≤30 minutes
- 75% reduction in over-engineering
- 84% cost reduction for simple tasks

Implement this system to prevent the 12x over-engineering observed in workflow 18 and optimize AI agent collaborations for both simple and complex tasks.
