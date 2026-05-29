import { Pipe, PipeTransform } from '@angular/core';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

@Pipe({
  name: 'markdown',
  standalone: true
})
export class MarkdownPipe implements PipeTransform {
  transform(value: string | undefined): string {
    if (!value) {
      return '';
    }

    // Convert markdown to HTML
    const html = marked.parse(value, { async: false }) as string;
    
    // Sanitize HTML to prevent XSS
    return DOMPurify.sanitize(html);
  }
}
