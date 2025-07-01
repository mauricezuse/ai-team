import { Component, OnInit } from '@angular/core';
import { AgentService } from '../../core/services/agent.service';
import { Router } from '@angular/router';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-agents-list',
  standalone: true,
  imports: [TableModule, ButtonModule, DialogModule, InputTextModule, FormsModule],
  templateUrl: './agents-list.component.html',
  styleUrl: './agents-list.component.scss'
})
export class AgentsListComponent implements OnInit {
  agents: any[] = [];
  selectedAgent: any;
  displayAddDialog = false;
  newAgent = { name: '', role: '', goal: '' };

  constructor(private agentService: AgentService, private router: Router) {}

  ngOnInit() {
    this.loadAgents();
  }

  loadAgents() {
    this.agentService.getAgents().subscribe(agents => this.agents = agents);
  }

  viewAgent(agent: any) {
    this.router.navigate(['/agents', agent.id]);
  }

  deleteAgent(agent: any) {
    this.agentService.deleteAgent(agent.id).subscribe(() => this.loadAgents());
  }

  showAddDialog() {
    this.displayAddDialog = true;
    this.newAgent = { name: '', role: '', goal: '' };
  }

  addAgent() {
    this.agentService.addAgent(this.newAgent).subscribe(() => {
      this.displayAddDialog = false;
      this.loadAgents();
    });
  }
}
