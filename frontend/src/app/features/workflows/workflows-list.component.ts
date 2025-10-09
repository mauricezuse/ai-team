import { Component, OnInit, OnDestroy } from '@angular/core';
import { WorkflowService } from '../../core/services/workflow.service';
import { WorkflowStatusChannelService } from '../../core/services/workflow-status-channel.service';
import { Router, RouterModule } from '@angular/router';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { DropdownModule } from 'primeng/dropdown';
import { FormsModule } from '@angular/forms';
import { MessageService } from 'primeng/api';
import { ToastModule } from 'primeng/toast';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { WorkflowResponse, WorkflowStatusInfo } from '../../core/models/workflow-status.model';

@Component({
  selector: 'app-workflows-list',
  standalone: true,
  imports: [TableModule, ButtonModule, DialogModule, InputTextModule, DropdownModule, FormsModule, ToastModule, CommonModule, RouterModule],
  providers: [MessageService],
  templateUrl: './workflows-list.component.html',
  styleUrl: './workflows-list.component.scss'
})
export class WorkflowsListComponent implements OnInit, OnDestroy {
  workflows: WorkflowResponse[] = [];
  filteredWorkflows: WorkflowResponse[] = [];
  selectedWorkflow: WorkflowResponse | null = null;
  displayAddDialog = false;
  newWorkflow = { name: '' };
  searchTerm: string = '';
  selectedStatus: string = '';
  loading: boolean = false;
  jiraId: string = '';
  
  // Status tracking
  statusSubscriptions: Map<number, Subscription> = new Map();
  statusInfo: Map<number, WorkflowStatusInfo> = new Map();

  constructor(
    private workflowService: WorkflowService,
    private statusChannelService: WorkflowStatusChannelService,
    private router: Router,
    private messageService: MessageService
  ) {}

  ngOnInit() {
    this.loadWorkflows();
  }

  ngOnDestroy() {
    // Clean up all status subscriptions
    this.statusSubscriptions.forEach((subscription, workflowId) => {
      subscription.unsubscribe();
      this.statusChannelService.stopConnection(workflowId);
    });
    this.statusSubscriptions.clear();
  }

  loadWorkflows() {
    this.workflowService.getWorkflows().subscribe({
      next: (workflows) => {
        this.workflows = workflows;
        this.filteredWorkflows = [...workflows];
        
        // Start status tracking for running workflows
        this.startStatusTracking();
      },
      error: (error) => {
        console.error('Error loading workflows:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Error loading workflows'
        });
        // Also show error in DOM for tests
        this.workflows = [];
        this.filteredWorkflows = [];
      }
    });
  }

  startStatusTracking() {
    // Track status for running workflows
    this.workflows.forEach(workflow => {
      if (workflow.status === 'running' && !this.statusSubscriptions.has(workflow.id)) {
        const subscription = this.statusChannelService.getStatusStream(workflow.id).subscribe({
          next: (statusInfo) => {
            this.statusInfo.set(workflow.id, statusInfo);
            
            // Update workflow status
            const workflowIndex = this.workflows.findIndex(w => w.id === workflow.id);
            if (workflowIndex !== -1) {
              this.workflows[workflowIndex].status = statusInfo.status;
              this.workflows[workflowIndex].isTerminal = statusInfo.isTerminal;
              this.workflows[workflowIndex].heartbeat_stale = statusInfo.heartbeat_stale;
              
              // Update filtered workflows
              const filteredIndex = this.filteredWorkflows.findIndex(w => w.id === workflow.id);
              if (filteredIndex !== -1) {
                this.filteredWorkflows[filteredIndex] = { ...this.workflows[workflowIndex] };
              }
            }
            
            // Stop tracking if terminal
            if (statusInfo.isTerminal) {
              this.stopStatusTracking(workflow.id);
            }
          },
          error: (error) => {
            console.error(`Status tracking error for workflow ${workflow.id}:`, error);
          }
        });
        
        this.statusSubscriptions.set(workflow.id, subscription);
      }
    });
  }

  stopStatusTracking(workflowId: number) {
    const subscription = this.statusSubscriptions.get(workflowId);
    if (subscription) {
      subscription.unsubscribe();
      this.statusSubscriptions.delete(workflowId);
      this.statusChannelService.stopConnection(workflowId);
    }
  }

  getStatusInfo(workflowId: number): WorkflowStatusInfo | undefined {
    return this.statusInfo.get(workflowId);
  }

  filterWorkflows() {
    this.filteredWorkflows = this.workflows.filter(workflow => {
      const matchesSearch = !this.searchTerm || 
        workflow.name?.toLowerCase().includes(this.searchTerm.toLowerCase());
      
      const matchesStatus = !this.selectedStatus || workflow.status === this.selectedStatus;
      
      return matchesSearch && matchesStatus;
    });
  }

  viewWorkflow(workflow: any) {
    this.router.navigate(['/workflows', workflow.id]);
  }

  startWorkflow(workflow: any) {
    this.workflowService.startWorkflow(workflow.id).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Workflow execution started'
        });
        this.loadWorkflows();
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to start workflow'
        });
      }
    });
  }

  deleteWorkflow(workflow: any) {
    if (confirm(`Are you sure you want to delete workflow "${workflow.name}"?`)) {
      this.workflowService.deleteWorkflow(workflow.id).subscribe({
        next: () => {
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Workflow deleted successfully'
          });
          this.loadWorkflows();
        },
        error: (error) => {
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to delete workflow'
          });
        }
      });
    }
  }

  showAddDialog() {
    this.displayAddDialog = true;
    this.newWorkflow = { name: '' };
  }

  addWorkflow() {
    this.workflowService.addWorkflow(this.newWorkflow).subscribe({
      next: () => {
        this.displayAddDialog = false;
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Workflow added successfully'
        });
        this.loadWorkflows();
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to add workflow'
        });
      }
    });
  }

  createWorkflow() {
    this.router.navigate(['/workflows/create']);
  }

  createFromJira() {
    let storyId = (this.jiraId || '').trim();
    if (!storyId) {
      const prompted = (window as any).prompt ? (window as any).prompt('Enter Jira Story ID') : null;
      storyId = (prompted || '').trim();
    }
    if (storyId) {
      this.loading = true;
      this.workflowService.createWorkflowFromJira(storyId).subscribe({
        next: (response) => {
          this.loading = false;
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: response.message || `Workflow created successfully for ${storyId}`
          });
          this.loadWorkflows(); // Refresh the list
          this.jiraId = '';
        },
        error: (error) => {
          this.loading = false;
          const rawDetail = error?.error?.detail;
          const backendMsg = error?.error?.message || (typeof rawDetail === 'string' ? rawDetail : rawDetail?.message);
          const detail = backendMsg || `Could not retrieve story ${storyId} from Jira`;
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail
          });
        }
      });
    }
  }
}
