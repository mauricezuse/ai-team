import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { AgentsListComponent } from './agents-list.component';
import { AgentDetailComponent } from './agent-detail.component';

@NgModule({
  declarations: [],
  imports: [
    CommonModule,
    RouterModule.forChild([
      { path: '', component: AgentsListComponent },
      { path: ':id', component: AgentDetailComponent }
    ])
  ]
})
export class AgentsModule { }
