export interface SourceDocument {
  content: string;
  source: string;
  page?: number;
  score?: number;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  sources?: SourceDocument[];
}

export interface ChatSession {
  session_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
}

export interface ChatRequest {
  question: string;
  session_id?: string;
  top_k?: number;
}

export interface ChatResponse {
  answer: string;
  sources: SourceDocument[];
  session_id: string;
  tokens_used?: number;
}
