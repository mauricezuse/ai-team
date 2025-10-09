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
  executions: any[] = [];
  execA: number | null = null;
  execB: number | null = null;
  data: any = null;
  loading = false;

  constructor(private route: ActivatedRoute, private adv: WorkflowAdvancedService) {}

  ngOnInit(): void {
    this.workflowId = this.route.parent?.snapshot.paramMap.get('id') || '';
    if (this.workflowId) {
      this.adv.listExecutions(this.workflowId).subscribe(list => {
        this.executions = list || [];
        if (this.executions.length >= 2) {
          this.execA = this.executions[1]?.id;
          this.execB = this.executions[0]?.id;
        }
      });
    }
  }

  compare() {
    if (!this.execA || !this.execB) return;
    this.loading = true;
    this.adv.compareExecutions(this.workflowId, this.execA, this.execB).subscribe(res => {
      this.data = res;
      this.loading = false;
    }, () => this.loading = false);
  }
}


