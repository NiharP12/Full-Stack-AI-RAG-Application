import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ChatService } from '../../services/chat.service';
import { ChatSession } from '../../models/chat.model';
import { FileUploadComponent } from '../file-upload/file-upload.component';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatButtonModule, MatTooltipModule, FileUploadComponent],
  templateUrl: './sidebar.component.html',
  styleUrl: './sidebar.component.css'
})
export class SidebarComponent implements OnInit {
  sessions: ChatSession[] = [];
  currentSessionId: string | null = null;

  constructor(private chatService: ChatService) {}

  ngOnInit() {
    this.loadSessions();
    // In a real app we'd poll or use SSE to update sessions list,
    // for now we'll just check periodically or rely on manual refresh
    setInterval(() => {
      this.currentSessionId = this.chatService.getCurrentSessionId();
    }, 1000);
  }

  loadSessions() {
    this.chatService.getHistory().subscribe({
      next: (res) => {
        this.sessions = res.sessions;
      },
      error: (err) => console.error('Failed to load sessions', err)
    });
  }

  startNewChat() {
    this.chatService.setCurrentSessionId(null);
    this.currentSessionId = null;
    // Dispatch event or subject to tell chat component to clear
    window.dispatchEvent(new CustomEvent('new-chat'));
  }

  selectSession(sessionId: string) {
    this.chatService.setCurrentSessionId(sessionId);
    this.currentSessionId = sessionId;
    window.dispatchEvent(new CustomEvent('load-session', { detail: sessionId }));
  }

  deleteSession(event: Event, sessionId: string) {
    event.stopPropagation();
    this.chatService.deleteSession(sessionId).subscribe({
      next: () => {
        this.sessions = this.sessions.filter(s => s.session_id !== sessionId);
        if (this.currentSessionId === sessionId) {
          this.startNewChat();
        }
      },
      error: (err) => console.error('Failed to delete session', err)
    });
  }
}
