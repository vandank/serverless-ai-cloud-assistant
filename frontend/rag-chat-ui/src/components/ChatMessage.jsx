import { useEffect, useState } from "react";

export default function ChatMessage({ role, text, latency, loading, sources }) {
  const [dots, setDots] = useState("");

  // Animate "Thinking..." dots
  useEffect(() => {
    if (!loading) return;

    const interval = setInterval(() => {
      setDots((prev) => (prev.length >= 3 ? "" : prev + "."));
    }, 500);

    return () => clearInterval(interval);
  }, [loading]);

  return (
    <div className={`message-row ${role}`}>
      <div className="message-bubble">
        {loading ? (
          <span>
            Thinking{dots}
            <span className="spinner" />
          </span>
        ) : (
          text
        )}
        {sources && sources.length > 0 && (
          <div className="sources">
            <strong>Sources:</strong>
            <ul>
              {sources.map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ul>
          </div>
        )}
        {latency && !loading && (
          <span className="latency">{latency} ms</span>
        )}
      </div>
    </div>
  );
}
