import { Component, OnInit } from '@angular/core';
import { WorkflowService } from '../../core/services/workflow.service';
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

@Component({
  selector: 'app-workflows-list',
  standalone: true,
  imports: [TableModule, ButtonModule, DialogModule, InputTextModule, DropdownModule, FormsModule, ToastModule, CommonModule, RouterModule],
  providers: [MessageService],
  templateUrl: './workflows-list.component.html',
  styleUrl: './workflows-list.component.scss'
})
export class WorkflowsListComponent implements OnInit {
  workflows: any[] = [];
  filteredWorkflows: any[] = [];
  selectedWorkflow: any;
  displayAddDialog = false;
  newWorkflow = { name: '' };
  searchTerm: string = '';
  selectedStatus: string = '';
  loading: boolean = false;

  constructor(
    private workflowService: WorkflowService, 
    private router: Router,
    private messageService: MessageService
  ) {}

  ngOnInit() {
    this.loadWorkflows();
  }

  loadWorkflows() {
    this.workflowService.getWorkflows().subscribe({
      next: (workflows) => {
        this.workflows = workflows;
        this.filteredWorkflows = [...workflows];
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
    const storyId = prompt('Enter Jira Story ID (e.g., NEGISHI-123):');
    if (storyId && storyId.trim()) {
      this.loading = true;
      this.workflowService.createWorkflowFromJira(storyId.trim()).subscribe({
        next: (response) => {
          this.loading = false;
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: response.message
          });
          this.loadWorkflows(); // Refresh the list
        },
        error: (error) => {
          this.loading = false;
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: error.error?.detail || 'Failed to create workflow from Jira'
          });
        }
      });
    }
  }
}
