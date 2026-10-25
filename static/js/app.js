// Application State
let sessionId = localStorage.getItem("apex_support_session_id") || "sess_" + Math.random().toString(36).substring(2, 10);
localStorage.setItem("apex_support_session_id", sessionId);

let isWaitingForResponse = false;
let currentSettings = null;

// Initialization
document.addEventListener("DOMContentLoaded", () => {
  loadSettings();
  loadTickets();
  loadKnowledge();
  loadOrders();
});

// View Navigation
function switchView(view) {
  document.getElementById("view-chat").classList.toggle("active", view === "chat");
  document.getElementById("view-admin").classList.toggle("active", view === "admin");
  document.getElementById("tab-chat").classList.toggle("active", view === "chat");
  document.getElementById("tab-admin").classList.toggle("active", view === "admin");

  if (view === "admin") {
    loadTickets();
  }
}

function switchAdminTab(tab) {
  document.querySelectorAll(".admin-subtab").forEach(b => b.classList.remove("active"));
  document.getElementById(`subtab-${tab}`).classList.add("active");

  document.getElementById("admin-content-tickets").style.display = tab === "tickets" ? "block" : "none";
  document.getElementById("admin-content-analytics").style.display = tab === "analytics" ? "block" : "none";
  document.getElementById("admin-content-knowledge").style.display = tab === "knowledge" ? "block" : "none";
  document.getElementById("admin-content-orders").style.display = tab === "orders" ? "block" : "none";

  if (tab === "tickets") loadTickets();
  if (tab === "analytics") loadAnalytics();
  if (tab === "knowledge") loadKnowledge();
  if (tab === "orders") loadOrders();
}

// Chat Functionality
function sendQuickPrompt(promptText) {
  const input = document.getElementById("chat-user-input");
  input.value = promptText;
  document.getElementById("chat-form").dispatchEvent(new Event("submit"));
}

