import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

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

  getWorkflow(id: string): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/${id}`);
  }

  executeWorkflow(id: string, storyId?: string): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/${id}/execute`, { story_id: storyId });
  }
}
