# LLM Call Tracking Implementation Plan

## Executive Summary
This document outlines two approaches for integrating real-time LLM call tracking into the CrewAI workflow system. After analysis, **Approach 1 (Direct Integration)** is recommended as it's actually simpler and more robust than initially assessed.

---

## Current System Analysis

### How LLM Calls Are Made
1. **OpenAIService** (`crewai_app/services/openai_service.py`):
   - Central service for all LLM API calls
   - `generate()` method handles all OpenAI/Azure OpenAI calls
   - Already logs token usage to `openai_usage.log`
   - Already captures response metadata (tokens, timing)

2. **Workflow Execution** (`crewai_app/workflows/enhanced_story_workflow.py`):
   - `run()` method orchestrates all workflow steps
   - Calls agent methods (PM, Architect, Developer, etc.)
   - Creates `workflow_log` entries for each step
   - Stores results in database via `crewai_app/main.py`

3. **Agent Implementation** (`crewai_app/agents/*.py`):
   - Each agent has methods that call `OpenAIService.generate()`
   - Example: `PMAgent.review_story()` calls `pm_tool._run(prompt)`
   - Agents don't directly know about workflows or conversations

### Current Data Flow
```
Workflow.run() 
  → Agent.method() 
    → OpenAIService.generate(prompt) 
      → Azure OpenAI API 
        → Response
  → workflow_log.append()
    → Database (Conversation + CodeFile)
```

### What's Missing
- **No connection** between OpenAIService calls and database Conversations
- **No capture** of actual LLM request/response data in database
- **No real-time** token usage tracking per conversation
- **Mock data** currently used instead of real LLM call data

---

## Approach 1: Direct Integration (RECOMMENDED)

### Complexity Assessment: **LOW-MEDIUM**

### Overview
Modify the existing `OpenAIService.generate()` method to accept optional `workflow_id` and `conversation_id` parameters, then capture and store LLM call data directly in the database.

### Implementation Steps

#### Step 1: Modify OpenAIService (ALREADY DONE ✓)
**File**: `crewai_app/services/openai_service.py`
**Changes**:
- ✅ Add `workflow_id` and `conversation_id` parameters to `generate()` method
- ✅ Add `_capture_llm_call()` method to store data in database
- ✅ Capture request/response data, tokens, cost, timing

**Estimated Time**: 1 hour (COMPLETED)

#### Step 2: Update Workflow Execution
**File**: `crewai_app/main.py` - `execute_workflow()` function
**Changes**:
```python
# When creating conversations from workflow_log:
for log_entry in enhanced_workflow.workflow_log:
    conversation = Conversation(
        workflow_id=workflow_id,
        step=log_entry.get('step'),
        agent=log_entry.get('agent'),
        # ... other fields
    )
    db.add(conversation)
    db.flush()  # Get conversation.id
    
    # NOW: Pass conversation_id to subsequent LLM calls for this step
    # Store conversation_id in workflow context
```

**Estimated Time**: 2 hours

#### Step 3: Pass Context to Agents
**Files**: `crewai_app/workflows/enhanced_story_workflow.py`
**Changes**:
```python
class EnhancedStoryWorkflow:
    def __init__(self, ..., workflow_id=None):
        self.workflow_id = workflow_id
        self.current_conversation_id = None
        # ...
    
    def _retrieve_and_analyze_story(self):
        # Create conversation first
        conversation = self._create_conversation('story_retrieved_and_analyzed', 'pm')
        self.current_conversation_id = conversation.id
        
        # Pass context to agent
        pm_suggestions = self.pm.review_story(
            story, 
            workflow_id=self.workflow_id,
            conversation_id=self.current_conversation_id
        )
        # ...
```

**Estimated Time**: 3-4 hours

#### Step 4: Update Agent Methods
**Files**: `crewai_app/agents/*.py`
**Changes**:
```python
class PMAgent:
    def review_story(self, story, workflow_id=None, conversation_id=None):
        prompt = f"Analyze story: {story}..."
        # Pass context to OpenAIService
        response = self.openai_service.generate(
            prompt,
            workflow_id=workflow_id,
            conversation_id=conversation_id,
            step='pm.review_story'
        )
        return response
```

**Estimated Time**: 2-3 hours (6 agent files)

#### Step 5: Handle Conversation Creation
**File**: `crewai_app/workflows/enhanced_story_workflow.py`
**Changes**:
```python
def _create_conversation(self, step, agent):
    """Create conversation in database before agent execution"""
    from crewai_app.database import get_db, Conversation
    db = next(get_db())
    
    conversation = Conversation(
        workflow_id=self.workflow_id,
        step=step,
        agent=agent,
        status='running',
        timestamp=datetime.utcnow()
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation
```

**Estimated Time**: 1 hour

### Total Estimated Time: **9-11 hours**

### Pros
✅ **Clean architecture** - LLM tracking integrated at the right layer  
✅ **Real-time capture** - Data stored as calls happen  
✅ **Accurate data** - Captures actual API responses, not estimates  
✅ **Minimal overhead** - Single database write per LLM call  
✅ **Production-ready** - Proper error handling, doesn't break workflow  

### Cons
❌ **Requires workflow changes** - Need to pass context through layers  
❌ **Conversation timing** - Must create conversations before agent execution  
❌ **Database dependency** - OpenAIService now depends on database models  

---

## Approach 2: Post-Processing (SIMPLE BUT LIMITED)

### Complexity Assessment: **LOW**

### Overview
Parse the existing `openai_usage.log` file after workflow completion and backfill LLM call data into the database.

