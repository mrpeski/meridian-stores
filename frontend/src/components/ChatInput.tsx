import { useEffect, useRef, useState, type KeyboardEvent } from "react";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSend(input);
      setInput("");
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div
      style={{
        padding: "1rem",
        borderTop: "1px solid #3f3f46",
        display: "flex",
        gap: "0.5rem",
      }}
    >
      <textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type your message..."
        disabled={disabled}
        rows={2}
        style={{
          flex: 1,
          padding: "0.75rem",
          borderRadius: "0.375rem",
          border: "1px solid #3f3f46",
          backgroundColor: "#18181b",
          color: "#e4e4e7",
          fontSize: "0.875rem",
          resize: "none",
          fontFamily: "inherit",
        }}
      />
      <button
        type="button"
        onClick={handleSend}
        disabled={disabled || !input.trim()}
        style={{
          padding: "0.75rem 1.5rem",
          borderRadius: "0.375rem",
          border: "none",
          backgroundColor: disabled || !input.trim() ? "#3f3f46" : "#3b82f6",
          color: "#ffffff",
          fontSize: "0.875rem",
          fontWeight: 500,
          cursor: disabled || !input.trim() ? "not-allowed" : "pointer",
        }}
      >
        Send
      </button>
    </div>
  );
}
