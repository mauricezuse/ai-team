import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class WorkflowAdvancedService {
  constructor(private http: HttpClient) {}

  getLLMCalls(conversationId: string, params?: { page?: number; page_size?: number; sort_by?: string; sort_dir?: string; model?: string; q?: string; date_from?: string; date_to?: string; }): Observable<any> {
    let httpParams = new HttpParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null) {
          const s = String(v);
          if (s !== '') {
            httpParams = httpParams.set(k, s);
          }
        }
      });
    }
    return this.http.get<any>(`/api/conversations/${conversationId}/llm-calls`, { params: httpParams });
  }

  compareWorkflows(workflowId: string, withId: string): Observable<any> {
    const params = new HttpParams().set('with', withId);
    return this.http.get<any>(`/api/workflows/${workflowId}/compare`, { params });
  }

  // Executions APIs
  listExecutions(workflowId: string): Observable<any[]> {
    return this.http.get<any[]>(`/api/workflows/${workflowId}/executions`);
  }

  startExecution(workflowId: string): Observable<any> {
    return this.http.post<any>(`/api/workflows/${workflowId}/executions/start`, {});
  }

  compareExecutions(workflowId: string, execA: number, execB: number): Observable<any> {
    let params = new HttpParams().set('execA', String(execA)).set('execB', String(execB));
    return this.http.get<any>(`/api/workflows/${workflowId}/executions/compare`, { params });
  }

  // New: PR summary for workflow
  getWorkflowPr(workflowId: string): Observable<any> {
    return this.http.get<any>(`/api/workflows/${workflowId}/pr`);
  }

  // New: PR checks for workflow
  listPrChecks(workflowId: string, params?: { page?: number; page_size?: number }): Observable<any[]> {
    let httpParams = new HttpParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null) {
          httpParams = httpParams.set(k, String(v));
        }
      });
    }
    return this.http.get<any[]>(`/api/workflows/${workflowId}/pr/checks`, { params: httpParams });
  }

  // New: Diffs for workflow
  listDiffs(workflowId: string, params?: { page?: number; page_size?: number; path?: string }): Observable<any[]> {
    let httpParams = new HttpParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null) {
          httpParams = httpParams.set(k, String(v));
        }
      });
    }
    return this.http.get<any[]>(`/api/workflows/${workflowId}/diffs`, { params: httpParams });
  }

  // New: Artifacts for workflow
  listArtifacts(workflowId: string, params?: { page?: number; page_size?: number; kind?: string }): Observable<any[]> {
    let httpParams = new HttpParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null) {
          httpParams = httpParams.set(k, String(v));
        }
      });
    }
    return this.http.get<any[]>(`/api/workflows/${workflowId}/artifacts`, { params: httpParams });
  }
}


