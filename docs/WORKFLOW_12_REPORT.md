## Workflow 12 (NEGISHI-165) - Comprehensive Report

### Summary
- Workflow ID: 12
- Jira: NEGISHI-165
- Name: Freelancer can view and accept job offers, with link to the communication system
- Current Status: failed (terminal)
- Error: Heartbeat timeout after 300 seconds
- Started At: 2025-10-09 23:50:18.860544
- Finished At: 2025-10-09 23:55:51.554861
- Last Heartbeat: 2025-10-09 23:50:18.863454
- Repository: https://github.com/mauricezuse/negishi-freelancing
- Target Branch: main

### Database Snapshot

Core record from `workflows`:

```csv
id,name,jira_story_id,jira_story_title,jira_story_description,status,created_at,updated_at,repository_url,target_branch,started_at,finished_at,error,last_heartbeat_at
12,"NEGISHI-165: Freelancer can view and accept job offers, with link to the communication system",NEGISHI-165,"Freelancer can view and accept job offers, with link to the communication system","As a freelancer,
I want to view job offers and accept or reject them,
so that I can start working on projects,
and communicate with clients if I have questions or want to negotiate. Implementation Details: Backend: Use the existing JobOffer model. Endpoints: GET /job_offers/ — List job offers for the current freelancer. GET /job_offers/{job_offer_id} — Get details of a specific job offer. PUT /job_offers/{job_offer_id} — Update the status to accepted or rejected. No changes needed unless a dedicated "accept" endpoint is desired. Frontend: Add a list/table of job offers in the freelancer dashboard. Show offer details (amount, timeline, message). Add “Accept” and “Reject” buttons. On click, call the PUT endpoint to update the status. Add a “Message Client” button that opens the chat/communication system (use a router link or integration API). Show success/error messages after actions. Testing: Add/extend unit and integration tests for: Listing job offers. Accepting/rejecting an offer (status update). UI feedback and error handling.",failed,"2025-10-09 22:58:26.483887","2025-10-09 23:55:51.554872",https://github.com/mauricezuse/negishi-freelancing,main,"2025-10-09 23:50:18.860544","2025-10-09 23:55:51.554861","Heartbeat timeout after 300 seconds","2025-10-09 23:50:18.863454"
```

Related `executions`:

```text
None found for workflow_id=12
```

Related `conversations` (subset of fields):

```csv
id,workflow_id,agent,step,status,timestamp
76,12,pm,story_retrieved_and_analyzed,running,"2025-10-09 23:00:14.365542"
77,12,architect,file_selection,running,"2025-10-09 23:00:17.892232"
78,12,architect,user_acceptance_plan,running,"2025-10-09 23:00:32.704202"
79,12,architect,dev_plan,running,"2025-10-09 23:00:37.057295"
```

Related `code_files`:

```text
None found for workflow_id=12
```

### Logs

Backend access and WS activity (excerpt from `backend.log`):

```text
... "GET /workflows/12 HTTP/1.1" 200 OK  
... "GET /workflows/12/executions HTTP/1.1" 200 OK  
... "WebSocket /ws/workflows/12" [accepted]
```

Project log references to NEGISHI-165 (from `logs/ai_team.log`):

```text
2025-10-04 ... INFO ai_team [Stub] Would fetch Jira story: NEGISHI-165
```

Service-side heartbeat/audit (from runtime stdout):

```text
[WorkflowStatusService] Marking stale workflow 12 as failed
[WorkflowStatusService] Finalized workflow 12 with status: failed
```

### Timeline
- 2025-10-09 22:58:26: Workflow created
- 2025-10-09 23:00:14–23:00:37: Early conversations logged (PM/Architect)
- 2025-10-09 23:50:18: Workflow started; last heartbeat recorded around start
- 2025-10-09 23:55:51: Marked failed by audit due to heartbeat timeout (300s)

### Current State (API)

Key fields returned by `/workflows/12`:

```json
{
  "status": "failed",
  "isTerminal": true,
  "error": "Heartbeat timeout after 300 seconds",
  "started_at": "2025-10-09T23:50:18.860544",
  "finished_at": "2025-10-09T23:55:51.554861",
  "last_heartbeat_at": "2025-10-09T23:50:18.863454"
}
```

### Analysis
- Failure Reason: Heartbeat timeout detection marked the workflow as failed after no liveness signals within 300 seconds.
- Missing Artifacts: No `executions` or `code_files` persisted for this run; only early `conversations` exist.
- UI Status: Frontend correctly shows `failed` with error text; list and detail tests confirm visibility.

### Recommendations
- Ensure `WorkflowExecutor` emits periodic heartbeats throughout execution phases.
- Persist at least one `executions` entry on start to improve observability.
- Add executor-side error capture around long operations so failures surface before heartbeat expiry.
- Consider reducing heartbeat timeout in dev or adding per-environment configuration.
- Expand audit logs to include the time since last heartbeat and responsible component.

### Attachments / Sources
- Database: `ai_team.db`
- Logs: `backend.log`, `logs/ai_team.log`
- API: `/workflows/12`, `/ws/workflows/12`

### LLM Calls (from Conversations)

Aggregated from `conversations.llm_calls` for workflow 12.

```json
[
  {
    "conversation_id": 76,
    "step": "story_retrieved_and_analyzed",
    "agent": "pm",
    "timestamp": "2025-10-09 23:00:14.365542",
    "total_tokens_used": 1258,
    "total_cost": "0.0377",
    "num_calls": 1,
    "calls": [
      {
        "model": "pm-gpt-35-turbo",
        "total_tokens": 1258,
        "cost": "0.0377",
        "latency_ms": 3338,
        "timestamp": "2025-10-09T23:00:17.741977"
      }
    ]
  },
  {
    "conversation_id": 77,
    "step": "file_selection",
    "agent": "architect",
    "timestamp": "2025-10-09 23:00:17.892232",
    "total_tokens_used": 491,
    "total_cost": "0.0147",
    "num_calls": 1,
    "calls": [
      {
        "model": "architect-gpt-4.1-a",
        "total_tokens": 491,
        "cost": "0.0147",
        "latency_ms": 4792,
        "timestamp": "2025-10-09T23:00:32.701392"
      }
    ]
  },
  {
    "conversation_id": 78,
    "step": "user_acceptance_plan",
    "agent": "architect",
    "timestamp": "2025-10-09 23:00:32.704202",
    "total_tokens_used": 666,
    "total_cost": "0.0200",
    "num_calls": 1,
    "calls": [
      {
        "model": "architect-gpt-4.1-b",
        "total_tokens": 666,
        "cost": "0.0200",
        "latency_ms": 4329,
        "timestamp": "2025-10-09T23:00:37.055533"
      }
    ]
  },
  {
    "conversation_id": 79,
    "step": "dev_plan",
    "agent": "architect",
    "timestamp": "2025-10-09 23:00:37.057295",
    "total_tokens_used": 1309,
    "total_cost": "0.0393",
    "num_calls": 1,
    "calls": [
      {
        "model": "architect-gpt-4.1-c",
        "total_tokens": 397,
        "cost": "0.0119",
        "latency_ms": 3237,
        "timestamp": "2025-10-09T23:00:50.311360"
      }
    ]
  }
]
```

#### LLM Usage Metrics
- Total conversations with LLM calls: 4
- Total LLM calls: 4
- Total tokens (sum of conversation totals): 1258 + 491 + 666 + 1309 = 3724
- Total cost (sum): 0.0377 + 0.0147 + 0.0200 + 0.0393 = 0.1117
- Avg latency (approx across first calls): (3338 + 4792 + 4329 + 3237) / 4 ≈ 3924 ms


