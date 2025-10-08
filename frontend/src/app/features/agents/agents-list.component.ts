import { Component, OnInit } from '@angular/core';
import { AgentService } from '../../core/services/agent.service';
import { Router } from '@angular/router';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { FormsModule } from '@angular/forms';
import { MessageService } from 'primeng/api';
import { ToastModule } from 'primeng/toast';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-agents-list',
  standalone: true,
  imports: [TableModule, ButtonModule, DialogModule, InputTextModule, FormsModule, ToastModule, CommonModule],
  providers: [MessageService],
  templateUrl: './agents-list.component.html',
  styleUrl: './agents-list.component.scss'
})
export class AgentsListComponent implements OnInit {
  agents: any[] = [];
  selectedAgent: any;
  displayAddDialog = false;
  newAgent = { name: '', role: '', goal: '' };

  constructor(
    private agentService: AgentService, 
    private router: Router,
    private messageService: MessageService
  ) {}

  ngOnInit() {
    this.loadAgents();
  }

  loadAgents() {
    this.agentService.getAgents().subscribe({
      next: (agents) => {
        this.agents = agents;
      },
      error: (error) => {
        console.error('Error loading agents:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load agents'
        });
      }
    });
  }

  viewAgent(agent: any) {
    this.router.navigate(['/agents', agent.id]);
  }

  deleteAgent(agent: any) {
    if (confirm(`Are you sure you want to delete agent "${agent.name}"?`)) {
      this.agentService.deleteAgent(agent.id).subscribe({
        next: () => {
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Agent deleted successfully'
          });
          this.loadAgents();
        },
        error: (error) => {
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to delete agent'
          });
        }
      });
    }
  }

  showAddDialog() {
    this.displayAddDialog = true;
    this.newAgent = { name: '', role: '', goal: '' };
  }

  addAgent() {
    this.agentService.addAgent(this.newAgent).subscribe({
      next: () => {
        this.displayAddDialog = false;
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Agent added successfully'
        });
        this.loadAgents();
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to add agent'
        });
      }
    });
  }
}
