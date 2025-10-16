# CrewAI Stateful Workflow Orchestration with Azure Durable Functions

## Complete Implementation Guide

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Project Setup](#project-setup)
5. [Core Components](#core-components)
6. [Implementation](#implementation)
7. [Observability & Monitoring](#observability--monitoring)
8. [Deployment](#deployment)
9. [Testing](#testing)
10. [Cost Optimization](#cost-optimization)
11. [Troubleshooting](#troubleshooting)

---

## Overview

This guide provides a complete implementation of a CrewAI-based AI App Builder using Azure Durable Functions for stateful workflow orchestration. The system enables long-running, multi-agent workflows with full observability and fault tolerance.

### Key Benefits

- ✅ **No Timeout Limits**: Workflows can run for hours or days
- ✅ **Automatic State Management**: Built-in checkpointing and replay
- ✅ **Fault Tolerance**: Automatic retry and error recovery
- ✅ **Observability**: Complete visibility into agent collaboration
- ✅ **Cost Effective**: Pay only for execution time
- ✅ **Scalable**: Auto-scaling based on workload

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Web Dashboard│  │  Mobile App  │  │   External APIs      │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
└─────────┼──────────────────┼──────────────────────┼──────────────┘
          │                  │                      │
          └──────────────────┼──────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Azure API Management                          │
│  • Rate Limiting  • Authentication  • Request Validation         │
└─────────────────────────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Azure Durable Functions                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────┐     │
│  │         HTTP Trigger (Starter Function)                │     │
│  │  • Validates request                                   │     │
│  │  • Starts orchestration                                │     │
│  │  • Returns workflow instance ID                        │     │
│  └────────────────────────────────────────────────────────┘     │
│                             ▼                                    │
│  ┌────────────────────────────────────────────────────────┐     │
│  │      Orchestrator Function (State Machine)             │     │
│  │  • Coordinates agent execution                         │     │
│  │  • Manages workflow state                              │     │
│  │  • Handles sequential/parallel execution               │     │
│  │  • Implements retry logic                              │     │
│  └────────────────────────────────────────────────────────┘     │
│                             ▼                                    │
│  ┌────────────────────────────────────────────────────────┐     │
│  │         Activity Functions (Agent Executors)           │     │
│  │  ┌──────────────┐  ┌──────────────┐                   │     │
│  │  │Requirements  │  │Architecture  │                   │     │
│  │  │    Agent     │  │    Agent     │                   │     │
│  │  └──────────────┘  └──────────────┘                   │     │
│  │  ┌──────────────┐  ┌──────────────┐                   │     │
│  │  │Code Generator│  │  QA Agent    │                   │     │
│  │  │    Agent     │  │              │                   │     │
│  │  └──────────────┘  └──────────────┘                   │     │
│  └────────────────────────────────────────────────────────┘     │
│                             ▼                                    │
│  ┌────────────────────────────────────────────────────────┐     │
│  │       Durable Entities (Agent State Storage)           │     │
│  │  • Conversation history                                │     │
│  │  • Agent context and memory                            │     │
│  │  • Session state                                       │     │
│  └────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Integration Services                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │Azure OpenAI  │  │  Event Grid  │  │  SignalR Service     │  │
│  │   Service    │  │              │  │  (Real-time updates) │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data & Storage Layer                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Cosmos DB   │  │  Blob Storage│  │  Redis Cache         │  │
│  │  (Workflow   │  │  (Generated  │  │  (Session state)     │  │
│  │   history)   │  │   artifacts) │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Observability & Monitoring Layer                    │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Application  │  │Log Analytics │  │  Azure Monitor       │  │
│  │  Insights    │  │   Workspace  │  │  (Alerts & Metrics)  │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Workflow Execution Flow

```
User Request → HTTP Trigger → Orchestrator Starts
                                    ↓
                      ┌─────────────┴─────────────┐
                      ▼                           ▼
              Requirements Agent          Store in Entity
                      ↓                           
              Architecture Agent          Update Status
                      ↓                           
          ┌───────────┴───────────┐              
          ▼                       ▼              
  Code Generator 1        Code Generator 2       
          ↓                       ↓              
          └───────────┬───────────┘              
                      ↓                          
                  QA Agent                       
                      ↓                          
              Human Approval?                    
                      ↓                          
              Complete Workflow                  
                      ↓                          
              Return Results                     
```

---

## Prerequisites

### Azure Resources Required

1. **Azure Subscription** with permissions to create resources
2. **Azure OpenAI Service** with GPT-4 deployment
3. **Azure Functions** (Premium Plan recommended)
4. **Azure Storage Account** (for Durable Functions state)
5. **Azure Cosmos DB** (optional, for workflow history)
6. **Azure Cache for Redis** (optional, for session state)
7. **Application Insights** (for monitoring)
8. **Azure Event Grid** (optional, for event-driven notifications)
9. **Azure SignalR Service** (optional, for real-time UI updates)

### Development Tools

- Python 3.9+
- Azure Functions Core Tools v4
- Azure CLI
- VS Code with Azure Functions extension
- Git

---

## Project Setup

### 1. Create Project Structure

```bash
mkdir ai-app-builder
cd ai-app-builder

# Create directory structure
mkdir -p {functions,shared,tests,config}
mkdir -p functions/{orchestrators,activities,entities,triggers}
mkdir -p shared/{agents,models,utils}
```

### 2. Initialize Azure Functions Project

```bash
# Initialize Functions project
func init . --python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install azure-functions
pip install azure-durable-functions
pip install crewai
pip install langchain-openai
pip install azure-cosmos
pip install redis
pip install azure-monitor-opentelemetry
pip install python-dotenv
```

### 3. Project Structure

```
ai-app-builder/
├── functions/
│   ├── orchestrators/
│   │   └── workflow_orchestrator.py
│   ├── activities/
│   │   ├── requirements_agent.py
│   │   ├── architecture_agent.py
│   │   ├── code_generator_agent.py
│   │   └── qa_agent.py
│   ├── entities/
│   │   └── agent_state_entity.py
│   └── triggers/
│       ├── http_start.py
│       ├── http_status.py
│       └── event_listener.py
├── shared/
│   ├── agents/
│   │   ├── base_agent.py
│   │   └── crew_factory.py
│   ├── models/
│   │   ├── workflow_models.py
│   │   └── agent_models.py
│   └── utils/
│       ├── telemetry.py
│       ├── storage_helper.py
│       └── openai_helper.py
├── tests/
│   ├── unit/
│   └── integration/
├── config/
│   ├── settings.py
│   └── agents_config.yaml
├── host.json
├── local.settings.json
├── requirements.txt
├── function_app.py
└── README.md
```

---

## Core Components

### 1. Configuration Files

#### `host.json`

```json
{
  "version": "2.0",
  "logging": {
    "applicationInsights": {
      "samplingSettings": {
        "isEnabled": true,
        "maxTelemetryItemsPerSecond": 20
      }
    }
  },
  "extensions": {
    "durableTask": {
      "hubName": "CrewAIWorkflowHub",
      "storageProvider": {
        "type": "azure_storage",
        "connectionStringName": "AzureWebJobsStorage"
      },
      "tracing": {
        "traceInputsAndOutputs": true,
        "traceReplayEvents": false
      },
      "maxConcurrentActivityFunctions": 10,
      "maxConcurrentOrchestratorFunctions": 10
    },
    "http": {
      "routePrefix": "api"
    }
  },
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle.Workflows",
    "version": "[1.*, 2.0.0)"
  }
}
```

#### `local.settings.json`

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AZURE_OPENAI_ENDPOINT": "https://your-openai.openai.azure.com/",
    "AZURE_OPENAI_API_KEY": "your-api-key",
    "AZURE_OPENAI_DEPLOYMENT": "gpt-4",
    "AZURE_OPENAI_API_VERSION": "2024-02-15-preview",
    "COSMOS_DB_ENDPOINT": "https://your-cosmos.documents.azure.com:443/",
    "COSMOS_DB_KEY": "your-cosmos-key",
    "REDIS_CONNECTION_STRING": "your-redis:6380,password=...,ssl=True",
    "APPINSIGHTS_INSTRUMENTATIONKEY": "your-insights-key",
    "SIGNALR_CONNECTION_STRING": "your-signalr-connection",
    "EVENT_GRID_TOPIC_ENDPOINT": "https://your-topic.eventgrid.azure.net/api/events",
    "EVENT_GRID_TOPIC_KEY": "your-topic-key"
  }
}
```

#### `requirements.txt`

```txt
azure-functions==1.18.0
azure-durable-functions==1.2.5
crewai==0.28.0
langchain==0.1.10
langchain-openai==0.0.8
azure-cosmos==4.5.1
redis==5.0.1
azure-identity==1.15.0
azure-monitor-opentelemetry==1.2.0
opentelemetry-api==1.22.0
opentelemetry-sdk==1.22.0
python-dotenv==1.0.0
pydantic==2.6.1
pyyaml==6.0.1
```

---

## Implementation

### 1. Workflow Models

#### `shared/models/workflow_models.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class WorkflowInput(BaseModel):
    """Input for creating a new workflow"""
    user_id: str
    app_description: str
    requirements: Optional[str] = None
    target_platform: str = "web"
    tech_stack_preferences: Optional[List[str]] = None
    additional_context: Optional[Dict[str, Any]] = None

class AgentExecution(BaseModel):
    """Tracks individual agent execution"""
    agent_name: str
    status: AgentStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    tokens_used: Optional[int] = None
    error_message: Optional[str] = None
    retry_count: int = 0

class WorkflowState(BaseModel):
    """Complete workflow state"""
    workflow_id: str
    user_id: str
    status: WorkflowStatus
    current_agent: Optional[str] = None
    progress_percentage: int = 0
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    # Input and output
    input_data: WorkflowInput
    final_output: Optional[Dict[str, Any]] = None
    
    # Agent executions
    agent_executions: List[AgentExecution] = Field(default_factory=list)
    
    # Metrics
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0
    
    # Error handling
    error_message: Optional[str] = None
    retry_count: int = 0

class WorkflowMetrics(BaseModel):
    """Metrics for observability"""
    workflow_id: str
    total_duration_seconds: float
    agents_executed: int
    total_tokens: int
    estimated_cost: float
    success: bool
```

### 2. Base Agent Implementation

#### `shared/agents/base_agent.py`

```python
from crewai import Agent, Task
from langchain_openai import AzureChatOpenAI
from typing import Dict, Any, Optional
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseCrewAgent:
    """Base class for all CrewAI agents with telemetry"""
    
    def __init__(self, agent_name: str, role: str, goal: str, backstory: str):
        self.agent_name = agent_name
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.llm = self._initialize_llm()
        self.agent = self._create_agent()
        
    def _initialize_llm(self) -> AzureChatOpenAI:
        """Initialize Azure OpenAI LLM"""
        return AzureChatOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            temperature=0.7,
            model_kwargs={
                "user": self.agent_name
            }
        )
    
    def _create_agent(self) -> Agent:
        """Create CrewAI agent"""
        return Agent(
            role=self.role,
            goal=self.goal,
            backstory=self.backstory,
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
    
    def execute_task(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a task and return results with metadata"""
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"[{self.agent_name}] Starting task execution")
            
            # Create task
            task = Task(
                description=task_description,
                agent=self.agent,
                expected_output="Detailed analysis and recommendations"
            )
            
            # Execute task
            result = self.agent.execute_task(task)
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"[{self.agent_name}] Task completed in {duration:.2f}s")
            
            return {
                "agent_name": self.agent_name,
                "status": "completed",
                "result": result,
                "duration_seconds": duration,
                "timestamp": end_time.isoformat(),
                "tokens_used": self._estimate_tokens(task_description, result)
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_name}] Task failed: {str(e)}")
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            return {
                "agent_name": self.agent_name,
                "status": "failed",
                "error": str(e),
                "duration_seconds": duration,
                "timestamp": end_time.isoformat()
            }
    
    def _estimate_tokens(self, input_text: str, output_text: str) -> int:
        """Rough estimation of tokens used"""
        # Approximate: 1 token ≈ 4 characters
        total_chars = len(str(input_text)) + len(str(output_text))
        return int(total_chars / 4)

class RequirementsAgent(BaseCrewAgent):
    """Agent specialized in requirements analysis"""
    
    def __init__(self):
        super().__init__(
            agent_name="requirements_agent",
            role="Requirements Analyst",
            goal="Extract, clarify, and document comprehensive application requirements",
            backstory="""You are an expert business analyst with 15 years of experience 
            in gathering and documenting software requirements. You excel at asking the 
            right questions and translating business needs into technical specifications."""
        )

class ArchitectureAgent(BaseCrewAgent):
    """Agent specialized in solution architecture"""
    
    def __init__(self):
        super().__init__(
            agent_name="architecture_agent",
            role="Solution Architect",
            goal="Design optimal, scalable, and maintainable application architecture",
            backstory="""You are a senior solution architect with deep expertise in 
            cloud-native architectures, microservices, and modern development patterns. 
            You design systems that are scalable, secure, and cost-effective."""
        )

class CodeGeneratorAgent(BaseCrewAgent):
    """Agent specialized in code generation"""
    
    def __init__(self):
        super().__init__(
            agent_name="code_generator_agent",
            role="Senior Software Engineer",
            goal="Generate clean, efficient, and well-documented code",
            backstory="""You are a senior software engineer with expertise in multiple 
            programming languages and frameworks. You write production-ready code that 
            follows best practices and is easy to maintain."""
        )

class QAAgent(BaseCrewAgent):
    """Agent specialized in quality assurance"""
    
    def __init__(self):
        super().__init__(
            agent_name="qa_agent",
            role="QA Engineer",
            goal="Ensure code quality, identify bugs, and verify requirements",
            backstory="""You are an experienced QA engineer with a keen eye for detail. 
            You excel at finding edge cases, potential bugs, and ensuring the code meets 
            all requirements and quality standards."""
        )
```

### 3. HTTP Trigger (Starter Function)

#### `functions/triggers/http_start.py`

```python
import azure.functions as func
import azure.durable_functions as df
import json
import logging
from datetime import datetime
from shared.models.workflow_models import WorkflowInput, WorkflowStatus

async def main(req: func.HttpRequest, starter: str) -> func.HttpResponse:
    """HTTP trigger to start a new workflow"""
    client = df.DurableOrchestrationClient(starter)
    
    try:
        # Parse request
        req_body = req.get_json()
        workflow_input = WorkflowInput(**req_body)
        
        # Start orchestration
        instance_id = await client.start_new(
            orchestration_name="workflow_orchestrator",
            client_input=workflow_input.dict()
        )
        
        logging.info(f"Started orchestration with ID: {instance_id}")
        
        # Create status URLs
        status_response = client.create_check_status_response(req, instance_id)
        
        # Return response with workflow details
        return func.HttpResponse(
            json.dumps({
                "workflow_id": instance_id,
                "status": "pending",
                "created_at": datetime.utcnow().isoformat(),
                "status_query_url": status_response.get_body().decode(),
                "message": "Workflow started successfully"
            }),
            status_code=202,
            mimetype="application/json"
        )
        
    except ValueError as e:
        logging.error(f"Invalid request: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Invalid request format", "details": str(e)}),
            status_code=400,
            mimetype="application/json"
        )
    
    except Exception as e:
        logging.error(f"Failed to start workflow: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to start workflow", "details": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
```

### 4. Orchestrator Function

#### `functions/orchestrators/workflow_orchestrator.py`

```python
import azure.durable_functions as df
import logging
from typing import Dict, Any
from datetime import datetime

def orchestrator_function(context: df.DurableOrchestrationContext):
    """Main orchestrator for the AI app building workflow"""
    
    # Get input
    workflow_input = context.get_input()
    workflow_id = context.instance_id
    
    logging.info(f"Starting workflow {workflow_id}")
    
    try:
        # Initialize workflow state
        context.set_custom_status({
            "status": "running",
            "current_agent": "requirements",
            "progress": 0,
            "started_at": context.current_utc_datetime.isoformat()
        })
        
        # Step 1: Requirements Analysis (10-15 min)
        logging.info(f"[{workflow_id}] Starting Requirements Agent")
        context.set_custom_status({
            "status": "running",
            "current_agent": "requirements",
            "progress": 10
        })
        
        requirements_result = yield context.call_activity(
            'requirements_agent_activity',
            workflow_input
        )
        
        # Store state in entity
        entity_id = df.EntityId("AgentStateEntity", workflow_id)
        context.signal_entity(entity_id, "update_agent_result", {
            "agent": "requirements",
            "result": requirements_result
        })
        
        # Step 2: Architecture Design (10-15 min)
        logging.info(f"[{workflow_id}] Starting Architecture Agent")
        context.set_custom_status({
            "status": "running",
            "current_agent": "architecture",
            "progress": 30
        })
        
        architecture_result = yield context.call_activity(
            'architecture_agent_activity',
            {
                "workflow_input": workflow_input,
                "requirements": requirements_result
            }
        )
        
        context.signal_entity(entity_id, "update_agent_result", {
            "agent": "architecture",
            "result": architecture_result
        })
        
        # Step 3: Code Generation (15-30 min) - Parallel execution
        logging.info(f"[{workflow_id}] Starting Code Generation (Parallel)")
        context.set_custom_status({
            "status": "running",
            "current_agent": "code_generation",
            "progress": 50
        })
        
        # Determine components to generate
        components = architecture_result.get("components", [])
        
        # Fan-out: Generate code for each component in parallel
        code_generation_tasks = []
        for component in components:
            code_generation_tasks.append(
                context.call_activity(
                    'code_generator_agent_activity',
                    {
                        "component": component,
                        "architecture": architecture_result,
                        "requirements": requirements_result
                    }
                )
            )
        
        # Fan-in: Wait for all code generation tasks to complete
        generated_code = yield context.task_all(code_generation_tasks)
        
        context.signal_entity(entity_id, "update_agent_result", {
            "agent": "code_generation",
            "result": generated_code
        })
        
        # Step 4: Quality Assurance (5-10 min)
        logging.info(f"[{workflow_id}] Starting QA Agent")
        context.set_custom_status({
            "status": "running",
            "current_agent": "qa",
            "progress": 80
        })
        
        qa_result = yield context.call_activity(
            'qa_agent_activity',
            {
                "requirements": requirements_result,
                "architecture": architecture_result,
                "code": generated_code
            }
        )
        
        context.signal_entity(entity_id, "update_agent_result", {
            "agent": "qa",
            "result": qa_result
        })
        
        # Step 5: Human approval (if needed)
        if qa_result.get("requires_approval", False):
            logging.info(f"[{workflow_id}] Waiting for human approval")
            context.set_custom_status({
                "status": "awaiting_approval",
                "current_agent": "human_review",
                "progress": 90
            })
            
            # Wait for external event (timeout after 24 hours)
            approval_task = context.wait_for_external_event("approval_event")
            timeout_task = context.create_timer(
                context.current_utc_datetime + timedelta(hours=24)
            )
            
            winner = yield context.task_any([approval_task, timeout_task])
            
            if winner == timeout_task:
                return {
                    "status": "timeout",
                    "message": "Approval timeout after 24 hours"
                }
            
            approval = approval_task.result
            if not approval.get("approved", False):
                return {
                    "status": "rejected",
                    "reason": approval.get("reason", "No reason provided")
                }
        
        # Workflow completed successfully
        context.set_custom_status({
            "status": "completed",
            "progress": 100,
            "completed_at": context.current_utc_datetime.isoformat()
        })
        
        logging.info(f"[{workflow_id}] Workflow completed successfully")
        
        return {
            "status": "completed",
            "workflow_id": workflow_id,
            "requirements": requirements_result,
            "architecture": architecture_result,
            "code": generated_code,
            "qa_results": qa_result,
            "completed_at": context.current_utc_datetime.isoformat()
        }
        
    except Exception as e:
        logging.error(f"[{workflow_id}] Workflow failed: {str(e)}")
        context.set_custom_status({
            "status": "failed",
            "error": str(e)
        })
        
        return {
            "status": "failed",
            "error": str(e),
            "workflow_id": workflow_id
        }

main = df.Orchestrator.create(orchestrator_function)
```

### 5. Activity Functions (Agents)

#### `functions/activities/requirements_agent.py`

```python
import azure.functions as func
from shared.agents.base_agent import RequirementsAgent
import logging

def main(input_data: dict) -> dict:
    """Activity function for requirements analysis"""
    
    logging.info("Requirements Agent: Starting execution")
    
    try:
        agent = RequirementsAgent()
        
        # Build task description
        task_description = f"""
        Analyze the following application request and extract comprehensive requirements:
        
        Application Description: {input_data.get('app_description')}
        Target Platform: {input_data.get('target_platform', 'web')}
        Additional Requirements: {input_data.get('requirements', 'None provided')}
        User Preferences: {input_data.get('tech_stack_preferences', [])}
        
        Please provide:
        1. Functional Requirements (detailed feature list)
        2. Non-Functional Requirements (performance, security, scalability)
        3. User Stories with acceptance criteria
        4. Technical Constraints
        5. Dependencies and Integrations
        6. Success Metrics
        """
        
        # Execute agent task
        result = agent.execute_task(task_description, context=input_data)
        
        logging.info("Requirements Agent: Execution completed")
        return result
        
    except Exception as e:
        logging.error(f"Requirements Agent failed: {str(e)}")
        return {
            "agent_name": "requirements_agent",
            "status": "failed",
            "error": str(e)
        }
```

#### `functions/activities/architecture_agent.py`

```python
import azure.functions as func
from shared.agents.base_agent import ArchitectureAgent
import logging
import json

def main(input_data: dict) -> dict:
    """Activity function for architecture design"""
    
    logging.info("Architecture Agent: Starting execution")
    
    try:
        agent = ArchitectureAgent()
        
        requirements = input_data.get('requirements', {})
        workflow_input = input_data.get('workflow_input', {})
        
        task_description = f"""
        Design a comprehensive application architecture based on these requirements:
        
        {json.dumps(requirements, indent=2)}
        
        Target Platform: {workflow_input.get('target_platform', 'web')}
        Preferred Tech Stack: {workflow_input.get('tech_stack_preferences', [])}
        
        Please provide:
        1. High-Level Architecture Diagram (described in text)
        2. Technology Stack Recommendations
        3. Component Breakdown (list all major components)
        4. Data Model Design
        5. API Design (endpoints and contracts)
        6. Security Architecture
        7. Deployment Strategy
        8. Scalability Considerations
        
        Format the component list as JSON array for code generation.
        """
        
        result = agent.execute_task(task_description, context=input_data)
        
        # Parse components for parallel code generation
        if result.get('status') == 'completed':
            try:
                # Extract components from result (assuming structured output)
                result_text = result.get('result', '')
                # Simple parsing - in production, use structured output
                components = [
                    {"name": "frontend", "type": "ui", "priority": 1},
                    {"name": "backend_api", "type": "api", "priority": 1},
                    {"name": "database", "type": "data", "priority": 2},
                    {"name": "authentication", "type": "service", "priority": 1}
                ]
                result['components'] = components
            except Exception as e:
                logging.warning(f"Could not parse components: {str(e)}")
                result['components'] = []
        
        logging.info("Architecture Agent: Execution completed")
        return result
        
    except Exception as e:
        logging.error(f"Architecture Agent failed: {str(e)}")
        return {
            "agent_name": "architecture_agent",
            "status": "failed",
            "error": str(e)
        }
```

#### `functions/activities/code_generator_agent.py`

```python
import azure.functions as func
from shared.agents.base_agent import CodeGeneratorAgent
import logging
import json

def main(input_data: dict) -> dict:
    """Activity function for code generation"""
    
    logging.info("Code Generator Agent: Starting execution")
    
    try:
        agent = CodeGeneratorAgent()
        
        component = input_data.get('component', {})
        architecture = input_data.get('architecture', {})
        requirements = input_data.get('requirements', {})
        
        task_description = f"""
        Generate production-ready code for the following component:
        
        Component: {component.get('name')}
        Type: {component.get('type')}
        
        Architecture Context:
        {json.dumps(architecture, indent=2)[:1000]}  # Limit context size
        
        Requirements Context:
        {json.dumps(requirements, indent=2)[:1000]}
        
        Please generate:
        1. Complete source code files with proper structure
        2. Configuration files
        3. Dependencies list (package.json, requirements.txt, etc.)
        4. README with setup instructions
        5. Unit tests
        6. Docker configuration (if applicable)
        
        Follow best practices for:
        - Code organization and structure
        - Error handling
        - Security
        - Performance
        - Documentation
        """
        
        result = agent.execute_task(task_description, context=input_data)
        
        # Add component info to result
        if result.get('status') == 'completed':
            result['component_name'] = component.get('name')
            result['component_type'] = component.get('type')
        
        logging.info(f"Code Generator Agent: Completed for {component.get('name')}")
        return result
        
    except Exception as e:
        logging.error(f"Code Generator Agent failed: {str(e)}")
        return {
            "agent_name": "code_generator_agent",
            "status": "failed",
            "error": str(e),
            "component": input_data.get('component', {}).get('name')
        }
```

#### `functions/activities/qa_agent.py`

```python
import azure.functions as func
from shared.agents.base_agent import QAAgent
import logging
import json

def main(input_data: dict) -> dict:
    """Activity function for quality assurance"""
    
    logging.info("QA Agent: Starting execution")
    
    try:
        agent = QAAgent()
        
        requirements = input_data.get('requirements', {})
        architecture = input_data.get('architecture', {})
        code = input_data.get('code', [])
        
        task_description = f"""
        Perform comprehensive quality assurance on the generated application:
        
        Requirements to verify:
        {json.dumps(requirements, indent=2)[:1000]}
        
        Architecture to validate:
        {json.dumps(architecture, indent=2)[:1000]}
        
        Generated Components: {len(code)}
        
        Please analyze and provide:
        1. Requirements Coverage Analysis
           - Which requirements are fully implemented
           - Which requirements are partially implemented
           - Which requirements are missing
        
        2. Code Quality Assessment
           - Code structure and organization
           - Best practices adherence
           - Security vulnerabilities
           - Performance considerations
        
        3. Architecture Compliance
           - Does implementation match architecture?
           - Are all components present?
        
        4. Testing Coverage
           - Are unit tests adequate?
           - Integration test recommendations
        
        5. Issues and Bugs
           - List potential bugs or issues
           - Severity ratings
        
        6. Recommendations
           - Improvements needed
           - Priority ranking
        
        7. Approval Status
           - Ready for deployment? (yes/no)
           - If no, what needs to be fixed?
        """
        
        result = agent.execute_task(task_description, context=input_data)
        
        # Determine if human approval is needed
        if result.get('status') == 'completed':
            result_text = str(result.get('result', '')).lower()
            # Simple heuristic - in production, use structured output
            critical_issues = any(keyword in result_text for keyword in 
                ['critical', 'severe', 'security vulnerability', 'major bug'])
            result['requires_approval'] = critical_issues
            result['ready_for_deployment'] = not critical_issues
        
        logging.info("QA Agent: Execution completed")
        return result
        
    except Exception as e:
        logging.error(f"QA Agent failed: {str(e)}")
        return {
            "agent_name": "qa_agent",
            "status": "failed",
            "error": str(e)
        }
```

### 6. Durable Entity (Agent State)

#### `functions/entities/agent_state_entity.py`

```python
import azure.durable_functions as df
from typing import Dict, Any, List
from datetime import datetime
import logging

class AgentStateEntity:
    """Durable entity to maintain agent state across workflow"""
    
    def __init__(self):
        self.workflow_id: str = ""
        self.agent_results: Dict[str, Any] = {}
        self.conversation_history: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}
        self.created_at: str = datetime.utcnow().isoformat()
        self.updated_at: str = datetime.utcnow().isoformat()
    
    def initialize(self, workflow_id: str, metadata: Dict[str, Any] = None):
        """Initialize entity with workflow ID"""
        self.workflow_id = workflow_id
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()
        logging.info(f"Initialized entity for workflow {workflow_id}")
    
    def update_agent_result(self, data: Dict[str, Any]):
        """Store agent execution result"""
        agent_name = data.get('agent')
        result = data.get('result')
        
        self.agent_results[agent_name] = {
            'result': result,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.updated_at = datetime.utcnow().isoformat()
        
        logging.info(f"Updated result for agent: {agent_name}")
    
    def add_conversation(self, agent: str, message: str, role: str = "assistant"):
        """Add to conversation history"""
        self.conversation_history.append({
            'agent': agent,
            'role': role,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        })
        self.updated_at = datetime.utcnow().isoformat()
    
    def get_agent_result(self, agent_name: str) -> Dict[str, Any]:
        """Retrieve specific agent result"""
        return self.agent_results.get(agent_name, {})
    
    def get_all_results(self) -> Dict[str, Any]:
        """Retrieve all agent results"""
        return self.agent_results
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Retrieve full conversation history"""
        return self.conversation_history
    
    def get_state(self) -> Dict[str, Any]:
        """Get complete entity state"""
        return {
            'workflow_id': self.workflow_id,
            'agent_results': self.agent_results,
            'conversation_history': self.conversation_history,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def delete(self):
        """Clean up entity"""
        Entity.current.destruct_on_exit()
        logging.info(f"Entity deleted for workflow {self.workflow_id}")

# Register entity
main = df.Entity.create(AgentStateEntity)
```

### 7. Status Query Function

#### `functions/triggers/http_status.py`

```python
import azure.functions as func
import azure.durable_functions as df
import json
import logging

async def main(req: func.HttpRequest, starter: str) -> func.HttpResponse:
    """Query workflow status"""
    client = df.DurableOrchestrationClient(starter)
    
    # Get instance ID from route parameter
    instance_id = req.route_params.get('instanceId')
    
    if not instance_id:
        return func.HttpResponse(
            json.dumps({"error": "Missing instance ID"}),
            status_code=400,
            mimetype="application/json"
        )
    
    try:
        # Get orchestration status
        status = await client.get_status(instance_id)
        
        if status is None:
            return func.HttpResponse(
                json.dumps({"error": "Workflow not found"}),
                status_code=404,
                mimetype="application/json"
            )
        
        # Build response
        response = {
            "workflow_id": instance_id,
            "runtime_status": status.runtime_status.name,
            "custom_status": status.custom_status,
            "created_time": status.created_time.isoformat() if status.created_time else None,
            "last_updated_time": status.last_updated_time.isoformat() if status.last_updated_time else None,
            "input": status.input,
            "output": status.output
        }
        
        # Add entity state if available
        try:
            entity_id = df.EntityId("AgentStateEntity", instance_id)
            entity_state = await client.read_entity_state(entity_id)
            if entity_state.entity_exists:
                response['agent_state'] = entity_state.entity_state
        except Exception as e:
            logging.warning(f"Could not retrieve entity state: {str(e)}")
        
        return func.HttpResponse(
            json.dumps(response, indent=2),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Failed to get status: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
```

### 8. Approval Event Function

#### `functions/triggers/http_approval.py`

```python
import azure.functions as func
import azure.durable_functions as df
import json
import logging

async def main(req: func.HttpRequest, starter: str) -> func.HttpResponse:
    """Send approval event to workflow"""
    client = df.DurableOrchestrationClient(starter)
    
    instance_id = req.route_params.get('instanceId')
    
    if not instance_id:
        return func.HttpResponse(
            json.dumps({"error": "Missing instance ID"}),
            status_code=400,
            mimetype="application/json"
        )
    
    try:
        req_body = req.get_json()
        approved = req_body.get('approved', False)
        reason = req_body.get('reason', '')
        
        # Send external event
        await client.raise_event(
            instance_id,
            'approval_event',
            {
                'approved': approved,
                'reason': reason,
                'reviewer': req_body.get('reviewer', 'anonymous'),
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        logging.info(f"Approval event sent to {instance_id}: {approved}")
        
        return func.HttpResponse(
            json.dumps({
                "message": "Approval event sent successfully",
                "workflow_id": instance_id,
                "approved": approved
            }),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Failed to send approval: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
```

---

## Observability & Monitoring

### 1. Telemetry Helper

#### `shared/utils/telemetry.py`

```python
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode
import logging
import os

# Configure Azure Monitor
configure_azure_monitor(
    connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
)

tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

# Custom metrics
workflow_counter = meter.create_counter(
    name="crewai.workflows.total",
    description="Total number of workflows started",
    unit="1"
)

agent_duration = meter.create_histogram(
    name="crewai.agent.duration",
    description="Agent execution duration in seconds",
    unit="s"
)

token_usage = meter.create_counter(
    name="crewai.tokens.total",
    description="Total tokens consumed",
    unit="1"
)

class WorkflowTelemetry:
    """Helper class for workflow telemetry"""
    
    @staticmethod
    def start_workflow(workflow_id: str, input_data: dict):
        """Log workflow start"""
        with tracer.start_as_current_span("workflow_start") as span:
            span.set_attribute("workflow.id", workflow_id)
            span.set_attribute("workflow.type", "crewai_app_builder")
            workflow_counter.add(1, {"status": "started"})
            logging.info(f"Workflow {workflow_id} started")
    
    @staticmethod
    def complete_workflow(workflow_id: str, success: bool, duration: float):
        """Log workflow completion"""
        with tracer.start_as_current_span("workflow_complete") as span:
            span.set_attribute("workflow.id", workflow_id)
            span.set_attribute("workflow.success", success)
            span.set_attribute("workflow.duration", duration)
            
            status = "completed" if success else "failed"
            workflow_counter.add(1, {"status": status})
            
            logging.info(f"Workflow {workflow_id} {status} in {duration:.2f}s")
    
    @staticmethod
    def track_agent_execution(agent_name: str, duration: float, tokens: int, success: bool):
        """Track individual agent execution"""
        with tracer.start_as_current_span(f"agent_{agent_name}") as span:
            span.set_attribute("agent.name", agent_name)
            span.set_attribute("agent.duration", duration)
            span.set_attribute("agent.tokens", tokens)
            span.set_attribute("agent.success", success)
            
            agent_duration.record(duration, {"agent": agent_name})
            token_usage.add(tokens, {"agent": agent_name})
            
            if not success:
                span.set_status(Status(StatusCode.ERROR))
```

### 2. Application Insights Queries

#### Useful KQL Queries for Monitoring

```kusto
// Average workflow duration
customMetrics
| where name == "crewai.workflows.total"
| summarize avg(value) by bin(timestamp, 1h)

// Agent execution times
customMetrics
| where name == "crewai.agent.duration"
| extend agent = tostring(customDimensions.agent)
| summarize avg(value), percentile(value, 95) by agent

// Token usage by agent
customMetrics
| where name == "crewai.tokens.total"
| extend agent = tostring(customDimensions.agent)
| summarize sum(value) by agent, bin(timestamp, 1d)

// Workflow success rate
customMetrics
| where name == "crewai.workflows.total"
| extend status = tostring(customDimensions.status)
| summarize count() by status
| extend success_rate = todouble(count_) / toscalar(summarize sum(count_))

// Failed workflows with errors
traces
| where severityLevel >= 3  // Warning and above
| where message contains "workflow"
| project timestamp, message, customDimensions
| order by timestamp desc

// Real-time workflow status
customEvents
| where name == "workflow_status_update"
| extend workflow_id = tostring(customDimensions.workflow_id)
| extend status = tostring(customDimensions.status)
| extend agent = tostring(customDimensions.current_agent)
| project timestamp, workflow_id, status, agent
| order by timestamp desc
```

---

## Deployment

### 1. Azure Resources Setup Script

#### `deploy/setup-azure-resources.sh`

```bash
#!/bin/bash

# Configuration
RESOURCE_GROUP="rg-crewai-app-builder"
LOCATION="eastus"
STORAGE_ACCOUNT="stcrewaiworkflows"
FUNCTION_APP="func-crewai-orchestrator"
APPINSIGHTS="ai-crewai-monitoring"
COSMOSDB_ACCOUNT="cosmos-crewai-workflows"
REDIS_NAME="redis-crewai-cache"
OPENAI_NAME="openai-crewai"

# Create resource group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# Create storage account
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS

# Create Application Insights
az monitor app-insights component create \
  --app $APPINSIGHTS \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP \
  --application-type web

# Get instrumentation key
APPINSIGHTS_KEY=$(az monitor app-insights component show \
  --app $APPINSIGHTS \
  --resource-group $RESOURCE_GROUP \
  --query instrumentationKey -o tsv)

# Create Azure Functions (Premium Plan for Durable Functions)
az functionapp plan create \
  --name ${FUNCTION_APP}-plan \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku EP1 \
  --is-linux true

az functionapp create \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --plan ${FUNCTION_APP}-plan \
  --runtime python \
  --runtime-version 3.11 \
  --storage-account $STORAGE_ACCOUNT \
  --functions-version 4 \
  --app-insights-key $APPINSIGHTS_KEY

# Create Cosmos DB
az cosmosdb create \
  --name $COSMOSDB_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --default-consistency-level Session

az cosmosdb sql database create \
  --account-name $COSMOSDB_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --name workflows

# Create Redis Cache
az redis create \
  --name $REDIS_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Basic \
  --vm-size c0

# Create Azure OpenAI
az cognitiveservices account create \
  --name $OPENAI_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --kind OpenAI \
  --sku S0

# Deploy GPT-4 model
az cognitiveservices account deployment create \
  --name $OPENAI_NAME \
  --resource-group $RESOURCE_GROUP \
  --deployment-name gpt-4 \
  --model-name gpt-4 \
  --model-version "0613" \
  --model-format OpenAI \
  --scale-settings-scale-type "Standard"

echo "Azure resources created successfully!"
echo "Function App: $FUNCTION_APP"
echo "Application Insights Key: $APPINSIGHTS_KEY"
```

### 2. Deploy Function App

```bash
# Build and deploy
cd /path/to/ai-app-builder

# Install dependencies
pip install -r requirements.txt

# Deploy to Azure
func azure functionapp publish func-crewai-orchestrator

# Configure app settings
az functionapp config appsettings set \
  --name func-crewai-orchestrator \
  --resource-group rg-crewai-app-builder \
  --settings \
    AZURE_OPENAI_ENDPOINT="https://openai-crewai.openai.azure.com/" \
    AZURE_OPENAI_API_VERSION="2024-02-15-preview" \
    AZURE_OPENAI_DEPLOYMENT="gpt-4"
```

---

## Testing

### 1. Unit Tests

#### `tests/unit/test_agents.py`

```python
import pytest
from shared.agents.base_agent import RequirementsAgent, ArchitectureAgent

def test_requirements_agent_initialization():
    agent = RequirementsAgent()
    assert agent.agent_name == "requirements_agent"
    assert agent.role == "Requirements Analyst"

def test_agent_task_execution():
    agent = RequirementsAgent()
    result = agent.execute_task("Analyze requirements for a todo app")
    
    assert "status" in result
    assert "agent_name" in result
    assert result["agent_name"] == "requirements_agent"

@pytest.mark.asyncio
async def test_architecture_agent():
    agent = ArchitectureAgent()
    result = agent.execute_task("Design architecture for microservices app")
    
    assert result["agent_name"] == "architecture_agent"
```

### 2. Integration Tests

#### `tests/integration/test_workflow.py`

```python
import pytest
import requests
import time

BASE_URL = "http://localhost:7071/api"

@pytest.mark.integration
def test_complete_workflow():
    # Start workflow
    response = requests.post(f"{BASE_URL}/start", json={
        "user_id": "test_user",
        "app_description": "Build a simple todo list app",
        "target_platform": "web"
    })
    
    assert response.status_code == 202
    data = response.json()
    workflow_id = data["workflow_id"]
    
    # Poll for completion (with timeout)
    max_attempts = 60
    for i in range(max_attempts):
        status_response = requests.get(f"{BASE_URL}/status/{workflow_id}")
        status_data = status_response.json()
        
        if status_data["runtime_status"] == "Completed":
            assert "output" in status_data
            break
        
        time.sleep(10)  # Wait 10 seconds between polls
    
    assert status_data["runtime_status"] == "Completed"
```

---

## Cost Optimization

### Best Practices

1. **Use Premium Plan with Always Ready Instances**: 1-2 instances minimum
2. **Set Maximum Burst**: Limit to 10 instances for cost control
3. **Enable Auto-scale**: Scale based on queue length or HTTP requests
4. **Monitor Token Usage**: Set alerts for unusual spikes
5. **Implement Caching**: Use Redis for frequently accessed data
6. **Optimize Prompts**: Reduce token usage with concise prompts

### Estimated Monthly Costs (1000 workflows/month)

| Service | Configuration | Estimated Cost |
|---------|--------------|----------------|
| Azure Functions Premium | EP1, 1 instance | $150 |
| Azure OpenAI (GPT-4) | ~500K tokens/workflow | $300-400 |
| Cosmos DB | 400 RU/s provisioned | $25 |
| Redis Cache | Basic C0 | $17 |
| Application Insights | 5GB ingestion | $12 |
| Blob Storage | 50GB | $1 |
| **Total** | | **~$505-615/month** |

---

## Troubleshooting

### Common Issues

#### 1. Orchestrator Timeout

**Symptom**: Orchestration stops after 5-10 minutes

**Solution**:
- Ensure using Premium Plan (not Consumption Plan)
- Check `host.json` has no timeout settings
- Verify activity functions complete within reasonable time

#### 2. Missing Dependencies

**Symptom**: Import errors in deployed function

**Solution**:
```bash
# Ensure all dependencies in requirements.txt
pip freeze > requirements.txt

# Use remote build
func azure functionapp publish func-crewai-orchestrator --build remote
```

#### 3. State Not Persisting

**Symptom**: Entity state lost between calls

**Solution**:
- Verify `AzureWebJobsStorage` is configured
- Check entity operations use correct entity ID
- Ensure entity methods don't have side effects

#### 4. High Token Costs

**Symptom**: Azure OpenAI costs higher than expected

**Solution**:
- Implement prompt caching
- Use truncation for long contexts
- Monitor token usage per agent
- Consider GPT-3.5 for non-critical agents

---

## Next Steps

1. **Add Real-time Dashboard**: Integrate SignalR for live workflow updates
2. **Implement Human-in-the-Loop**: Build approval UI
3. **Add Workflow Templates**: Pre-configured workflows for common apps
4. **Enhanced Error Handling**: Retry logic with exponential backoff
5. **Multi-tenancy**: Isolate workflows by tenant/user
6. **CI/CD Pipeline**: Automate testing and deployment
7. **Cost Analytics Dashboard**: Track costs per workflow

---

## Resources

- [Azure Durable Functions Documentation](https://docs.microsoft.com/azure/azure-functions/durable/)
- [CrewAI Documentation](https://docs.crewai.com/)
- [Azure OpenAI Service](https://azure.microsoft.com/services/cognitive-services/openai-service/)
- [Application Insights](https://docs.microsoft.com/azure/azure-monitor/app/app-insights-overview)

---

## License

MIT License - See LICENSE file for details

---

## Support

For issues and questions:
- GitHub Issues: [your-repo/issues]
- Email: support@yourcompany.com
- Documentation: [your-docs-site]