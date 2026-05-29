import { Injectable } from '@angular/core';
import { HttpClient, HttpEvent, HttpEventType } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import { DocumentListResponse, UploadResponse } from '../models/document.model';

@Injectable({
  providedIn: 'root'
})
export class UploadService {
  private apiUrl = `${environment.apiUrl}/api`;

  constructor(private http: HttpClient) {}

  uploadFiles(files: File[]): Observable<HttpEvent<UploadResponse>> {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file, file.name);
    });

    return this.http.post<UploadResponse>(`${this.apiUrl}/upload`, formData, {
      reportProgress: true,
      observe: 'events'
    });
  }

  getDocuments(): Observable<DocumentListResponse> {
    return this.http.get<DocumentListResponse>(`${this.apiUrl}/documents`);
  }

  deleteDocument(filename: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/documents?filename=${encodeURIComponent(filename)}`);
  }

  deleteAllDocuments(): Observable<any> {
    return this.http.delete(`${this.apiUrl}/documents`);
  }
}
