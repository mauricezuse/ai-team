import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { CardModule } from 'primeng/card';
import { TimelineModule } from 'primeng/timeline';
import { FormsModule } from '@angular/forms';
import { WorkflowService } from '../../core/services/workflow.service';

@Component({
  selector: 'app-workflow-timeline',
  standalone: true,
  imports: [CommonModule, RouterModule, CardModule, TimelineModule, FormsModule],
  templateUrl: './workflow-timeline.component.html',
  styleUrl: './workflow-timeline.component.scss'
})
export class WorkflowTimelineComponent implements OnInit {
  workflowId!: string;
  steps: any[] = [];
  filteredSteps: any[] = [];
  loading = false;
  error: string | null = null;
  filterText = '';

  constructor(private route: ActivatedRoute, private workflowService: WorkflowService) {}

  ngOnInit(): void {
    this.workflowId = this.route.parent?.snapshot.paramMap.get('id') || this.route.snapshot.paramMap.get('id') || '';
    this.loadTimeline();
  }

  private loadTimeline() {
    if (!this.workflowId) return;
    this.loading = true;
    this.workflowService.getWorkflow(this.workflowId).subscribe({
      next: (wf) => {
        const conversations = wf?.conversations || [];
        this.steps = conversations.map((c: any) => ({
          step: c.step,
          agent: c.agent,
          status: c.status,
          timestamp: c.timestamp,
          id: c.id
        }));
        this.applyFilter();
        this.loading = false;
      },
      error: () => {
        this.error = 'Failed to load workflow timeline';
        this.loading = false;
      }
    });
  }

  applyFilter() {
    const t = (this.filterText || '').toLowerCase();
    if (!t) { this.filteredSteps = this.steps; return; }
    this.filteredSteps = this.steps.filter(s =>
      (s.agent && String(s.agent).toLowerCase().includes(t)) ||
      (s.step && String(s.step).toLowerCase().includes(t))
    );
  }
}


