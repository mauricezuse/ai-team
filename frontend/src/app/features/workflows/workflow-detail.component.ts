import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { WorkflowService } from '../../core/services/workflow.service';
import { WorkflowAdvancedService } from '../../core/services/workflow-advanced.service';
import { WorkflowStatusChannelService } from '../../core/services/workflow-status-channel.service';
import { CommonModule } from '@angular/common';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { DropdownModule } from 'primeng/dropdown';
import { FormsModule } from '@angular/forms';
import { ChipModule } from 'primeng/chip';
import { MessageService } from 'primeng/api';
import { ToastModule } from 'primeng/toast';
import { AccordionModule } from 'primeng/accordion';
import { TabViewModule } from 'primeng/tabview';
import { Subscription } from 'rxjs';
import { WorkflowResponse, WorkflowStatusInfo, ConnectionType } from '../../core/models/workflow-status.model';

@Component({
  selector: 'app-workflow-detail',
  standalone: true,
  imports: [CommonModule, ButtonModule, InputTextModule, DropdownModule, FormsModule, ChipModule, ToastModule, AccordionModule, TabViewModule, RouterModule],
  providers: [MessageService],
  templateUrl: './workflow-detail.component.html',
  styleUrl: './workflow-detail.component.scss'
})
export class WorkflowDetailComponent implements OnInit, OnDestroy {
  workflow: WorkflowResponse | null = null;
  searchTerm: string = '';
  selectedAgent: string = '';
  filteredConversations: any[] = [];
  uniqueAgents: string[] = [];
  agentOptions: { label: string, value: string }[] = [];
  
  // Status tracking
  statusInfo: WorkflowStatusInfo | null = null;
  connectionType: ConnectionType | undefined;
  statusSubscription: Subscription | null = null;
  workflowId: number | null = null;
  
  // UI state
  activeTabIndex: number = 2; // default to Conversations tab to preserve existing tests expecting conversations visible

  // Aggregated insights
  allCodeFiles: any[] = [];
  prInfo: { url?: string; skippedReason?: string } = {};
  prChecks: any[] = [];
  artifacts: any[] = [];
  diffs: any[] = [];
  llmConversations: Array<{ id: number; label: string; calls: any[] }> = [];
  llmSelectedConvId: number | null = null;
  escalationsList: Array<{ from_agent: string; to_agent: string; reason: string; status: string }> = [];
  // Executions compare UI state
  execA: number | null = null;
  execB: number | null = null;
  execCompareResult: any | null = null;
  // Live event stream
  liveLogs: Array<{ level?: string; message?: string; timestamp?: string }> = [];
  liveConversations: any[] = [];
  private streamCloser: { close: () => void } | null = null;

  constructor(
    private route: ActivatedRoute, 
    private workflowService: WorkflowService,
    private advancedService: WorkflowAdvancedService,
    private statusChannelService: WorkflowStatusChannelService,
    private messageService: MessageService
  ) {}

