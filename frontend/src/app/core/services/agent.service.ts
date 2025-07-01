import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AgentService {
  private apiUrl = '/api/agents';

  constructor(private http: HttpClient) {}

  getAgents(): Observable<any[]> {
    return this.http.get<any[]>(this.apiUrl);
  }

  addAgent(agent: any): Observable<any> {
    return this.http.post<any>(this.apiUrl, agent);
  }

  deleteAgent(id: string): Observable<any> {
    return this.http.delete<any>(`${this.apiUrl}/${id}`);
  }

  getAgent(id: string): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/${id}`);
  }
}
