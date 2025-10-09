import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { TableModule } from 'primeng/table';
import { DialogModule } from 'primeng/dialog';
import { ToastModule } from 'primeng/toast';
import { ButtonModule } from 'primeng/button';

import { WorkflowTimelineComponent } from './workflow-timeline.component';
import { LLmCallsTableComponent } from './llm-calls-table.component';
import { PromptOutputViewerComponent } from './prompt-output-viewer.component';
import { RunComparisonComponent } from './run-comparison.component';
import { ErrorDiagnosticsComponent } from './error-diagnostics.component';
import { CodeArtifactsComponent } from './code-artifacts.component';
import { CollaborationGraphComponent } from './collaboration-graph.component';

@NgModule({
  declarations: [],
  imports: [
    CommonModule,
    WorkflowTimelineComponent,
    LLmCallsTableComponent,
    TableModule,
    DialogModule,
    ToastModule,
    ButtonModule,
    RouterModule.forChild([
      { path: '', component: WorkflowTimelineComponent },
      { path: 'llm-calls', component: LLmCallsTableComponent },
      { path: 'prompt-viewer', component: PromptOutputViewerComponent },
      { path: 'comparison', component: RunComparisonComponent },
      { path: 'diagnostics', component: ErrorDiagnosticsComponent },
      { path: 'artifacts', component: CodeArtifactsComponent },
      { path: 'collaboration', component: CollaborationGraphComponent }
    ])
  ]
})
export class WorkflowsAdvancedModule { }


