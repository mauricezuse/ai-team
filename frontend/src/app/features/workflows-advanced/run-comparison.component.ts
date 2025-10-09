import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { WorkflowAdvancedService } from '../../core/services/workflow-advanced.service';

@Component({
  selector: 'app-run-comparison',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './run-comparison.component.html',
  styleUrl: './run-comparison.component.scss'
})
export class RunComparisonComponent implements OnInit {
  workflowId!: string;
  otherId = '';
  data: any = null;
  loading = false;

  constructor(private route: ActivatedRoute, private adv: WorkflowAdvancedService) {}

  ngOnInit(): void {
    this.workflowId = this.route.parent?.snapshot.paramMap.get('id') || '';
  }

  compare() {
    if (!this.otherId) return;
    this.loading = true;
    this.adv.compareWorkflows(this.workflowId, this.otherId).subscribe(res => {
      this.data = res;
      this.loading = false;
    }, () => this.loading = false);
  }
}


