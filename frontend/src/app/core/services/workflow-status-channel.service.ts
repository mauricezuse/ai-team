import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, Subject, BehaviorSubject, timer, throwError, of } from 'rxjs';
import { retry, catchError, switchMap, takeUntil, tap, debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { 
  WorkflowStatusInfo, 
  WorkflowStatusUpdate, 
  ConnectionType, 
  StatusChannelConfig 
} from '../models/workflow-status.model';

@Injectable({
  providedIn: 'root'
})
export class WorkflowStatusChannelService {
  private apiUrl = '/api';
  private wsUrl = 'ws://localhost:8000/ws';
  private sseUrl = '/api/events';
  private streamUrl = '/api/events';
  
  private statusSubjects: Map<number, BehaviorSubject<WorkflowStatusInfo>> = new Map();
  private connectionTypes: Map<number, ConnectionType> = new Map();
  private stopSubjects: Map<number, Subject<void>> = new Map();
  private retryCounts: Map<number, number> = new Map();
  private backoffTimers: Map<number, number> = new Map();

  constructor(private http: HttpClient) {}

  /**
   * Get a status stream for a workflow with automatic fallback
   */
  getStatusStream(workflowId: number): Observable<WorkflowStatusInfo> {
    // Return existing stream if available
    if (this.statusSubjects.has(workflowId)) {
      return this.statusSubjects.get(workflowId)!.asObservable();
    }

    // Create new status subject
    const statusSubject = new BehaviorSubject<WorkflowStatusInfo>({
      workflow_id: workflowId,
      status: 'unknown',
      isTerminal: false,
      heartbeat_stale: false,
      message: 'Connecting...'
    });
    this.statusSubjects.set(workflowId, statusSubject);

    // Start connection with fallback
    this.startConnection(workflowId);

    return statusSubject.asObservable().pipe(
      debounceTime(100), // Debounce rapid updates
      distinctUntilChanged((prev, curr) => 
        prev.status === curr.status && 
        prev.isTerminal === curr.isTerminal &&
        prev.heartbeat_stale === curr.heartbeat_stale
      )
    );
  }

  /**
   * Start connection with fallback: WebSocket -> SSE -> Polling
   */
  private startConnection(workflowId: number): void {
    const config: StatusChannelConfig = {
      workflowId,
      connectionType: ConnectionType.WEBSOCKET,
      retryCount: 0,
      maxRetries: 3,
      backoffMs: 1000,
      maxBackoffMs: 30000
    };

    this.attemptConnection(config);
  }

  private attemptConnection(config: StatusChannelConfig): void {
    const { workflowId, connectionType, retryCount, backoffMs } = config;
    
    // Stop any existing connection
    this.stopConnection(workflowId);

    // Create stop subject for this connection
    const stopSubject = new Subject<void>();
    this.stopSubjects.set(workflowId, stopSubject);

    switch (connectionType) {
      case ConnectionType.WEBSOCKET:
        this.connectWebSocket(workflowId, stopSubject, config);
        break;
      case ConnectionType.SSE:
        this.connectSSE(workflowId, stopSubject, config);
        break;
      case ConnectionType.POLLING:
        this.connectPolling(workflowId, stopSubject, config);
        break;
    }
  }

  private connectWebSocket(workflowId: number, stopSubject: Subject<void>, config: StatusChannelConfig): void {
    try {
      const ws = new WebSocket(`${this.wsUrl}/workflows/${workflowId}`);
      this.connectionTypes.set(workflowId, ConnectionType.WEBSOCKET);

      ws.onopen = () => {
        console.log(`[WorkflowStatusChannel] WebSocket connected for workflow ${workflowId}`);
        this.retryCounts.set(workflowId, 0);
      };

      ws.onmessage = (event) => {
        try {
          const statusInfo: WorkflowStatusInfo = JSON.parse(event.data);
          // Add connection type to status info
          const enhancedStatusInfo = {
            ...statusInfo,
            connectionType: 'websocket'
          };
          this.updateStatus(workflowId, enhancedStatusInfo);
          
          // If terminal, stop connection
          if (statusInfo.isTerminal) {
            this.stopConnection(workflowId);
          }
        } catch (error) {
          console.error(`[WorkflowStatusChannel] WebSocket message error:`, error);
        }
      };

      ws.onclose = () => {
        console.log(`[WorkflowStatusChannel] WebSocket closed for workflow ${workflowId}`);
        this.handleConnectionClose(workflowId, config);
      };

      ws.onerror = (error) => {
        console.error(`[WorkflowStatusChannel] WebSocket error:`, error);
        this.handleConnectionError(workflowId, config);
      };

      // Store WebSocket for cleanup
      (ws as any).__workflowId = workflowId;
      
    } catch (error) {
      console.error(`[WorkflowStatusChannel] WebSocket connection failed:`, error);
      this.handleConnectionError(workflowId, config);
    }
  }

  private connectSSE(workflowId: number, stopSubject: Subject<void>, config: StatusChannelConfig): void {
    try {
      const eventSource = new EventSource(`${this.sseUrl}/workflows/${workflowId}`);
      this.connectionTypes.set(workflowId, ConnectionType.SSE);

      eventSource.onopen = () => {
        console.log(`[WorkflowStatusChannel] SSE connected for workflow ${workflowId}`);
        this.retryCounts.set(workflowId, 0);
      };

      eventSource.onmessage = (event) => {
        try {
          const statusInfo: WorkflowStatusInfo = JSON.parse(event.data);
          // Add connection type to status info
          const enhancedStatusInfo = {
            ...statusInfo,
            connectionType: 'sse'
          };
          this.updateStatus(workflowId, enhancedStatusInfo);
          
          // If terminal, stop connection
          if (statusInfo.isTerminal) {
            this.stopConnection(workflowId);
          }
        } catch (error) {
          console.error(`[WorkflowStatusChannel] SSE message error:`, error);
        }
      };

      eventSource.onerror = (error) => {
        console.error(`[WorkflowStatusChannel] SSE error:`, error);
        this.handleConnectionError(workflowId, config);
      };

      // Store EventSource for cleanup
      (eventSource as any).__workflowId = workflowId;
      
    } catch (error) {
      console.error(`[WorkflowStatusChannel] SSE connection failed:`, error);
      this.handleConnectionError(workflowId, config);
    }
  }

  /**
   * Connect to real-time event stream (logs + conversation events)
   */
  connectEventStream(workflowId: number, onEvent: (evt: any) => void): { close: () => void } {
    const source = new EventSource(`${this.streamUrl}/workflows/${workflowId}/stream`);
    source.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        onEvent(data);
      } catch (e) {
        console.error('[WorkflowStatusChannel] stream parse error', e);
      }
    };
    source.onerror = (err) => {
      console.error('[WorkflowStatusChannel] stream error', err);
    };
    return { close: () => source.close() };
  }

  private connectPolling(workflowId: number, stopSubject: Subject<void>, config: StatusChannelConfig): void {
    console.log(`[WorkflowStatusChannel] Starting polling for workflow ${workflowId}`);
    this.connectionTypes.set(workflowId, ConnectionType.POLLING);

    // Start with immediate request, then poll every 5 seconds
    timer(0, 5000).pipe(
      takeUntil(stopSubject),
      switchMap(() => this.getWorkflowStatus(workflowId)),
      tap(statusInfo => {
        // Add connection type to status info
        const enhancedStatusInfo = {
          ...statusInfo,
          connectionType: 'polling'
        };
        this.updateStatus(workflowId, enhancedStatusInfo);
        
        // If terminal, stop polling
        if (statusInfo.isTerminal) {
          this.stopConnection(workflowId);
        }
      }),
      catchError(error => {
        console.error(`[WorkflowStatusChannel] Polling error:`, error);
        this.handleConnectionError(workflowId, config);
        return of(null);
      })
    ).subscribe();
  }

  private getWorkflowStatus(workflowId: number): Observable<WorkflowStatusInfo> {
    return this.http.get<WorkflowStatusInfo>(`${this.apiUrl}/workflows/${workflowId}/status`);
  }

  private updateStatus(workflowId: number, statusInfo: WorkflowStatusInfo): void {
    const subject = this.statusSubjects.get(workflowId);
    if (subject) {
      subject.next(statusInfo);
    }
  }

  private handleConnectionClose(workflowId: number, config: StatusChannelConfig): void {
    // If not terminal, try next connection type
    const currentStatus = this.statusSubjects.get(workflowId)?.value;
    if (!currentStatus?.isTerminal) {
      this.fallbackToNextConnection(workflowId, config);
    }
  }

  private handleConnectionError(workflowId: number, config: StatusChannelConfig): void {
    this.fallbackToNextConnection(workflowId, config);
  }

  private fallbackToNextConnection(workflowId: number, config: StatusChannelConfig): void {
    const retryCount = this.retryCounts.get(workflowId) || 0;
    
    if (retryCount >= config.maxRetries) {
      console.error(`[WorkflowStatusChannel] Max retries reached for workflow ${workflowId}`);
      return;
    }

    // Increment retry count
    this.retryCounts.set(workflowId, retryCount + 1);

    // Determine next connection type
    let nextConnectionType: ConnectionType;
    switch (config.connectionType) {
      case ConnectionType.WEBSOCKET:
        nextConnectionType = ConnectionType.SSE;
        break;
      case ConnectionType.SSE:
        nextConnectionType = ConnectionType.POLLING;
        break;
      case ConnectionType.POLLING:
        // Already at polling, just retry with backoff
        nextConnectionType = ConnectionType.POLLING;
        break;
    }

    // Calculate backoff delay
    const backoffMs = Math.min(config.backoffMs * Math.pow(2, retryCount), config.maxBackoffMs);
    
    console.log(`[WorkflowStatusChannel] Retrying workflow ${workflowId} with ${nextConnectionType} in ${backoffMs}ms`);
    
    // Schedule retry
    setTimeout(() => {
      this.attemptConnection({
        ...config,
        connectionType: nextConnectionType,
        retryCount: retryCount + 1,
        backoffMs: backoffMs
      });
    }, backoffMs);
  }

  /**
   * Stop connection for a workflow
   */
  stopConnection(workflowId: number): void {
    const stopSubject = this.stopSubjects.get(workflowId);
    if (stopSubject) {
      stopSubject.next();
      stopSubject.complete();
      this.stopSubjects.delete(workflowId);
    }

    // Clean up WebSocket connections
    // Note: In a real implementation, you'd need to track and close WebSocket/SSE connections
    
    this.connectionTypes.delete(workflowId);
    this.retryCounts.delete(workflowId);
    
    console.log(`[WorkflowStatusChannel] Stopped connection for workflow ${workflowId}`);
  }

  /**
   * Get current connection type for a workflow
   */
  getConnectionType(workflowId: number): ConnectionType | undefined {
    return this.connectionTypes.get(workflowId);
  }

  /**
   * Manually reconcile workflow status
   */
  reconcileWorkflowStatus(workflowId: number): Observable<any> {
    return this.http.post(`${this.apiUrl}/workflows/${workflowId}/reconcile`, {});
  }

  /**
   * Clean up all connections
   */
  cleanup(): void {
    for (const workflowId of this.statusSubjects.keys()) {
      this.stopConnection(workflowId);
    }
    this.statusSubjects.clear();
  }
}
