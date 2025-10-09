import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { TextareaModule } from 'primeng/textarea';
import { DropdownModule } from 'primeng/dropdown';
import { MessageService } from 'primeng/api';
import { ToastModule } from 'primeng/toast';
import { Router } from '@angular/router';
import { WorkflowService } from '../../core/services/workflow.service';

@Component({
  selector: 'app-create-workflow',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    ButtonModule,
    InputTextModule,
    TextareaModule,
    DropdownModule,
    ToastModule
  ],
  providers: [MessageService],
  templateUrl: './create-workflow.component.html',
  styleUrl: './create-workflow.component.scss'
})
export class CreateWorkflowComponent implements OnInit {
  workflowForm: FormGroup;
  loading = false;
  submittedInvalid = false;

  constructor(
    private fb: FormBuilder,
    private workflowService: WorkflowService,
    private messageService: MessageService,
    private router: Router
  ) {
    this.workflowForm = this.fb.group({
      jira_story_id: ['', [Validators.required, Validators.pattern(/^[A-Z]+-\d+$/)]],
      jira_story_title: ['', [Validators.required, Validators.minLength(10)]],
      jira_story_description: ['', [Validators.required, Validators.minLength(20)]],
      repository_url: ['https://github.com/mauricezuse/negishi-freelancing', [Validators.required]],
      target_branch: ['main', [Validators.required]]
    });
  }

  ngOnInit() {
    // Form is already initialized in constructor
  }

  onSubmit() {
    if (this.workflowForm.valid) {
      this.submittedInvalid = false;
      this.loading = true;
      
      this.workflowService.createWorkflow(this.workflowForm.value).subscribe({
        next: (workflow) => {
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: `Workflow ${workflow.jira_story_id} created successfully`
          });
          
          // Navigate to the new workflow detail page
          setTimeout(() => {
            this.router.navigate(['/workflows', workflow.id]);
          }, 300);
        },
        error: (error) => {
          this.loading = false;
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: error.error?.detail || 'Failed to create workflow'
          });
        }
      });
    } else {
      // Surface validation errors to the user
      Object.values(this.workflowForm.controls).forEach(control => control.markAsTouched());
      this.messageService.add({
        severity: 'warn',
        summary: 'Validation Error',
        detail: 'Please fill in all required fields correctly'
      });
      this.submittedInvalid = true;
    }
  }

  onCancel() {
    this.router.navigate(['/workflows']);
  }
}