async function handleSendMessage(event) {
  if (event) event.preventDefault();
  if (isWaitingForResponse) return;

  const input = document.getElementById("chat-user-input");
  const message = input.value.trim();
  if (!message) return;

  input.value = "";
  isWaitingForResponse = true;
  document.getElementById("btn-send-message").disabled = true;

  // Append user message
  appendMessage("user", message);

  // Create assistant placeholder container
  const assistantMsgId = "msg-" + Date.now();
  const assistantRow = document.createElement("div");
  assistantRow.className = "message-row assistant";
  assistantRow.id = assistantMsgId;
  assistantRow.innerHTML = `
    <div class="agent-avatar">AI</div>
    <div class="msg-bubble">
      <div class="thought-container" style="display: none;"></div>
      <div class="answer-content">
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
      </div>
    </div>
  `;
  const container = document.getElementById("chat-messages-container");
  container.appendChild(assistantRow);
  container.scrollTop = container.scrollHeight;

  const thoughtContainer = assistantRow.querySelector(".thought-container");
  const answerContent = assistantRow.querySelector(".answer-content");

  try {
    const response = await fetch("/api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId })
    });

    if (!response.ok) {
      throw new Error(`Server returned HTTP ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let accumulatedText = "";
    let isFirstAnswerToken = true;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split("\n");

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const rawData = line.replace("data: ", "").trim();
        if (rawData === "[DONE]") break;

        try {
          const event = JSON.parse(rawData);

          if (event.type === "sentiment") {
            updateSentimentBadge(event);
          } else if (event.type === "thought") {
            thoughtContainer.style.display = "block";
            const thoughtDiv = document.createElement("div");
            thoughtDiv.className = "thought-box";
            thoughtDiv.innerHTML = `<strong>🧠 Agent Thinking:</strong> ${escapeHtml(event.content)}`;
            thoughtContainer.appendChild(thoughtDiv);
          } else if (event.type === "tool_call") {
            thoughtContainer.style.display = "block";
            const toolDiv = document.createElement("div");
            toolDiv.className = "thought-box";
            toolDiv.style.borderLeft = "3px solid var(--accent)";
            toolDiv.innerHTML = `
              <strong>⚡ Action Tool:</strong> <span class="tool-chip">${escapeHtml(event.tool)}</span>
              <pre style="margin-top: 4px; font-size: 0.75rem; color: #64748b;">${JSON.stringify(event.input)}</pre>
            `;
            thoughtContainer.appendChild(toolDiv);
          } else if (event.type === "observation") {
            const obsDiv = document.createElement("div");
            obsDiv.className = "thought-box";
            obsDiv.style.borderLeft = "3px solid var(--success)";
            obsDiv.innerHTML = `<strong>👁️ Observation:</strong> <div style="margin-top: 4px; white-space: pre-wrap;">${escapeHtml(event.content)}</div>`;
            thoughtContainer.appendChild(obsDiv);
          } else if (event.type === "final_answer") {
            if (isFirstAnswerToken) {
              answerContent.innerHTML = "";
              isFirstAnswerToken = false;
            }
            accumulatedText = event.content;
            answerContent.innerHTML = escapeHtml(accumulatedText);
            
            // Show CSAT card after successful resolution
            setTimeout(() => {
              const csat = document.getElementById("csat-card");
              if (csat) csat.style.display = "block";
            }, 1000);
          }
        } catch (e) {
          // Non-JSON SSE line
        }
      }
      container.scrollTop = container.scrollHeight;
    }

    if (isFirstAnswerToken) {
      // Fallback if no final_answer event
      answerContent.innerHTML = accumulatedText || "Thank you. Let me know if you need anything else!";
    }

  } catch (err) {
    console.error("Chat streaming error:", err);
    answerContent.innerHTML = `<span style="color: var(--danger);">Error receiving response: ${err.message}. Please check connection or LLM settings.</span>`;
  } finally {
    isWaitingForResponse = false;
    document.getElementById("btn-send-message").disabled = false;
    container.scrollTop = container.scrollHeight;
  }
}

function appendMessage(role, text) {
  const container = document.getElementById("chat-messages-container");
  const row = document.createElement("div");
  row.className = `message-row ${role}`;
  row.innerHTML = `
    ${role === 'assistant' ? '<div class="agent-avatar">AI</div>' : ''}
    <div class="msg-bubble">${escapeHtml(text)}</div>
  `;
  container.appendChild(row);
  container.scrollTop = container.scrollHeight;
}

async function clearCurrentChat() {
  if (!confirm("Are you sure you want to clear your current conversation?")) return;
  try {
    await fetch(`/api/chat/session/${sessionId}`, { method: "DELETE" });
    const container = document.getElementById("chat-messages-container");
    container.innerHTML = `
      <div class="message-row assistant">
        <div class="agent-avatar">AI</div>
        <div class="msg-bubble">
          Conversation cleared. How can I assist you with ApexTech orders, policies, or technical support?
        </div>
      </div>
    `;
  } catch (e) {
    console.error("Clear error:", e);
  }
}

// Admin Dashboard - Tickets
async function loadTickets() {
  const filter = document.getElementById("ticket-filter").value;
  const url = filter ? `/api/tickets?status=${filter}` : "/api/tickets";
  
  try {
    const res = await fetch(url);
    const data = await res.json();
    const tickets = data.tickets || [];

    // Update metrics
    document.getElementById("metric-total-tickets").innerText = tickets.length;
    document.getElementById("metric-open-tickets").innerText = tickets.filter(t => t.status === "OPEN").length;
    document.getElementById("metric-escalated-tickets").innerText = tickets.filter(t => t.status === "ESCALATED").length;
    document.getElementById("metric-resolved-tickets").innerText = tickets.filter(t => t.status === "RESOLVED").length;

    const tbody = document.getElementById("tickets-table-body");
    if (!tickets.length) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">No tickets found.</td></tr>`;
      return;
    }

    tbody.innerHTML = tickets.map(t => `
      <tr>
        <td><strong>${t.id}</strong></td>
        <td>
          <div style="font-weight: 600;">${escapeHtml(t.subject)}</div>
          <div style="font-size: 0.775rem; color: var(--text-muted); max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
            ${escapeHtml(t.description)}
          </div>
        </td>
        <td><span class="badge badge-${t.priority.toLowerCase()}">${t.priority}</span></td>
        <td><span class="badge badge-${t.status.toLowerCase()}">${t.status}</span></td>
        <td>${escapeHtml(t.assigned_agent || 'Unassigned')}</td>
        <td style="font-size: 0.8rem; color: var(--text-muted);">${t.created_at ? t.created_at.slice(0, 16) : ''}</td>
        <td>
          <div style="display: flex; flex-direction: column; gap: 4px;">
            <select onchange="updateTicketStatus('${t.id}', this.value)" class="form-control" style="padding: 2px 6px; font-size: 0.775rem;">
              <option value="" disabled selected>Update Status</option>
              <option value="OPEN">Mark Open</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="ESCALATED">Escalate</option>
              <option value="RESOLVED">Resolve</option>
            </select>
            <button class="settings-btn" style="padding: 2px 6px; font-size: 0.75rem; color: #4f46e5; font-weight: 600;" onclick="openInspectTicketModal('${t.id}')">
              💬 Inspect & Takeover
            </button>
          </div>
        </td>
      </tr>
    `).join("");

  } catch (err) {
    console.error("Error loading tickets:", err);
  }
}

