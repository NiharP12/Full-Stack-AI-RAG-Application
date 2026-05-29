import { Component, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { ChatService } from '../../services/chat.service';
import { ChatMessage } from '../../models/chat.model';
import { MessageBubbleComponent } from './message-bubble/message-bubble.component';
import { TypingIndicatorComponent } from './typing-indicator/typing-indicator.component';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule, MatIconModule, MatButtonModule, MessageBubbleComponent, TypingIndicatorComponent],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.css'
})
export class ChatComponent implements OnInit, OnDestroy, AfterViewChecked {
  @ViewChild('messagesContainer') private messagesContainer!: ElementRef;
  @ViewChild('chatInput') private chatInput!: ElementRef;

  messages: ChatMessage[] = [];
  currentInput: string = '';
  isWaitingForResponse: boolean = false;
  isStreaming: boolean = false;
  
  private streamSubscription?: Subscription;
  private autoScroll = true;

  constructor(private chatService: ChatService) {}

  ngOnInit() {
    // Listen for new chat events from sidebar
    window.addEventListener('new-chat', () => {
      this.messages = [];
      this.currentInput = '';
      this.focusInput();
    });

    // Listen for session load events from sidebar
    window.addEventListener('load-session', (e: any) => {
      const sessionId = e.detail;
      this.loadSession(sessionId);
    });

    // If there is an active session, load it
    const activeSession = this.chatService.getCurrentSessionId();
    if (activeSession) {
      this.loadSession(activeSession);
    }
  }

  ngOnDestroy() {
    this.streamSubscription?.unsubscribe();
  }

  ngAfterViewChecked() {
    if (this.autoScroll) {
      this.scrollToBottom();
    }
  }

  loadSession(sessionId: string) {
    this.chatService.getHistory(sessionId).subscribe({
      next: (res) => {
        if (res.sessions && res.sessions.length > 0) {
          this.messages = res.sessions[0].messages;
          this.autoScroll = true;
          setTimeout(() => this.scrollToBottom(), 100);
        }
      },
      error: (err) => console.error('Failed to load session', err)
    });
  }

  sendMessage() {
    const text = this.currentInput.trim();
    if (!text || this.isWaitingForResponse) return;

    // Add user message
    this.messages.push({
      role: 'user',
      content: text
    });

    this.currentInput = '';
    this.isWaitingForResponse = true;
    this.autoScroll = true;

    // Add empty assistant message placeholder for streaming
    this.messages.push({
      role: 'assistant',
      content: ''
    });

    const assistantMsgIndex = this.messages.length - 1;

    this.streamSubscription = this.chatService.streamChat(text).subscribe({
      next: (event: any) => {
        this.isWaitingForResponse = false; // We started getting a response
        this.isStreaming = true;

        if (event.type === 'token') {
          this.messages[assistantMsgIndex].content += event.content;
        } else if (event.type === 'sources') {
          this.messages[assistantMsgIndex].sources = event.sources;
        } else if (event.type === 'done') {
          this.isStreaming = false;
        } else if (event.type === 'error') {
          this.isStreaming = false;
          this.messages[assistantMsgIndex].content += `\n\n**Error:** ${event.content}`;
        }
      },
      error: (err) => {
        console.error('Chat error', err);
        this.isWaitingForResponse = false;
        this.isStreaming = false;
        this.messages[assistantMsgIndex].content = "**Error:** Could not connect to the server.";
      }
    });
  }

  handleKeyDown(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  stopStreaming() {
    if (this.streamSubscription) {
      this.streamSubscription.unsubscribe();
      this.isStreaming = false;
      this.isWaitingForResponse = false;
    }
  }

  onScroll() {
    const element = this.messagesContainer.nativeElement;
    const atBottom = element.scrollHeight - element.scrollTop <= element.clientHeight + 50;
    this.autoScroll = atBottom;
  }

  private scrollToBottom(): void {
    try {
      const element = this.messagesContainer.nativeElement;
      element.scrollTop = element.scrollHeight;
    } catch(err) { }
  }

  private focusInput(): void {
    setTimeout(() => {
      try {
        this.chatInput.nativeElement.focus();
      } catch (err) {}
    }, 100);
  }
}
