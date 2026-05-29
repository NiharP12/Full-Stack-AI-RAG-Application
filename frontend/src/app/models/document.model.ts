export interface DocumentInfo {
  filename: string;
  file_type: string;
  file_size: number;
  upload_time: string;
  chunk_count: number;
  status: 'processing' | 'processed' | 'failed';
}

export interface DocumentListResponse {
  documents: DocumentInfo[];
  total_count: number;
}

export interface UploadResponse {
  message: string;
  uploaded_files: string[];
  failed_files: { filename: string; error: string }[];
  total_chunks: number;
}

export interface FileUploadItem {
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'success' | 'error';
  errorMessage?: string;
}