async function updateTicketStatus(ticketId, newStatus) {
  if (!newStatus) return;
  try {
    await fetch(`/api/tickets/${ticketId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus })
    });
    loadTickets();
  } catch (e) {
    alert("Error updating ticket: " + e.message);
  }
}

// Admin Dashboard - Knowledge Base (RAG)
async function loadKnowledge() {
  try {
    const res = await fetch("/api/knowledge");
    const data = await res.json();
    const docs = data.documents || [];

    const tbody = document.getElementById("knowledge-table-body");
    if (!docs.length) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">No knowledge articles.</td></tr>`;
      return;
    }

    tbody.innerHTML = docs.map(d => `
      <tr>
        <td><code>${d.id}</code></td>
        <td><strong>${escapeHtml(d.title)}</strong></td>
        <td><span class="badge badge-medium">${escapeHtml(d.category)}</span></td>
        <td style="font-size: 0.825rem; color: var(--text-muted); max-width: 400px;">
          ${escapeHtml(d.content.slice(0, 140))}...
        </td>
        <td>
          <button class="settings-btn" style="color: var(--danger); font-size: 0.75rem;" onclick="deleteDoc('${d.id}')">
            Delete
          </button>
        </td>
      </tr>
    `).join("");

  } catch (err) {
    console.error("Error loading knowledge docs:", err);
  }
}

async function testRagSearch() {
  const query = document.getElementById("rag-test-input").value.trim();
  const resultsContainer = document.getElementById("rag-test-results");
  if (!query) return;

  resultsContainer.innerHTML = `<span style="font-size: 0.825rem; color: var(--text-muted);">Vector searching index...</span>`;

  try {
    const res = await fetch("/api/knowledge/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, top_k: 2 })
    });
    const data = await res.json();
    const hits = data.results || [];

    if (!hits.length) {
      resultsContainer.innerHTML = `<p style="font-size: 0.825rem; color: var(--danger);">No relevant articles met the similarity threshold.</p>`;
      return;
    }

    resultsContainer.innerHTML = hits.map(h => `
      <div style="background: #f8fafc; border: 1px solid var(--border); border-radius: 8px; padding: 0.75rem; margin-top: 0.5rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
          <strong style="font-size: 0.875rem;">${escapeHtml(h.title)}</strong>
          <span class="badge badge-resolved">Score: ${(h.similarity * 100).toFixed(1)}%</span>
        </div>
        <p style="font-size: 0.8rem; color: #475569;">${escapeHtml(h.content)}</p>
      </div>
    `).join("");

  } catch (err) {
    resultsContainer.innerHTML = `<p style="color: var(--danger); font-size: 0.825rem;">Search error: ${err.message}</p>`;
  }
}

