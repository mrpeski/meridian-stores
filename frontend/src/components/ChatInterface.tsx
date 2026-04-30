import { useChat } from "../hooks/useChat";
import { ChatInput } from "./ChatInput";
import { MessageList } from "./MessageList";
import { TypingIndicator } from "./TypingIndicator";

export function ChatInterface() {
  const { messages, isLoading, error, sendMessage, clearConversation } = useChat();

  return (
    <div
      style={{
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        backgroundColor: "#18181b",
        color: "#e4e4e7",
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <div
        style={{
          padding: "1rem",
          borderBottom: "1px solid #3f3f46",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <h1 style={{ fontSize: "1.25rem", fontWeight: 600, margin: 0 }}>Meridian Electronics Support</h1>
        <button
          type="button"
          onClick={clearConversation}
          style={{
            padding: "0.5rem 1rem",
            borderRadius: "0.375rem",
            border: "1px solid #3f3f46",
            backgroundColor: "transparent",
            color: "#a1a1aa",
            fontSize: "0.875rem",
            cursor: "pointer",
          }}
        >
          Clear
        </button>
      </div>

      {error !== null ? (
        <div
          role="alert"
          style={{
            padding: "0.75rem 1rem",
            backgroundColor: "#7f1d1d",
            color: "#fca5a5",
            fontSize: "0.875rem",
            borderBottom: "1px solid #991b1b",
          }}
        >
          {error}
        </div>
      ) : null}

      <MessageList messages={messages} />
      {isLoading ? <TypingIndicator /> : null}
      <ChatInput onSend={sendMessage} disabled={isLoading} />
    </div>
  );
}
