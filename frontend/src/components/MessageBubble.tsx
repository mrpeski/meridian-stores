import type { Message } from "../types/chat";

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        marginBottom: "1rem",
      }}
    >
      <div
        style={{
          maxWidth: "70%",
          padding: "0.75rem 1rem",
          borderRadius: "0.5rem",
          backgroundColor: isUser ? "#3b82f6" : "#27272a",
          color: "#ffffff",
          wordWrap: "break-word",
        }}
      >
        <div style={{ fontSize: "0.875rem", whiteSpace: "pre-wrap" }}>{message.content}</div>
      </div>
    </div>
  );
}
