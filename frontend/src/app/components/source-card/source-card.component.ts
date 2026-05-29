import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { SourceDocument } from '../../models/chat.model';

@Component({
  selector: 'app-source-card',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  templateUrl: './source-card.component.html',
  styleUrl: './source-card.component.css'
})
export class SourceCardComponent {
  @Input() source!: SourceDocument;
  @Input() index!: number;
  
  isExpanded = false;

  toggleExpand() {
    this.isExpanded = !this.isExpanded;
  }
}
