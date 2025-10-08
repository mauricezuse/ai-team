import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { AgentService } from '../../core/services/agent.service';
import { CommonModule } from '@angular/common';
import { InputTextModule } from 'primeng/inputtext';
import { ButtonModule } from 'primeng/button';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-agent-detail',
  standalone: true,
  imports: [CommonModule, InputTextModule, ButtonModule, FormsModule],
  templateUrl: './agent-detail.component.html',
  styleUrl: './agent-detail.component.scss'
})
export class AgentDetailComponent implements OnInit {
  agent: any = null;
  editMode = false;
  editedAgent: any = {};

  constructor(private route: ActivatedRoute, private agentService: AgentService) {}

  ngOnInit() {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.agentService.getAgent(id).subscribe(agent => {
        this.agent = agent;
        this.editedAgent = { ...agent };
      });
    }
  }

  enableEdit() {
    this.editMode = true;
    this.editedAgent = { ...this.agent };
  }

  save() {
    // Implement update logic if backend supports it
    this.agent = { ...this.editedAgent };
    this.editMode = false;
  }

  cancel() {
    this.editMode = false;
    this.editedAgent = { ...this.agent };
  }
}
