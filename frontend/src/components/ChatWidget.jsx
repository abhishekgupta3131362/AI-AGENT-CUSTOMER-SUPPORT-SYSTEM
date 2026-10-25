import React, { useState, useEffect, useRef } from "react";

export function ChatWidget({ sessionId }) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Hello! Welcome to ApexTech Support. How can I assist you with orders, returns, or warranty claims today?"
    }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (messageText) => {
    const text = (messageText || input).trim();
    if (!text || isLoading) return;

    setInput("");
    setIsLoading(true);

    const userMsg = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, session_id: sessionId })
      });
      const data = await response.json();

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.response,
          thoughts: data.thoughts,
          toolCalls: data.tool_calls
        }
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error contacting support server: ${err.message}` }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-card">
      <div className="chat-header">
        <div className="chat-header-info">
          <div className="agent-avatar">AI</div>
          <div>
            <strong>Apex Support Specialist</strong>
            <p style={{ fontSize: "0.75rem", color: "#64748b" }}>Online &bull; ReAct Agent</p>
          </div>
        </div>
      </div>

      <div className="chat-messages">
        {messages.map((m, idx) => (
          <div key={idx} className={`message-row ${m.role}`}>
            {m.role === "assistant" && <div className="agent-avatar">AI</div>}
            <div className="msg-bubble">
              {m.thoughts && m.thoughts.length > 0 && (
                <div className="thought-box">
                  <strong>🧠 Reasoning:</strong> {m.thoughts.join(" ")}
                </div>
              )}
              {m.content}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message-row assistant">
            <div className="agent-avatar">AI</div>
            <div className="msg-bubble">
              <span className="typing-dot"></span>
              <span className="typing-dot"></span>
              <span className="typing-dot"></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="quick-prompts">
        <button className="quick-chip" onClick={() => handleSend("Where is order ORD-1002?")}>
          📦 Track ORD-1002
        </button>
        <button className="quick-chip" onClick={() => handleSend("What is your 30-day return policy?")}>
          🔄 Return Policy
        </button>
        <button className="quick-chip" onClick={() => handleSend("I want to speak with human agent")}>
          👤 Human Support
        </button>
      </div>

      <form
        className="chat-input-area"
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
      >
        <input
          type="text"
          className="chat-input"
          placeholder="Ask a question or enter order ID..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button type="submit" className="btn-send" disabled={isLoading}>
          Send
        </button>
      </form>
    </div>
  );
}
