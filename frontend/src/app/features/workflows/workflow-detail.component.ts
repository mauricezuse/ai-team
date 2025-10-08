import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { WorkflowService } from '../../core/services/workflow.service';
import { CommonModule } from '@angular/common';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { DropdownModule } from 'primeng/dropdown';
import { FormsModule } from '@angular/forms';
import { ChipModule } from 'primeng/chip';
import { MessageService } from 'primeng/api';
import { ToastModule } from 'primeng/toast';
import { AccordionModule } from 'primeng/accordion';

@Component({
  selector: 'app-workflow-detail',
  standalone: true,
  imports: [CommonModule, ButtonModule, InputTextModule, DropdownModule, FormsModule, ChipModule, ToastModule, AccordionModule],
  providers: [MessageService],
  templateUrl: './workflow-detail.component.html',
  styleUrl: './workflow-detail.component.scss'
})
export class WorkflowDetailComponent implements OnInit {
  workflow: any = null;
  searchTerm: string = '';
  selectedAgent: string = '';
  filteredConversations: any[] = [];
  uniqueAgents: string[] = [];
  agentOptions: { label: string, value: string }[] = [];

  constructor(
    private route: ActivatedRoute, 
    private workflowService: WorkflowService,
    private messageService: MessageService
  ) {}

  ngOnInit() {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.loadWorkflow(id);
    }
  }

  loadWorkflow(id: string) {
    this.workflowService.getWorkflow(id).subscribe({
      next: (workflow) => {
        this.workflow = workflow;
        this.initializeConversations();
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

  initializeConversations() {
    if (this.workflow?.conversations) {
      // Add expanded property to each conversation - expand by default
      this.workflow.conversations.forEach((conversation: any) => {
        conversation.expanded = true;
      });
      
      this.filteredConversations = [...this.workflow.conversations];
      this.uniqueAgents = [...new Set(this.workflow.conversations.map((c: any) => c.agent))] as string[];
      this.agentOptions = this.uniqueAgents.map(a => ({ label: a, value: a }));
    }
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

    this.workflowService.executeWorkflow(this.workflow.id).subscribe({
      next: (result) => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Workflow executed successfully'
        });
        this.refreshWorkflow();
      },
      error: (error) => {
        this.workflow.status = 'error';
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Error executing workflow'
        });
      }
    });
  }

  refreshWorkflow() {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.loadWorkflow(id);
    }
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
}
