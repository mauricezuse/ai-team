import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { WorkflowResponse } from '../models/workflow-status.model';

@Injectable({
  providedIn: 'root'
})
export class WorkflowService {
  private apiUrl = '/api/workflows';

  constructor(private http: HttpClient) {}

  getWorkflows(): Observable<any[]> {
    return this.http.get<any[]>(this.apiUrl);
  }

  addWorkflow(workflow: any): Observable<any> {
    return this.http.post<any>(this.apiUrl, workflow);
  }

  deleteWorkflow(id: string): Observable<any> {
    return this.http.delete<any>(`${this.apiUrl}/${id}`);
  }

  startWorkflow(id: string): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/${id}/execute`, {});
  }

  getWorkflow(id: string, etag?: string): Observable<WorkflowResponse> {
    let headers = new HttpHeaders();
    if (etag) {
      headers = headers.set('If-None-Match', etag);
    }
    return this.http.get<WorkflowResponse>(`${this.apiUrl}/${id}`, { headers });
  }

  executeWorkflow(id: string, storyId?: string): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/${id}/execute`, { story_id: storyId });
  }

  createWorkflow(workflowData: any): Observable<any> {
    return this.http.post<any>(this.apiUrl, workflowData);
  }

  createWorkflowFromJira(storyId: string): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/from-jira/${storyId}`, {});
  }
}
