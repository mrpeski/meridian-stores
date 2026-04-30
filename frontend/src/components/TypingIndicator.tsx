export function TypingIndicator() {
  return (
    <div style={{ padding: "0 1rem 1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
      <div
        style={{
          padding: "0.75rem 1rem",
          borderRadius: "0.5rem",
          backgroundColor: "#27272a",
          color: "#a1a1aa",
          fontSize: "0.875rem",
        }}
      >
        <span>Bot is typing</span>
        <span className="typing-dots">...</span>
      </div>
    </div>
  );
}
