export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  customer_id?: string;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  metadata?: Record<string, unknown>;
}

export interface ErrorResponse {
  error: {
    code: string;
    message: string;
  };
}
