import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { FeatureFlagService } from '../../core/services/feature-flag.service';
import { WorkflowAdvancedService } from '../../core/services/workflow-advanced.service';

@Component({
  selector: 'app-prompt-output-viewer',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './prompt-output-viewer.component.html',
  styleUrl: './prompt-output-viewer.component.scss'
})
export class PromptOutputViewerComponent implements OnInit {
  conversationId: string | null = null;
  redactionEnabled = false;
  calls: any[] = [];
  loading = false;

  constructor(private route: ActivatedRoute, private flags: FeatureFlagService, private adv: WorkflowAdvancedService) {}

  ngOnInit(): void {
    this.conversationId = this.route.snapshot.queryParamMap.get('conversationId');
    this.redactionEnabled = this.flags.isEnabled('REDACT_SENSITIVE', false);
    if (this.conversationId) {
      this.loading = true;
      this.adv.getLLMCalls(this.conversationId, { page: 1, page_size: 1, sort_by: 'timestamp', sort_dir: 'desc' }).subscribe(res => {
        this.calls = res?.calls || [];
        this.loading = false;
      }, () => this.loading = false);
    }
  }
}