  ngOnInit() {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.workflowId = parseInt(id);
      this.loadWorkflow(id);
      this.startStatusTracking();
      this.startEventStream();
    }
  }

  refreshPrChecks() {
    if (!this.workflowId) return;
    this.advancedService.refreshPrChecks(String(this.workflowId)).subscribe({
      next: () => {
        this.advancedService.listPrChecks(String(this.workflowId), { page: 1, page_size: 50 }).subscribe(checks => {
          this.prChecks = checks || [];
          this.messageService.add({ severity: 'success', summary: 'Refreshed', detail: 'PR & Checks updated' });
        });
      },
      error: () => this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to refresh PR & Checks' })
    });
  }

  refreshDiffs() {
    if (!this.workflowId) return;
    this.advancedService.refreshDiffs(String(this.workflowId)).subscribe({
      next: () => {
        this.advancedService.listDiffs(String(this.workflowId), { page: 1, page_size: 100 }).subscribe(diffs => {
          this.diffs = diffs || [];
          this.messageService.add({ severity: 'success', summary: 'Refreshed', detail: 'Diffs updated' });
        });
      },
      error: () => this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to refresh diffs' })
    });
  }

  refreshArtifacts() {
    if (!this.workflowId) return;
    this.advancedService.refreshArtifacts(String(this.workflowId)).subscribe({
      next: () => {
        this.advancedService.listArtifacts(String(this.workflowId), { page: 1, page_size: 50 }).subscribe(arts => {
          this.artifacts = arts || [];
          this.messageService.add({ severity: 'success', summary: 'Refreshed', detail: 'Artifacts updated' });
        });
      },
      error: () => this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to refresh artifacts' })
    });
  }

  ngOnDestroy() {
    if (this.statusSubscription) {
      this.statusSubscription.unsubscribe();
    }
    if (this.workflowId) {
      this.statusChannelService.stopConnection(this.workflowId);
    }
    if (this.streamCloser) {
      this.streamCloser.close();
      this.streamCloser = null;
    }
  }

  loadWorkflow(id: string) {
    this.workflowService.getWorkflow(id).subscribe({
      next: (workflow) => {
        this.workflow = workflow;
        // Attach executions list
        this.advancedService.listExecutions(String(workflow.id)).subscribe(execs => {
          if (this.workflow) {
            (this.workflow as any).executions = execs || [];
          }
        });
        this.initializeConversations();

        // Compute aggregated views
        this.computeAggregates();

        // Fetch PR summary and checks
        this.advancedService.getWorkflowPr(String(workflow.id)).subscribe({
          next: (pr) => {
            if (pr && pr.url) {
              this.prInfo = { url: pr.url };
            }
          },
          error: () => {}
        });
        this.advancedService.listPrChecks(String(workflow.id), { page: 1, page_size: 50 }).subscribe({
          next: (checks) => { this.prChecks = checks || []; },
          error: () => { this.prChecks = []; }
        });

        // Fetch diffs meta
        this.advancedService.listDiffs(String(workflow.id), { page: 1, page_size: 100 }).subscribe({
          next: (diffs) => { this.diffs = diffs || []; },
          error: () => { this.diffs = []; }
        });

        // Fetch artifacts
        this.advancedService.listArtifacts(String(workflow.id), { page: 1, page_size: 50 }).subscribe({
          next: (arts) => { this.artifacts = arts || []; },
          error: () => { this.artifacts = []; }
        });
      },
      error: (error) => {
        console.error('Error loading workflow:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load workflow'
        });
      }
    });
  }

  startStatusTracking() {
    if (!this.workflowId) return;

    this.statusSubscription = this.statusChannelService.getStatusStream(this.workflowId).subscribe({
      next: (statusInfo) => {
        this.statusInfo = statusInfo;
        this.connectionType = this.statusChannelService.getConnectionType(this.workflowId!);
        
        // Ensure the workflow object reflects latest status details
        if (this.workflow) {
          // Always sync core status fields
          this.workflow.status = statusInfo.status;
          this.workflow.isTerminal = statusInfo.isTerminal;
          this.workflow.heartbeat_stale = statusInfo.heartbeat_stale;

          // Propagate error and timestamps if provided by the status stream
          if (typeof (statusInfo as any).error !== 'undefined') {
            (this.workflow as any).error = (statusInfo as any).error;
          }
          if (typeof (statusInfo as any).started_at !== 'undefined') {
            (this.workflow as any).started_at = (statusInfo as any).started_at as any;
          }
          if (typeof (statusInfo as any).finished_at !== 'undefined') {
            (this.workflow as any).finished_at = (statusInfo as any).finished_at as any;
          }
          if (typeof (statusInfo as any).last_heartbeat_at !== 'undefined') {
            (this.workflow as any).last_heartbeat_at = (statusInfo as any).last_heartbeat_at as any;
          }
        }

        // Show warning for stale heartbeat
        if (statusInfo.heartbeat_stale && statusInfo.status === 'running') {
          this.messageService.add({
            severity: 'warn',
            summary: 'Status Warning',
            detail: 'Workflow heartbeat is stale - process may have stopped unexpectedly'
          });
        }
      },
      error: (error) => {
        console.error('Status tracking error:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Status Error',
          detail: 'Failed to track workflow status'
        });
      }
    });
  }

  reconcileStatus() {
    if (!this.workflowId) return;

    this.statusChannelService.reconcileWorkflowStatus(this.workflowId).subscribe({
      next: (response) => {
        this.messageService.add({
          severity: 'success',
          summary: 'Status Reconciled',
          detail: response.message
        });
      },
      error: (error) => {
        console.error('Reconciliation error:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Reconciliation Failed',
          detail: 'Failed to reconcile workflow status'
        });
      }
    });
  }

  initializeConversations() {
    if (this.workflow?.conversations) {
      // Infer missing agent labels from common step names and expand by default
      const stepToAgent: Record<string, string> = {
        'story_retrieved_and_analyzed': 'Product Manager',
        'story_analysis': 'Product Manager',
        'architecture_design': 'Solution Architect',
        'implementation_plan_generated': 'Solution Architect',
        'tasks_broken_down_with_collaboration': 'Solution Architect',
        'codebase_indexed': 'Backend Developer',
        'implementation': 'Backend Developer',
        'tasks_executed_with_escalation': 'Backend Developer',
        'frontend_implementation': 'Frontend Developer',
        'final_review_and_testing_completed': 'QA Tester',
        'pr_skipped': 'Code Reviewer'
      };
      this.workflow.conversations.forEach((conversation: any) => {
        const stepKey = String(conversation.step || '').trim().toLowerCase();
        if (!conversation.agent) {
          conversation.agent = stepToAgent[stepKey] || conversation.agent || '';
        }
        conversation.expanded = true;
      });
      
      this.filteredConversations = [...this.workflow.conversations];
      this.uniqueAgents = [...new Set(this.workflow.conversations.map((c: any) => c.agent))] as string[];
      this.agentOptions = this.uniqueAgents.map(a => ({ label: a, value: a }));
    }
  }

  private computeAggregates() {
    const wf: any = this.workflow;
    if (!wf) return;
    // Aggregate code files
    const files: any[] = [];
    (wf.conversations || []).forEach((c: any) => {
      (c.code_files || []).forEach((f: any) => files.push(f));
    });
    // de-duplicate by path/name string rep
    const seen = new Set<string>();
    this.allCodeFiles = files.filter(f => {
      const key = typeof f === 'string' ? f : (f.file_path || f.filename || JSON.stringify(f));
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });

    // PR info
    let prUrl: string | undefined;
    let skippedReason: string | undefined;
    (wf.conversations || []).forEach((c: any) => {
      if (c.step === 'pr_created' && c.pr && c.pr.url) {
        prUrl = c.pr.url;
      }
      if (c.step === 'pr_skipped' && c.reason) {
        skippedReason = c.reason;
      }
    });
    this.prInfo = { url: prUrl, skippedReason };

    // LLM conversations list
    this.llmConversations = (wf.conversations || [])
      .filter((c: any) => c.llm_calls && c.llm_calls.length > 0)
      .map((c: any) => ({ id: c.id, label: `${c.agent || 'Agent'} - ${c.step || 'Step'}`, calls: c.llm_calls }));
    this.llmSelectedConvId = this.llmConversations.length > 0 ? this.llmConversations[0].id : null;

    // Escalations aggregate
    const escalations: any[] = [];
    (wf.conversations || []).forEach((c: any) => {
      (c.escalations || []).forEach((e: any) => escalations.push(e));
    });
    this.escalationsList = escalations;
  }

  get selectedLlmCalls(): any[] {
    if (!this.llmSelectedConvId) return [];
    const found = this.llmConversations.find(x => x.id === this.llmSelectedConvId);
    return found ? (found.calls || []) : [];
  }

  compareExecutions() {
    if (!this.workflowId || !this.execA || !this.execB) {
      this.execCompareResult = null;
      return;
    }
    this.advancedService.compareExecutions(String(this.workflowId), this.execA, this.execB).subscribe({
      next: (res) => {
        this.execCompareResult = res;
      },
      error: () => {
        this.execCompareResult = { error: 'Failed to compare executions' };
      }
    });
  }

  filterConversations() {
    if (!this.workflow?.conversations) return;

    this.filteredConversations = this.workflow.conversations.filter((conversation: any) => {
      const matchesSearch = !this.searchTerm || 
        conversation.details?.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
        conversation.output?.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
        conversation.step?.toLowerCase().includes(this.searchTerm.toLowerCase());
      
      const matchesAgent = !this.selectedAgent || conversation.agent === this.selectedAgent;
      
      return matchesSearch && matchesAgent;
    });
  }

  filterByAgent(agentName: string) {
    this.selectedAgent = agentName;
    this.filterConversations();
  }

  toggleConversation(conversation: any) {
    conversation.expanded = !conversation.expanded;
  }

  executeWorkflow() {
    if (!this.workflow) return;

    this.workflow.status = 'running';
    this.messageService.add({
      severity: 'info',
      summary: 'Executing',
      detail: 'Workflow execution started...'
    });

    this.workflowService.executeWorkflow(String(this.workflow.id)).subscribe({
      next: (result) => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Workflow executed successfully'
        });
        this.refreshWorkflow();
      },
      error: (error) => {
        if (this.workflow) {
          this.workflow.status = 'error';
        }
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Error executing workflow'
        });
      }
    });
  }

  startNewExecution() {
    if (!this.workflow) return;
    this.messageService.add({ severity: 'info', summary: 'Starting', detail: 'Starting new execution...' });
    this.advancedService.startExecution(String(this.workflow.id)).subscribe({
      next: (ex) => {
        this.messageService.add({ severity: 'success', summary: 'Execution started', detail: `Execution #${ex.id}` });
        this.refreshWorkflow();
      },
      error: () => this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to start execution' })
    });
  }

  refreshWorkflow() {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.loadWorkflow(id);
    }
  }

  private startEventStream() {
    if (!this.workflowId) return;
    this.streamCloser = this.statusChannelService.connectEventStream(this.workflowId, (evt) => {
      if (!evt || !evt.type) return;
      if (evt.type === 'log') {
        this.liveLogs.unshift({ level: evt.level || 'info', message: evt.message || '', timestamp: evt.timestamp });
        this.liveLogs = this.liveLogs.slice(0, 200);
      } else if (evt.type === 'conversation' && evt.conversation) {
        this.liveConversations.unshift(evt.conversation);
        this.filteredConversations = [evt.conversation, ...(this.filteredConversations || [])];
      } else if (evt.type === 'status' && this.workflow) {
        this.workflow.status = evt.status;
      }
    });
  }

  getFileUrl(file: any): string {
    // Handle both string and object file formats
    const filePath = typeof file === 'string' ? file : file.file_path || file.filename;
    return `https://github.com/mauricezuse/negishi-freelancing/blob/main/${filePath}`;
  }

  getFileDisplayName(file: any): string {
    // Get display name for file
    if (typeof file === 'string') {
      return file.split('/').pop() || file;
    }
    return file.filename || file.file_path?.split('/').pop() || 'Unknown File';
  }

  getFilePath(file: any): string {
    // Get full file path
    if (typeof file === 'string') {
      return file;
    }
    return file.file_path || file.filename || '';
  }

  getCodePreview(file: any): string {
    // Generate a code preview based on file type
    const filename = this.getFileDisplayName(file);
    const fileExtension = filename.split('.').pop();
    const extension = fileExtension ? fileExtension.toLowerCase() : 'txt';
    
    // Sample code content based on file type
    const sampleCode: { [key: string]: string } = {
      'py': `# ${filename}
def main():
    """Main function for ${filename}"""
    pass

if __name__ == "__main__":
    main()`,
      'ts': `// ${filename}
export class ${filename.split('.')[0]} {
    constructor() {
        // Implementation here
    }
}`,
      'md': `# ${filename}

## Description
This file contains the implementation for the feature.

## Usage
\`\`\`typescript
// Example usage
\`\`\``,
      'spec.ts': `// ${filename}
import { ComponentFixture, TestBed } from '@angular/core/testing';

describe('${filename.split('.')[0]}', () => {
  it('should create', () => {
    expect(true).toBeTruthy();
  });
});`
    };
    
    return sampleCode[extension] || `// ${filename}\n// Generated code content would appear here\n// This is a preview of the ${extension} file`;
  }

  getLLMCallHeader(call: any): string {
    // Create a header for the LLM call accordion tab
    const timestamp = new Date(call.timestamp).toLocaleTimeString();
    return `${call.model} - ${call.total_tokens} tokens - $${call.cost} - ${timestamp}`;
  }
}
