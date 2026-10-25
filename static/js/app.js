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
  document.getElementById("admin-content-knowledge").style.display = tab === "knowledge" ? "block" : "none";
  document.getElementById("admin-content-orders").style.display = tab === "orders" ? "block" : "none";

  if (tab === "tickets") loadTickets();
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

          if (event.type === "thought") {
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
          <select onchange="updateTicketStatus('${t.id}', this.value)" class="form-control" style="padding: 2px 6px; font-size: 0.775rem;">
            <option value="" disabled selected>Update Status</option>
            <option value="OPEN">Mark Open</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="ESCALATED">Escalate</option>
            <option value="RESOLVED">Resolve</option>
          </select>
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
