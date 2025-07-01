import { Component, OnInit } from '@angular/core';
import { WorkflowService } from '../../core/services/workflow.service';
import { Router } from '@angular/router';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-workflows-list',
  standalone: true,
  imports: [TableModule, ButtonModule, DialogModule, InputTextModule, FormsModule],
  templateUrl: './workflows-list.component.html',
  styleUrl: './workflows-list.component.scss'
})
export class WorkflowsListComponent implements OnInit {
  workflows: any[] = [];
  selectedWorkflow: any;
  displayAddDialog = false;
  newWorkflow = { name: '' };

  constructor(private workflowService: WorkflowService, private router: Router) {}

  ngOnInit() {
    this.loadWorkflows();
  }

  loadWorkflows() {
    this.workflowService.getWorkflows().subscribe(workflows => this.workflows = workflows);
  }

  viewWorkflow(workflow: any) {
    this.router.navigate(['/workflows', workflow.id]);
  }

  startWorkflow(workflow: any) {
    this.workflowService.startWorkflow(workflow.id).subscribe();
  }

  deleteWorkflow(workflow: any) {
    this.workflowService.deleteWorkflow(workflow.id).subscribe(() => this.loadWorkflows());
  }

  showAddDialog() {
    this.displayAddDialog = true;
    this.newWorkflow = { name: '' };
  }

  addWorkflow() {
    this.workflowService.addWorkflow(this.newWorkflow).subscribe(() => {
      this.displayAddDialog = false;
      this.loadWorkflows();
    });
  }
}
