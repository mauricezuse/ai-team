import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { WorkflowService } from '../../core/services/workflow.service';
import { CommonModule } from '@angular/common';
import { ButtonModule } from 'primeng/button';

@Component({
  selector: 'app-workflow-detail',
  standalone: true,
  imports: [CommonModule, ButtonModule],
  templateUrl: './workflow-detail.component.html',
  styleUrl: './workflow-detail.component.scss'
})
export class WorkflowDetailComponent implements OnInit {
  workflow: any = null;

  constructor(private route: ActivatedRoute, private workflowService: WorkflowService) {}

  ngOnInit() {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.workflowService.getWorkflow(id).subscribe(workflow => {
        this.workflow = workflow;
      });
    }
  }
}
