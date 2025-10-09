import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { WorkflowService } from '../../core/services/workflow.service';

@Component({
  selector: 'app-error-diagnostics',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './error-diagnostics.component.html',
  styleUrl: './error-diagnostics.component.scss'
})
export class ErrorDiagnosticsComponent implements OnInit {
  workflowId!: string;
  failedSteps: any[] = [];
  escalations: any[] = [];
  retries: any[] = [];
  loading = false;

  constructor(private route: ActivatedRoute, private workflowService: WorkflowService) {}

  ngOnInit(): void {
    this.workflowId = this.route.parent?.snapshot.paramMap.get('id') || '';
    if (!this.workflowId) return;
    this.loading = true;
    this.workflowService.getWorkflow(this.workflowId).subscribe(wf => {
      const convs = wf?.conversations || [];
      this.failedSteps = convs.filter((c: any) => String(c.status || '').toLowerCase() === 'failed');
      this.escalations = convs.flatMap((c: any) => (c.escalations || []).map((e: any) => ({ ...e, conversationId: c.id })));
      // Best-effort retries: not explicitly modeled; infer by duplicate steps or status
      const stepCounts: Record<string, number> = {};
      convs.forEach((c: any) => {
        const k = String(c.step || '').toLowerCase();
        stepCounts[k] = (stepCounts[k] || 0) + 1;
      });
      this.retries = Object.entries(stepCounts).filter(([, v]) => (v as number) > 1).map(([k, v]) => ({ step: k, count: v }));
      this.loading = false;
    }, () => this.loading = false);
  }
}


