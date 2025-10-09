import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { WorkflowAdvancedService } from '../../core/services/workflow-advanced.service';
import { WorkflowService } from '../../core/services/workflow.service';
import { FeatureFlagService } from '../../core/services/feature-flag.service';
import { FormsModule } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { TableModule } from 'primeng/table';

@Component({
  selector: 'app-llm-calls-table',
  standalone: true,
  imports: [CommonModule, TableModule, FormsModule, ButtonModule],
  templateUrl: './llm-calls-table.component.html',
  styleUrl: './llm-calls-table.component.scss'
})
export class LLmCallsTableComponent implements OnInit {
  workflowId!: string;
  conversationId!: string | null;
  calls: any[] = [];
  total = 0;
  pageSize = 20;
  page = 1;
  sortBy = 'timestamp';
  sortDir = 'desc';
  search = '';
  model = '';

  redactionEnabled = false;

  constructor(private route: ActivatedRoute, private advancedService: WorkflowAdvancedService, private flags: FeatureFlagService, private workflowService: WorkflowService) {}

  ngOnInit(): void {
    this.workflowId = this.route.parent?.snapshot.paramMap.get('id') || '';
    this.conversationId = this.route.snapshot.queryParamMap.get('conversationId');
    this.redactionEnabled = this.flags.isEnabled('REDACT_SENSITIVE', false);
    if (!this.conversationId) {
      // Auto-select first conversation if none provided
      if (this.workflowId) {
        this.workflowService.getWorkflow(this.workflowId).subscribe(wf => {
          const convs = wf?.conversations || [];
          if (convs.length > 0) {
            this.conversationId = String(convs[0].id);
          }
          this.reload();
        }, () => this.reload());
      } else {
        this.reload();
      }
    } else {
      this.reload();
    }
  }

  reload() {
    if (!this.conversationId) { this.calls = []; this.total = 0; return; }
    this.advancedService.getLLMCalls(this.conversationId, {
      page: this.page,
      page_size: this.pageSize,
      sort_by: this.sortBy,
      sort_dir: this.sortDir,
      q: this.search || undefined,
      model: this.model || undefined
    }).subscribe(res => {
      this.calls = res?.calls || [];
      this.total = res?.total || 0;
    });
  }

  onPage(event: any) {
    // event.first, event.rows give pagination info
    this.pageSize = event.rows;
    this.page = Math.floor(event.first / event.rows) + 1;
    this.reload();
  }

  exportJson() {
    const blob = new Blob([JSON.stringify(this.calls, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `llm-calls-${this.conversationId}-page${this.page}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }
}


