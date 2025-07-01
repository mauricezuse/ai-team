import { Component, OnInit } from '@angular/core';
import { AgentService } from '../../core/services/agent.service';
import { WorkflowService } from '../../core/services/workflow.service';
import { CardModule } from 'primeng/card';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CardModule],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent implements OnInit {
  agentCount = 0;
  workflowCount = 0;

  constructor(private agentService: AgentService, private workflowService: WorkflowService) {}

  ngOnInit() {
    this.agentService.getAgents().subscribe(agents => this.agentCount = agents.length);
    this.workflowService.getWorkflows().subscribe(workflows => this.workflowCount = workflows.length);
  }
}