async function deleteDoc(docId) {
  if (!confirm(`Delete document ${docId}?`)) return;
  try {
    await fetch(`/api/knowledge/${docId}`, { method: "DELETE" });
    loadKnowledge();
  } catch (e) {
    alert("Error deleting document: " + e.message);
  }
}

// Admin Dashboard - Orders
async function loadOrders() {
  try {
    const res = await fetch("/api/orders");
    const data = await res.json();
    const orders = data.orders || [];

    const tbody = document.getElementById("orders-table-body");
    if (!orders.length) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">No orders found.</td></tr>`;
      return;
    }

    tbody.innerHTML = orders.map(o => {
      let itemsStr = "";
      if (Array.isArray(o.items_parsed)) {
        itemsStr = o.items_parsed.map(i => `${i.qty}x ${i.item}`).join(", ");
      } else {
        itemsStr = o.items;
      }

      return `
        <tr>
          <td><strong>${o.id}</strong></td>
          <td>${escapeHtml(o.customer_name)}<br><small style="color: var(--text-muted);">${escapeHtml(o.customer_email)}</small></td>
          <td><span class="badge badge-${o.customer_tier === 'VIP' ? 'high' : 'low'}">${o.customer_tier}</span></td>
          <td style="font-size: 0.825rem;">${escapeHtml(itemsStr)}</td>
          <td><strong>$${o.total_amount.toFixed(2)}</strong></td>
          <td><span class="badge badge-${o.status.toLowerCase().replace(' ', '_')}">${o.status}</span></td>
          <td style="font-size: 0.8rem;">${o.tracking_number ? `<code>${o.tracking_number}</code>` : 'None'}</td>
          <td>${o.is_refundable ? '✅ Yes (30d)' : '❌ Expired'}</td>
        </tr>
      `;
    }).join("");

  } catch (err) {
    console.error("Error loading orders:", err);
  }
}

// Modals
function openSettingsModal() {
  document.getElementById("settings-modal").classList.add("open");
  if (currentSettings) {
    document.getElementById("setting-provider-select").value = currentSettings.active_provider;
    handleProviderChangeUI();
  }
}
function closeSettingsModal() {
  document.getElementById("settings-modal").classList.remove("open");
}

function openNewDocModal() {
  document.getElementById("new-doc-modal").classList.add("open");
}
function closeNewDocModal() {
  document.getElementById("new-doc-modal").classList.remove("open");
}

function openNewTicketModal() {
  document.getElementById("new-ticket-modal").classList.add("open");
}
function closeNewTicketModal() {
  document.getElementById("new-ticket-modal").classList.remove("open");
}

function handleProviderChangeUI() {
  const provider = document.getElementById("setting-provider-select").value;
  const keyContainer = document.getElementById("settings-key-container");
  const modelInput = document.getElementById("setting-model-name");

  if (provider === "demo") {
    keyContainer.style.display = "none";
    modelInput.value = "rule-heuristic-agent";
  } else if (provider === "gemini") {
    keyContainer.style.display = "block";
    document.getElementById("settings-key-label").innerText = "Gemini API Key";
    modelInput.value = "gemini-2.5-flash";
  } else if (provider === "openai") {
    keyContainer.style.display = "block";
    document.getElementById("settings-key-label").innerText = "OpenAI API Key";
    modelInput.value = "gpt-4o-mini";
  } else if (provider === "groq") {
    keyContainer.style.display = "block";
    document.getElementById("settings-key-label").innerText = "Groq API Key";
    modelInput.value = "llama-3.3-70b-versatile";
  } else if (provider === "ollama") {
    keyContainer.style.display = "block";
    document.getElementById("settings-key-label").innerText = "Ollama Base URL (e.g. http://localhost:11434)";
    modelInput.value = "llama3:8b";
  }
}

