import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';
import { UploadService } from '../../services/upload.service';
import { FileUploadItem } from '../../models/document.model';
import { HttpEventType } from '@angular/common/http';

@Component({
  selector: 'app-file-upload',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatProgressBarModule, MatButtonModule, MatTooltipModule],
  templateUrl: './file-upload.component.html',
  styleUrl: './file-upload.component.css'
})
export class FileUploadComponent implements OnInit {
  isDragging = false;
  uploadQueue: FileUploadItem[] = [];
  documents: any[] = [];
  allowedTypes = ['.pdf', '.txt', '.docx', '.doc', '.csv', '.xlsx'];
  maxSizeMB = 50;

  constructor(private uploadService: UploadService) {}

  ngOnInit() {
    this.loadDocuments();
  }

  loadDocuments() {
    this.uploadService.getDocuments().subscribe({
      next: (res) => {
        this.documents = res.documents;
      },
      error: (err) => console.error('Failed to load docs', err)
    });
  }

  onDragOver(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = true;
  }

  onDragLeave(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;
    
    if (event.dataTransfer?.files) {
      this.handleFiles(Array.from(event.dataTransfer.files));
    }
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files) {
      this.handleFiles(Array.from(input.files));
    }
    input.value = ''; // Reset input
  }

  handleFiles(files: File[]) {
    // Validate files
    const validFiles = files.filter(file => this.validateFile(file));
    
    if (validFiles.length > 0) {
      this.uploadService.uploadFiles(validFiles).subscribe({
        next: (event: any) => {
          if (event.type === HttpEventType.UploadProgress && event.total) {
            // Optional: track progress for UI
          } else if (event.type === HttpEventType.Response) {
            // Success
            this.loadDocuments(); // Refresh list
          }
        },
        error: (err) => {
          console.error('Upload failed', err);
          alert('Upload failed. Please check the server logs.');
        }
      });
    }
  }

  validateFile(file: File): boolean {
    // Check size
    if (file.size > this.maxSizeMB * 1024 * 1024) {
      alert(`File ${file.name} is too large. Max size is ${this.maxSizeMB}MB.`);
      return false;
    }
    
    // Check extension
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!this.allowedTypes.includes(ext)) {
      alert(`File type ${ext} not supported.`);
      return false;
    }
    
    return true;
  }

  deleteDocument(filename: string) {
    if (confirm(`Are you sure you want to delete ${filename}?`)) {
      this.uploadService.deleteDocument(filename).subscribe({
        next: () => this.loadDocuments(),
        error: (err) => console.error('Failed to delete doc', err)
      });
    }
  }

  getFileIcon(filename: string): string {
    const ext = filename.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'pdf': return 'picture_as_pdf';
      case 'txt': return 'description';
      case 'docx':
      case 'doc': return 'article';
      case 'csv':
      case 'xlsx': return 'table_view';
      default: return 'insert_drive_file';
    }
  }
}
