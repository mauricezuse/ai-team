import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { WorkflowService } from '../../core/services/workflow.service';

@Component({
  selector: 'app-code-artifacts',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './code-artifacts.component.html',
  styleUrl: './code-artifacts.component.scss'
})
export class CodeArtifactsComponent implements OnInit {
  workflowId!: string;
  files: Array<{ conversationId: number, filename: string, file_path?: string }> = [];
  loading = false;

  constructor(private route: ActivatedRoute, private workflowService: WorkflowService) {}

  ngOnInit(): void {
    this.workflowId = this.route.parent?.snapshot.paramMap.get('id') || '';
    if (!this.workflowId) return;
    this.loading = true;
    this.workflowService.getWorkflow(this.workflowId).subscribe(wf => {
      const convs = wf?.conversations || [];
      const collected: Array<{ conversationId: number, filename: string, file_path?: string }> = [];
      convs.forEach((c: any) => {
        (c.code_files || []).forEach((f: any) => {
          const filename = typeof f === 'string' ? f : (f.filename || f.file_path);
          const file_path = typeof f === 'string' ? f : f.file_path;
          if (filename) collected.push({ conversationId: c.id, filename, file_path });
        });
      });
      this.files = collected;
      this.loading = false;
    }, () => this.loading = false);
  }
}


