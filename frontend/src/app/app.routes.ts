import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'dashboard',
    pathMatch: 'full'
  },
  {
    path: 'dashboard',
    loadChildren: () => import('./features/dashboard/dashboard.module').then(m => m.DashboardModule)
  },
  {
    path: 'agents',
    loadChildren: () => import('./features/agents/agents.module').then(m => m.AgentsModule)
  },
  {
    path: 'workflows',
    loadChildren: () => import('./features/workflows/workflows.module').then(m => m.WorkflowsModule)
  },
  {
    path: '**',
    redirectTo: 'dashboard'
  }
];
