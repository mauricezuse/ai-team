import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { WorkflowsListComponent } from './workflows-list.component';
import { WorkflowDetailComponent } from './workflow-detail.component';
import { CreateWorkflowComponent } from './create-workflow.component';

@NgModule({
  declarations: [],
  imports: [
    CommonModule,
    WorkflowsListComponent,
    WorkflowDetailComponent,
    CreateWorkflowComponent,
    RouterModule.forChild([
      { path: '', component: WorkflowsListComponent },
      { path: 'create', component: CreateWorkflowComponent },
      { path: ':id', component: WorkflowDetailComponent },
      { path: ':id/advanced', loadChildren: () => import('../workflows-advanced/workflows-advanced.module').then(m => m.WorkflowsAdvancedModule) }
    ])
  ]
})
export class WorkflowsModule { }
