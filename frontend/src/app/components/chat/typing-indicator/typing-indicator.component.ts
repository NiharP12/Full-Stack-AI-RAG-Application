import { Component } from '@angular/core';

@Component({
  selector: 'app-typing-indicator',
  standalone: true,
  template: `
    <div class="typing-indicator">
      <div class="typing-avatar">
        <span class="material-icons">auto_awesome</span>
      </div>
      <div class="dots">
        <div class="dot"></div>
        <div class="dot"></div>
        <div class="dot"></div>
      </div>
    </div>
  `,
  styles: [`
    .typing-indicator {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 8px 0;
    }

    .typing-avatar {
      width: 36px;
      height: 36px;
      border-radius: 10px;
      background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
    }

    .typing-avatar .material-icons {
      font-size: 20px;
      color: #ffffff;
    }

    .dots {
      display: flex;
      align-items: center;
      gap: 5px;
      padding: 12px 16px;
      background: var(--bg-tertiary);
      border-radius: 16px;
      border: 1px solid var(--border-color);
    }

    .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--accent-color);
      animation: bounce 1.4s infinite ease-in-out both;
      opacity: 0.6;
    }

    .dot:nth-child(1) { animation-delay: -0.32s; }
    .dot:nth-child(2) { animation-delay: -0.16s; }

    @keyframes bounce {
      0%, 80%, 100% { transform: scale(0.5); opacity: 0.3; }
      40% { transform: scale(1); opacity: 1; }
    }
  `]
})
export class TypingIndicatorComponent {}