### Implementation Steps

#### Step 1: Create Log Parser
**File**: `crewai_app/services/llm_log_parser.py`
**Changes**:
```python
def parse_openai_usage_log(workflow_id, start_time, end_time):
    """Parse openai_usage.log and extract LLM calls for a workflow"""
    with open('openai_usage.log', 'r') as f:
        for line in f:
            entry = json.loads(line)
            if entry['timestamp'] >= start_time and entry['timestamp'] <= end_time:
                # Extract LLM call data
                # Match to conversation by timestamp and step
                # Store in database
```

**Estimated Time**: 2 hours

#### Step 2: Update Workflow Execution
**File**: `crewai_app/main.py`
**Changes**:
```python
def execute_workflow(workflow_id, db):
    start_time = datetime.utcnow()
    # ... run workflow ...
    end_time = datetime.utcnow()
    
    # Parse and backfill LLM calls
    parse_and_store_llm_calls(workflow_id, start_time, end_time)
```

**Estimated Time**: 1 hour

### Total Estimated Time: **3 hours**

### Pros
✅ **Simple implementation** - No workflow changes needed  
✅ **Quick to implement** - Just parse existing logs  
✅ **Non-invasive** - Doesn't touch agent or workflow code  

### Cons
❌ **Not real-time** - Data only available after workflow completes  
❌ **Matching complexity** - Hard to match log entries to conversations  
❌ **Incomplete data** - May miss some context or details  
❌ **Fragile** - Depends on log format staying consistent  
❌ **No request/response content** - Logs don't capture full prompts/responses  

---

## Recommendation: Approach 1 (Direct Integration)

### Why Approach 1 is Better

1. **Actually Not That Complex**:
   - Most of the work is already done (OpenAIService changes)
   - Remaining work is straightforward parameter passing
   - Well-defined interfaces between components

2. **Production Quality**:
   - Real-time data capture
   - Accurate token counts and costs
   - Full request/response content
   - Proper error handling

3. **Maintainable**:
   - Clean architecture
   - Easy to test
   - No fragile log parsing
   - Clear data flow

4. **Scalable**:
   - Works for any number of workflows
   - No performance issues
   - Can add more metrics easily

### Implementation Priority

**Phase 1 (Critical Path - 4 hours)**:
1. ✅ Modify OpenAIService (DONE)
2. Update `execute_workflow()` to create conversations early
3. Pass `workflow_id` to `EnhancedStoryWorkflow.__init__()`

**Phase 2 (Core Integration - 5 hours)**:
4. Add conversation creation to workflow steps
5. Update agent methods to accept context parameters
6. Test with one agent (PM) first

**Phase 3 (Complete Integration - 2 hours)**:
7. Update remaining agents
8. Add error handling and logging
9. Test end-to-end with real workflow

### Testing Strategy

1. **Unit Tests**:
   - Test `OpenAIService._capture_llm_call()` with mock data
   - Test conversation creation in workflow

2. **Integration Tests**:
   - Run workflow with NEGISHI-165
   - Verify LLM calls are captured in database
   - Check token counts and costs

3. **E2E Tests**:
   - Update Playwright tests to verify LLM call display
   - Test with multiple workflows

---

## Alternative: Hybrid Approach

### If We Want Quick Wins First

**Phase 1**: Implement Approach 2 (3 hours)
- Get something working quickly
- Show LLM call data in UI (even if post-processed)
- Validate the UI/UX

**Phase 2**: Migrate to Approach 1 (9 hours)
- Implement proper real-time tracking
- Replace post-processing with direct capture
- Keep both systems running in parallel during migration

**Total Time**: 12 hours (but delivers value earlier)

---

## Risk Assessment

### Approach 1 Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Database writes slow down LLM calls | Medium | Make writes async, add connection pooling |
| Conversation creation timing issues | High | Create conversations at workflow start, not during execution |
| Agent method signature changes break existing code | Medium | Use optional parameters with defaults |
| Error in LLM tracking breaks workflow | High | Wrap all tracking in try/except, never raise |

### Approach 2 Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Log parsing fails silently | High | Add validation and error logging |
| Can't match logs to conversations | High | Add unique request IDs to logs and conversations |
| Log file grows too large | Medium | Implement log rotation |
| Missing data in logs | High | Accept limitation or switch to Approach 1 |

---

## Decision Matrix

| Criteria | Approach 1 (Direct) | Approach 2 (Post-Process) | Winner |
|----------|---------------------|---------------------------|--------|
| Implementation Time | 9-11 hours | 3 hours | Approach 2 |
| Data Accuracy | Excellent | Good | Approach 1 |
| Real-time Availability | Yes | No | Approach 1 |
| Maintainability | High | Low | Approach 1 |
| Production Readiness | High | Medium | Approach 1 |
| Risk Level | Medium | High | Approach 1 |
| **Total Score** | **5/6** | **1/6** | **Approach 1** |

---

## Conclusion

**Recommendation**: Implement **Approach 1 (Direct Integration)**

**Rationale**:
- The complexity is manageable (9-11 hours of focused work)
- The architecture is clean and maintainable
- The data quality is superior
- The system is production-ready
- The risk is acceptable with proper error handling

**Next Steps**:
1. Review this plan with the team
2. Get approval for 9-11 hour implementation
3. Start with Phase 1 (critical path)
4. Test incrementally after each phase
5. Deploy to production once all phases complete

**Alternative**: If time is critical, implement Hybrid Approach for quick wins, then migrate to full solution.