async function loadSettings() {
  try {
    const res = await fetch("/api/settings");
    currentSettings = await res.json();
    
    const prov = currentSettings.active_provider.toUpperCase();
    document.getElementById("provider-name-display").innerText = prov;
    document.getElementById("agent-active-model").innerText = prov;
  } catch (e) {
    console.error("Error loading settings:", e);
  }
}

async function saveSettings() {
  const provider = document.getElementById("setting-provider-select").value;
  const apiKey = document.getElementById("setting-api-key").value.trim();
  const model = document.getElementById("setting-model-name").value.trim();

  const payload = { provider, model };
  if (provider === "ollama" && apiKey) {
    payload.base_url = apiKey;
  } else if (apiKey) {
    payload.api_key = apiKey;
  }

  try {
    const res = await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (result.success) {
      alert("Settings applied! Active provider is now: " + provider.toUpperCase());
      closeSettingsModal();
      loadSettings();
    } else {
      alert("Error: " + result.error);
    }
  } catch (e) {
    alert("Failed to save settings: " + e.message);
  }
}

async function submitNewDoc() {
  const title = document.getElementById("doc-title-input").value.trim();
  const category = document.getElementById("doc-category-input").value.trim();
  const content = document.getElementById("doc-content-input").value.trim();

  if (!title || !content) {
    alert("Please provide title and content.");
    return;
  }

  try {
    const res = await fetch("/api/knowledge", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, category, content })
    });
    if (res.ok) {
      closeNewDocModal();
      loadKnowledge();
      document.getElementById("doc-title-input").value = "";
      document.getElementById("doc-content-input").value = "";
    }
  } catch (e) {
    alert("Error indexing document: " + e.message);
  }
}

async function submitNewTicket() {
  const subject = document.getElementById("ticket-subject-input").value.trim();
  const customer_email = document.getElementById("ticket-email-input").value.trim();
  const priority = document.getElementById("ticket-priority-select").value;
  const description = document.getElementById("ticket-desc-input").value.trim();

  if (!subject || !description) {
    alert("Please provide subject and description.");
    return;
  }

  try {
    const res = await fetch("/api/tickets", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ subject, customer_email, priority, description })
    });
    if (res.ok) {
      closeNewTicketModal();
      loadTickets();
      document.getElementById("ticket-subject-input").value = "";
      document.getElementById("ticket-desc-input").value = "";
    }
  } catch (e) {
    alert("Error creating ticket: " + e.message);
  }
}

// Utilities
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ==========================================
// ADVANCED FEATURES: Sentiment, CSAT, Analytics, Takeover & File Upload
// ==========================================

let currentInspectedTicketId = null;
let currentCsatRating = 5;

// 1. Live Sentiment Meter
function updateSentimentBadge(sentiment) {
  const badge = document.getElementById("customer-sentiment-badge");
  const text = document.getElementById("sentiment-text");
  if (!badge || !text) return;

  badge.className = "sentiment-chip";
  let icon = "😐";

  if (sentiment.label === "Positive") {
    badge.classList.add("sentiment-positive");
    icon = "😊";
  } else if (sentiment.label === "Frustrated") {
    badge.classList.add("sentiment-frustrated");
    icon = "😡";
  } else if (sentiment.label === "Dissatisfied") {
    badge.classList.add("sentiment-dissatisfied");
    icon = "😟";
  } else {
    badge.classList.add("sentiment-neutral");
    icon = "😐";
  }

  text.innerText = `Mood: ${sentiment.label} (${sentiment.score > 0 ? '+' : ''}${sentiment.score})`;
  badge.querySelector("span:first-child").innerText = icon;
}

