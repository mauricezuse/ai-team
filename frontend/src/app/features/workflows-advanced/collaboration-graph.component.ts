import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { WorkflowService } from '../../core/services/workflow.service';

@Component({
  selector: 'app-collaboration-graph',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './collaboration-graph.component.html',
  styleUrl: './collaboration-graph.component.scss'
})
export class CollaborationGraphComponent implements OnInit {
  workflowId!: string;
  edges: Array<{ from: string, to: string, count: number }> = [];
  nodes: string[] = [];
  loading = false;

  constructor(private route: ActivatedRoute, private workflowService: WorkflowService) {}

  ngOnInit(): void {
    this.workflowId = this.route.parent?.snapshot.paramMap.get('id') || '';
    if (!this.workflowId) return;
    this.loading = true;
    this.workflowService.getWorkflow(this.workflowId).subscribe(wf => {
      const convs = wf?.conversations || [];
      const counts = new Map<string, number>();
      const nodeSet = new Set<string>();
      convs.forEach((c: any) => {
        (c.collaborations || []).forEach((collab: any) => {
          const from = collab.from_agent || 'unknown';
          const to = collab.to_agent || 'unknown';
          nodeSet.add(from); nodeSet.add(to);
          const key = `${from}=>${to}`;
          counts.set(key, (counts.get(key) || 0) + 1);
        });
        (c.escalations || []).forEach((e: any) => {
          const from = e.from_agent || 'unknown';
          const to = e.to_agent || 'unknown';
          nodeSet.add(from); nodeSet.add(to);
          const key = `${from}=>${to}`;
          counts.set(key, (counts.get(key) || 0) + 1);
        });
      });
      this.nodes = Array.from(nodeSet);
      this.edges = Array.from(counts.entries()).map(([k, v]) => {
        const [from, to] = k.split('=>');
        return { from, to, count: v };
      });
      this.loading = false;
    }, () => this.loading = false);
  }
}


