import { useState } from "react";

import { apiUrl } from "../lib/apiBase";
import type { ChatRequest, ChatResponse, ErrorResponse, Message } from "../types/chat";

function parseErrorMessage(body: unknown, fallback: string): string {
  if (
    typeof body === "object" &&
    body !== null &&
    "error" in body &&
    typeof (body as { error?: { message?: unknown } }).error?.message === "string"
  ) {
    return (body as { error: { message: string } }).error.message;
  }
  return fallback;
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = async (text: string) => {
    if (!text.trim()) {
      return;
    }

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const request: ChatRequest = {
        message: text,
        conversation_id: conversationId,
      };

      const res = await fetch(apiUrl("/api/chat"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      });

      const body: unknown = await res.json().catch(() => ({}));

      if (!res.ok) {
        const errBody = body as ErrorResponse;
        const message =
          typeof errBody?.error?.message === "string"
            ? errBody.error.message
            : parseErrorMessage(body, res.statusText);
        throw new Error(message || "Failed to send message");
      }

      const data = body as ChatResponse;
      setConversationId(data.conversation_id);

      const botMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: data.response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  const clearConversation = () => {
    setMessages([]);
    setConversationId(undefined);
    setError(null);
  };

  return { messages, isLoading, error, sendMessage, clearConversation };
}
