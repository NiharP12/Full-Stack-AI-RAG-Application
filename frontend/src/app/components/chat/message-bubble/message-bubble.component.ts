import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { ChatMessage } from '../../../models/chat.model';
import { MarkdownPipe } from '../../../pipes/markdown.pipe';
import { SourceCardComponent } from '../../source-card/source-card.component';

@Component({
  selector: 'app-message-bubble',
  standalone: true,
  imports: [CommonModule, MatIconModule, MarkdownPipe, SourceCardComponent],
  templateUrl: './message-bubble.component.html',
  styleUrl: './message-bubble.component.css'
})
export class MessageBubbleComponent {
  @Input() message!: ChatMessage;
  @Input() isStreaming: boolean = false;
  
  get isUser(): boolean {
    return this.message.role === 'user';
  }
}
