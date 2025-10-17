import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ConversationReviewRequest {
  workflow_id: number;
}

export interface ConversationReviewResponse {
  summary: string;
  workflow_recommendations: Array<{
    title: string;
    description: string;
  }>;
  prompt_recommendations: Array<{
    agent: string;
    current_issue: string;
    suggestion: string;
  }>;
  code_change_suggestions: Array<{
    path: string;
    section: string;
    change_type: 'edit' | 'add' | 'remove';
    before_summary: string;
    after_summary: string;
    patch_outline: string;
  }>;
  risk_flags: string[];
  quick_wins: string[];
  estimated_savings: {
    messages: number;
    cost_usd: number;
    duration_minutes: number;
  };
}

@Injectable({
  providedIn: 'root'
})
export class ConversationReviewService {
  private apiUrl = '/api/workflows';

  constructor(private http: HttpClient) {}

  /**
   * Trigger a conversation review for a workflow
   */
  triggerReview(workflowId: number): Observable<ConversationReviewResponse> {
    return this.http.post<ConversationReviewResponse>(
      `${this.apiUrl}/workflows/${workflowId}/conversation-review`,
      { workflow_id: workflowId }
    );
  }

  /**
   * Get existing conversation review results
   */
  getReview(workflowId: number): Observable<ConversationReviewResponse> {
    return this.http.get<ConversationReviewResponse>(
      `${this.apiUrl}/workflows/${workflowId}/conversation-review`
    );
  }
}
