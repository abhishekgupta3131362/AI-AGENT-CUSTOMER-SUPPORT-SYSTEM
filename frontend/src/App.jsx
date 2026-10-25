import React, { useState } from "react";
import { ChatWidget } from "./components/ChatWidget";
import { AdminDashboard } from "./components/AdminDashboard";

export default function App() {
  const [view, setView] = useState("chat");
  const [sessionId] = useState(() => "react_sess_" + Math.random().toString(36).substring(2, 9));

  return (
    <div>
      <header className="navbar">
        <div className="brand">
          <div className="brand-icon">⚡</div>
          <span>ApexTech Support AI</span>
        </div>
        <div className="nav-tabs">
          <button
            className={`nav-tab ${view === "chat" ? "active" : ""}`}
            onClick={() => setView("chat")}
          >
            💬 Customer Chat
          </button>
          <button
            className={`nav-tab ${view === "admin" ? "active" : ""}`}
            onClick={() => setView("admin")}
          >
            📊 Admin CRM
          </button>
        </div>
      </header>

      <main className="container">
        {view === "chat" ? <ChatWidget sessionId={sessionId} /> : <AdminDashboard />}
      </main>
    </div>
  );
}