// 2. CSAT Rating
function rateCsat(rating) {
  currentCsatRating = rating;
  const stars = document.querySelectorAll("#csat-star-group .star-btn");
  stars.forEach((s, idx) => {
    s.classList.toggle("active", idx < rating);
  });
}

function dismissCsat() {
  const card = document.getElementById("csat-card");
  if (card) card.style.display = "none";
}

async function submitCsatFeedback() {
  const feedback = document.getElementById("csat-feedback-input").value.trim();
  try {
    await fetch("/api/chat/csat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, rating: currentCsatRating, feedback })
    });
    const card = document.getElementById("csat-card");
    if (card) {
      card.innerHTML = `<span style="color: #16a34a; font-size: 0.875rem; font-weight: 600;">🎉 Thank you for your feedback! Rating submitted.</span>`;
      setTimeout(() => dismissCsat(), 3000);
    }
  } catch (e) {
    console.error("CSAT error:", e);
  }
}

// 3. Analytics Dashboard
async function loadAnalytics() {
  try {
    const res = await fetch("/api/analytics");
    const data = await res.json();

    document.getElementById("analytics-csat-score").innerText = data.avg_csat.toFixed(1);
    document.getElementById("analytics-csat-count").innerText = `(${data.total_ratings} ratings)`;
    document.getElementById("analytics-csat-bar").style.width = `${(data.avg_csat / 5) * 100}%`;

    document.getElementById("analytics-resolution-rate").innerText = `${data.resolution_rate}%`;
    document.getElementById("analytics-res-bar").style.width = `${data.resolution_rate}%`;

    // Sentiment breakdown
    const totalSent = Object.values(data.sentiment_counts).reduce((a, b) => a + b, 0) || 1;
    const posPct = Math.round((data.sentiment_counts["Positive"] / totalSent) * 100);
    const neuPct = Math.round((data.sentiment_counts["Neutral"] / totalSent) * 100);
    const fruPct = Math.round(((data.sentiment_counts["Frustrated"] + data.sentiment_counts["Dissatisfied"]) / totalSent) * 100);

    document.getElementById("sent-pos-val").innerText = `${posPct}%`;
    document.getElementById("sent-pos-bar").style.width = `${posPct}%`;
    document.getElementById("sent-neu-val").innerText = `${neuPct}%`;
    document.getElementById("sent-neu-bar").style.width = `${neuPct}%`;
    document.getElementById("sent-fru-val").innerText = `${fruPct}%`;
    document.getElementById("sent-fru-bar").style.width = `${fruPct}%`;

    // Tool counts
    document.getElementById("tool-order-count").innerText = data.tool_counts["check_order_status"] || 0;
    document.getElementById("tool-kb-count").innerText = data.tool_counts["search_knowledge_base"] || 0;
    document.getElementById("tool-refund-count").innerText = data.tool_counts["process_refund_return"] || 0;
    document.getElementById("tool-esc-count").innerText = data.tool_counts["escalate_to_human"] || 0;

  } catch (e) {
    console.error("Analytics load error:", e);
  }
}

// 4. Ticket Inspection, AI Case Summary & Live Takeover
async function openInspectTicketModal(ticketId) {
  currentInspectedTicketId = ticketId;
  const modal = document.getElementById("inspect-ticket-modal");
  modal.classList.add("open");

  document.getElementById("inspect-modal-title").innerText = `Ticket #${ticketId}`;
  document.getElementById("inspect-modal-subtitle").innerText = "Loading conversation & status...";
  document.getElementById("ai-summary-content").innerText = "Click 'Generate AI Summary' to analyze this case with LLM.";

  try {
    const res = await fetch(`/api/tickets`);
    const data = await res.json();
    const ticket = (data.tickets || []).find(t => t.id === ticketId);
    if (ticket) {
      document.getElementById("inspect-modal-title").innerText = `${ticket.subject} (#${ticket.id})`;
      document.getElementById("inspect-modal-subtitle").innerText = `Status: ${ticket.status} | Priority: ${ticket.priority} | Customer: ${ticket.customer_email || 'guest'}`;
    }
  } catch (e) {
    console.error(e);
  }
}

