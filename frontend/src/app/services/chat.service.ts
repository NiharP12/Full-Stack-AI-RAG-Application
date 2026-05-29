import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject } from 'rxjs';
import { environment } from '../../environments/environment';
import { ChatMessage, ChatSession } from '../models/chat.model';

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private apiUrl = `${environment.apiUrl}/api`;
  private currentSessionId: string | null = null;
  private messageStream = new Subject<{ type: string; content?: string; sources?: any[]; session_id?: string; error?: string }>();

  constructor(private http: HttpClient) {}

  // ------------------------------------------------------------------
  // Chat Operations
  // ------------------------------------------------------------------

  getCurrentSessionId(): string | null {
    return this.currentSessionId;
  }

  setCurrentSessionId(id: string | null) {
    this.currentSessionId = id;
  }

  getHistory(sessionId?: string): Observable<{ sessions: ChatSession[] }> {
    const url = sessionId ? `${this.apiUrl}/history?session_id=${sessionId}` : `${this.apiUrl}/history`;
    return this.http.get<{ sessions: ChatSession[] }>(url);
  }

  deleteSession(sessionId: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/history?session_id=${sessionId}`);
  }

  deleteAllHistory(): Observable<any> {
    return this.http.delete(`${this.apiUrl}/history`);
  }

  // ------------------------------------------------------------------
  // Streaming Chat (SSE)
  // ------------------------------------------------------------------

  streamChat(question: string, sessionId?: string): Observable<any> {
    return new Observable(observer => {
      // Use Fetch API for streaming POST request since EventSource only supports GET
      const url = `${this.apiUrl}/chat`;
      const body = {
        question,
        session_id: sessionId || this.currentSessionId
      };

      fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream'
        },
        body: JSON.stringify(body)
      }).then(async response => {
        if (!response.ok || !response.body) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n\n');
          buffer = lines.pop() || ''; // Keep the incomplete line in the buffer

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.substring(6));
                
                // Track session ID
                if (data.type === 'done' && data.session_id) {
                  this.currentSessionId = data.session_id;
                }
                
                observer.next(data);
              } catch (e) {
                console.error('Error parsing SSE data:', e, line);
              }
            }
          }
        }
        observer.complete();
      }).catch(err => {
        observer.error(err);
      });
    });
  }
}
