import { useRef, useEffect } from "react";

export default function ChatInput({
  value,
  onChange,
  onSend,
  loading
}) {
    const textareaRef = useRef(null);

    useEffect(() => {
    if (!textareaRef.current) return;
    textareaRef.current.style.height = "auto";
    textareaRef.current.style.height =
        textareaRef.current.scrollHeight + "px";
    }, [value]);
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div className="chat-input">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            onSend();
            }
        }}
        disabled={loading}
        placeholder="Ask a technical question..."
    />

      <button onClick={onSend} disabled={loading || !value.trim()}>
        {loading ? "Thinking..." : "Send"}
      </button>
    </div>
  );
}