function closeInspectTicketModal() {
  document.getElementById("inspect-ticket-modal").classList.remove("open");
  currentInspectedTicketId = null;
}

async function fetchAiTicketSummary() {
  if (!currentInspectedTicketId) return;
  const summaryBox = document.getElementById("ai-summary-content");
  summaryBox.innerHTML = `<em>Generating AI case diagnosis and draft reply...</em>`;

  try {
    const res = await fetch(`/api/tickets/${currentInspectedTicketId}/ai-summary`, { method: "POST" });
    const data = await res.json();
    summaryBox.innerText = data.ai_summary || "No summary available.";
  } catch (e) {
    summaryBox.innerText = "Error generating AI summary: " + e.message;
  }
}

async function toggleTakeoverLive() {
  try {
    const res = await fetch("/api/chat/takeover", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, takeover: true, agent_name: "Sarah M. (Live Specialist)" })
    });
    const data = await res.json();
    document.getElementById("takeover-status-box").innerHTML = `
      <span style="color: #16a34a;">🟢 <strong>Live Human Takeover Active:</strong> Sarah M. is connected.</span>
      <button class="settings-btn" style="font-size: 0.75rem;" onclick="releaseTakeover()">Release to AI</button>
    `;
    alert("You have taken over this session. The customer was notified that a live human specialist has joined the chat!");
  } catch (e) {
    alert("Takeover error: " + e.message);
  }
}

async function releaseTakeover() {
  try {
    await fetch("/api/chat/takeover", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, takeover: false })
    });
    document.getElementById("takeover-status-box").innerHTML = `
      <span>🤖 Active Responder: <strong>AI Support Agent</strong></span>
      <button class="btn-primary" style="font-size: 0.75rem; padding: 0.35rem 0.75rem;" onclick="toggleTakeoverLive()">
        💬 Take Over Live as Human Agent
      </button>
    `;
    alert("Session released back to autonomous AI Agent.");
  } catch (e) {
    alert("Release error: " + e.message);
  }
}

async function submitHumanReply() {
  const input = document.getElementById("human-reply-input");
  const message = input.value.trim();
  if (!message) return;

  try {
    await fetch("/api/chat/human-reply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message, agent_name: "Sarah M. (Human Specialist)" })
    });
    input.value = "";
    alert("Human message sent directly to customer's live chat window!");
  } catch (e) {
    alert("Error sending message: " + e.message);
  }
}

async function resolveCurrentInspectedTicket() {
  if (!currentInspectedTicketId) return;
  await updateTicketStatus(currentInspectedTicketId, "RESOLVED");
  closeInspectTicketModal();
}

// 5. Documentation File Upload
function openUploadDocModal() {
  document.getElementById("upload-doc-modal").classList.add("open");
}
function closeUploadDocModal() {
  document.getElementById("upload-doc-modal").classList.remove("open");
}

async function submitUploadDoc() {
  const fileInput = document.getElementById("upload-doc-file");
  const title = document.getElementById("upload-doc-title").value.trim();
  const category = document.getElementById("upload-doc-category").value.trim();

  if (!fileInput.files.length) {
    alert("Please select a file to upload.");
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  if (title) formData.append("title", title);
  if (category) formData.append("category", category);

  try {
    const res = await fetch("/api/knowledge/upload", {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    if (res.ok) {
      alert("Success! " + data.message);
      closeUploadDocModal();
      loadKnowledge();
    } else {
      alert("Upload failed: " + data.error);
    }
  } catch (e) {
    alert("Upload error: " + e.message);
  }
}
