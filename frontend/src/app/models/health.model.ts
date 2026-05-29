export interface HealthResponse {
  status: string;
  version: string;
  llm_provider: string;
  vector_store: string;
  documents_count: number;
  uptime_seconds: number;
}
