import { useLayoutEffect, useRef } from "react";
import { useState } from "react";
import ChatHeader from "./components/ChatHeader";
import ChatMessage from "./components/ChatMessage";
import ChatInput from "./components/ChatInput";
import "./index.css";

const API_URL = "https://84f1uy22v5.execute-api.us-east-1.amazonaws.com/Prod/hello/";
const API_KEY = import.meta.env.VITE_API_KEY;

export default function App() {
  const chatWindowRef = useRef(null);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Hi! Ask me a technical question. I’ll use the knowledge base (RAG) when relevant."
    }
  ]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  //Adding for Scroll anchor
  useLayoutEffect(() => {
  const el = chatWindowRef.current;
  if (!el) return;

  el.scrollTop = el.scrollHeight;
  }, [messages]);

  const resetChat = () => {
    setMessages([
      {
        role: "assistant",
        text: "Hi! Ask me a technical question. I’ll use the knowledge base (RAG) when relevant."
      }
    ]);
  };

  const sendMessage = async () => {
  if (!input.trim() || loading) return;

  const userMessage = { role: "user", text: input };
  const thinkingMessage = {
    role: "assistant",
    text: "Thinking... retrieving relevant context",
    loading: true
  };

  setMessages((prev) => [...prev, userMessage, thinkingMessage]);
  setInput("");
  setLoading(true);

  try {
    const start = performance.now();

    const res = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
      },
      body: JSON.stringify({ prompt: input })
    });

    const data = await res.json();
    const latency = Math.round(performance.now() - start);

    setMessages((prev) => {
      const withoutThinking = prev.slice(0, -1);
      return [
        ...withoutThinking,
        {
          role: "assistant",
          text: data.response || "No response received.",
          latency,
          sources: data.sources || []
        }
      ];
    });
  } catch (err) {
    setMessages((prev) => {
      const withoutThinking = prev.slice(0, -1);
      return [
        ...withoutThinking,
        {
          role: "assistant",
          text:
            "Something went wrong on the Server. Please try again in a moment."
        }
      ];
    });
  } finally {
    setLoading(false);
  }
};


  return (
    <div className="app-container">
      <ChatHeader onReset={resetChat} />

      <div className="chat-window" ref={chatWindowRef}>
        {messages.map((msg, idx) => (
          <ChatMessage
            key={idx}
            role={msg.role}
            text={msg.text}
            latency={msg.latency}
            loading={msg.loading}
            sources={msg.sources}
          />
        ))}
      </div>

      <ChatInput
        value={input}
        onChange={setInput}
        onSend={sendMessage}
        loading={loading}
      />
    </div>
  );
}
