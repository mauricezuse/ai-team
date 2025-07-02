import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { WorkflowsListComponent } from './workflows-list.component';
import { WorkflowDetailComponent } from './workflow-detail.component';

@NgModule({
  declarations: [],
  imports: [
    CommonModule,
    RouterModule.forChild([
      { path: '', component: WorkflowsListComponent },
      { path: ':id', component: WorkflowDetailComponent }
    ])
  ]
})
export class WorkflowsModule { }
