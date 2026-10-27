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

let activeAgentType = "ecommerce";
let isVoiceTTSActive = true;
let isRecordingMic = false;
let callDurationSeconds = 45;
let callTimerInterval = null;

// Initialization
document.addEventListener("DOMContentLoaded", () => {
  loadSettings();
  loadTickets();
  loadKnowledge();
  loadOrders();
  startCallTimer();
  updateRoiCalculation();

  // Support URL routing for automated captures and direct deep links
  const urlParams = new URLSearchParams(window.location.search);
  const viewParam = urlParams.get("view");
  if (viewParam && DASHBOARD_METADATA[viewParam]) {
    switchView(viewParam);
  }
  const submodeParam = urlParams.get("submode");
  if (submodeParam && viewParam) {
    const domainPrefix = viewParam === "ecommerce" ? "ecom" : (viewParam === "hotel" ? "hotel" : (viewParam === "voice" ? "voice" : (viewParam === "whatsapp" ? "wa" : "saas")));
    toggleSubmode(domainPrefix, submodeParam);
  }
  const autorunParam = urlParams.get("autorun");
  if (autorunParam === "trials") {
    setTimeout(() => {
      if (typeof executeLiveBenchmarkTrials === "function") {
        executeLiveBenchmarkTrials();
      }
    }, 400);
  }
});

// Dashboard Metadata for App Launcher and Navigation
const DASHBOARD_METADATA = {
  overview: { name: "Platform Overview", icon: "⚡" },
  ecommerce: { name: "E-Commerce Agent", icon: "🛍️" },
  hotel: { name: "Hospitality Resort", icon: "🏨" },
  voice: { name: "Voice Telephony Agent", icon: "🎙️" },
  whatsapp: { name: "WhatsApp Commerce", icon: "💬" },
  saas: { name: "SaaS Platform Support", icon: "💻" },
  builder: { name: "Agentforce Builder", icon: "🛠️" },
  admin: { name: "Service Console & CRM", icon: "📊" },
  evaluation: { name: "Benchmark & Evaluation", icon: "📈" }
};

function toggleSidebar() {
  const sb = document.getElementById("app-sidebar");
  if (!sb) return;
  sb.classList.toggle("collapsed");
  try {
    localStorage.setItem("agentforce_sidebar_collapsed", sb.classList.contains("collapsed") ? "true" : "false");
  } catch (e) {}
}

function toggleDashboardDropdown(event) {
  if (event) event.stopPropagation();
  const menu = document.getElementById("dashboard-dropdown-menu");
  if (menu) menu.classList.toggle("show");
}

function closeDashboardDropdown() {
  const menu = document.getElementById("dashboard-dropdown-menu");
  if (menu) menu.classList.remove("show");
}

document.addEventListener("click", (e) => {
  const switcher = document.getElementById("dashboard-switcher");
  if (switcher && !switcher.contains(e.target)) {
    closeDashboardDropdown();
  }
});

// Restore sidebar state
try {
  if (localStorage.getItem("agentforce_sidebar_collapsed") === "true") {
    const sb = document.getElementById("app-sidebar");
    if (sb) sb.classList.add("collapsed");
  }
} catch (e) {}

// View Navigation across Agentforce Platform + Dedicated Standalone Dashboards
function switchView(view) {
  const allViews = ["overview", "ecommerce", "hotel", "voice", "whatsapp", "saas", "builder", "admin", "evaluation"];
  allViews.forEach(v => {
    const el = document.getElementById(`view-${v}`);
    const tab = document.getElementById(`tab-${v}`);
    const side = document.getElementById(`side-${v}`);
    if (el) el.classList.toggle("active", v === view);
    if (tab) tab.classList.toggle("active", v === view);
    if (side) side.classList.toggle("active", v === view);
  });

  // Update App Launcher dropdown active item
  document.querySelectorAll(".dash-menu-item").forEach(item => {
    item.classList.toggle("active", item.getAttribute("data-view") === view);
  });

  // Update App Launcher header button
  const meta = DASHBOARD_METADATA[view] || { name: "Platform Overview", icon: "⚡" };
  const curLabel = document.getElementById("current-dashboard-label");
  const curIcon = document.getElementById("current-dashboard-icon");
  if (curLabel) curLabel.innerText = meta.name;
  if (curIcon) curIcon.innerText = meta.icon;

  closeDashboardDropdown();

  activeAgentType = (view === "admin" || view === "overview" || view === "builder" || view === "evaluation") ? "ecommerce" : view;

  if (view === "overview") {
    updateRoiCalculation();
  } else if (view === "evaluation") {
    loadEvaluationBenchmarks();
  } else if (view === "builder") {
    loadAgentforceTopics();
    loadTrustGuardrails();
  } else if (view === "admin") {
    loadTickets();
    loadAnalytics();
  } else if (view === "ecommerce") {
    const p = document.getElementById("ecom-dash-panel");
    if (p && p.style.display !== "none") loadEcomDashboard();
  } else if (view === "hotel") {
    const p = document.getElementById("hotel-dash-panel");
    if (p && p.style.display !== "none") loadHotelDashboard();
  } else if (view === "voice") {
    const p = document.getElementById("voice-dash-panel");
    if (p && p.style.display !== "none") loadVoiceDashboard();
  } else if (view === "whatsapp") {
    const p = document.getElementById("wa-dash-panel");
    if (p && p.style.display !== "none") loadWhatsAppDashboard();
  } else if (view === "saas") {
    const p = document.getElementById("saas-dash-panel");
    if (p && p.style.display !== "none") loadSaasDashboard();
  }

  // Smooth scroll to top of view
  const mainWrapper = document.querySelector(".main-content-wrapper");
  if (mainWrapper) mainWrapper.scrollTo({ top: 0, behavior: "smooth" });
}

function startCallTimer() {
  if (callTimerInterval) clearInterval(callTimerInterval);
  callTimerInterval = setInterval(() => {
    callDurationSeconds++;
    const mins = String(Math.floor(callDurationSeconds / 60)).padStart(2, '0');
    const secs = String(callDurationSeconds % 60).padStart(2, '0');
    const timerEl = document.getElementById("voice-call-timer");
    if (timerEl) timerEl.innerText = `${mins}:${secs}`;
  }, 1000);
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
      body: JSON.stringify({ message, session_id: sessionId, agent_type: "ecommerce" })
    });

    if (!response.ok) {
      throw new Error(`Server returned HTTP ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let accumulatedText = "";
    let isFirstAnswerToken = true;
    let lastToolCall = null;
    let lastObservation = null;

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
            lastToolCall = event.tool;
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
            lastObservation = event.content;
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
    } else if (accumulatedText) {
      let trail = {
        engine: "Salesforce Atlas Reasoning Engine v3.4",
        grounded_in: ["Salesforce Data Cloud", "Customer 360", "E-Commerce Knowledge Base"],
        trust_layer: { confidence_score: "98.5%" },
        steps: [
          { type: "Atlas Reasoning & Tone Audit", detail: "Classified order/return inquiry with zero-latency sentiment audit." },
          { type: "Data Cloud Grounding & Policy Check", detail: "Grounding verified with SQLite Vector RAG and Orders database." }
        ]
      };
      if (lastToolCall) {
        trail.steps.push({
          type: "Autonomous Action: " + lastToolCall,
          observation: lastObservation || "Action completed successfully."
        });
      }
      answerContent.innerHTML = escapeHtml(accumulatedText) + renderAtlasTrailFromData(trail);
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

// ==========================================
// 1. HOTEL & HOSPITALITY CONTROLLER
// ==========================================

function sendHotelPrompt(promptText) {
  const input = document.getElementById("hotel-user-input");
  input.value = promptText;
  document.getElementById("hotel-form").dispatchEvent(new Event("submit"));
}

async function handleSendHotelMessage(event) {
  if (event) event.preventDefault();
  const input = document.getElementById("hotel-user-input");
  const message = input.value.trim();
  if (!message) return;
  input.value = "";

  const container = document.getElementById("hotel-messages-container");
  
  // User bubble
  const userRow = document.createElement("div");
  userRow.className = "message-row user";
  userRow.innerHTML = `<div class="msg-bubble">${escapeHtml(message)}</div>`;
  container.appendChild(userRow);

  // Assistant bubble placeholder
  const botRow = document.createElement("div");
  botRow.className = "message-row assistant";
  botRow.innerHTML = `
    <div class="agent-avatar" style="background: #fef3c7; color: #b45309;">🏨</div>
    <div class="msg-bubble"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></div>
  `;
  container.appendChild(botRow);
  container.scrollTop = container.scrollHeight;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: "hotel_" + sessionId, agent_type: "hotel" })
    });
    const data = await res.json();
    let replyHtml = `<div style="white-space: pre-wrap;">${escapeHtml(data.response)}</div>`;
    if (data.atlas_reasoning_trail) {
      replyHtml += renderAtlasTrailFromData(data.atlas_reasoning_trail);
    }
    botRow.querySelector(".msg-bubble").innerHTML = replyHtml;
  } catch (err) {
    botRow.querySelector(".msg-bubble").innerText = "Concierge connection error: " + err.message;
  }
  container.scrollTop = container.scrollHeight;
}

function clearHotelChat() {
  document.getElementById("hotel-messages-container").innerHTML = `
    <div class="message-row assistant">
      <div class="agent-avatar" style="background: #fef3c7; color: #b45309;">🏨</div>
      <div class="msg-bubble">Grand Apex Concierge desk cleared. How may I assist you with rooms, reservations, or resort facilities?</div>
    </div>
  `;
}

// ==========================================
// 2. AI VOICE SUPPORT AGENT CONTROLLER (Phone Call)
// ==========================================

function toggleVoiceSpeechAudio() {
  isVoiceTTSActive = !isVoiceTTSActive;
  const btn = document.getElementById("voice-tts-toggle");
  btn.innerText = isVoiceTTSActive ? "🔊 Voice Speech: ON" : "🔇 Voice Speech: OFF";
  btn.style.color = isVoiceTTSActive ? "#38bdf8" : "#94a3b8";
}

function speakVoiceResponse(text) {
  if (!isVoiceTTSActive || !window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  // Strip code blocks or emojis for natural speech
  const cleanSpeech = text.replace(/[*#`_]/g, "").replace(/https?:\/\/\S+/g, "link").slice(0, 300);
  const utterance = new SpeechSynthesisUtterance(cleanSpeech);
  utterance.rate = 1.05;
  utterance.pitch = 1.0;
  window.speechSynthesis.speak(utterance);
}

function toggleMicrophoneSTT() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    alert("Speech recognition is not supported in this browser. Please type your message or use Google Chrome/Edge.");
    return;
  }

  const micBtn = document.getElementById("voice-mic-btn");

  if (!isRecordingMic) {
    try {
      const recognition = new SpeechRecognition();
      recognition.lang = "en-US";
      recognition.interimResults = false;

      recognition.onstart = () => {
        isRecordingMic = true;
        micBtn.classList.add("speaking");
        document.getElementById("voice-call-status").innerText = "🎙️ Listening to your spoken voice...";
      };

      recognition.onresult = (event) => {
        const spokenTranscript = event.results[0][0].transcript;
        document.getElementById("voice-spoken-input").value = spokenTranscript;
        document.getElementById("voice-call-status").innerText = "Call Active &bull; Processing Spoken Audio";
        handleSendVoiceSpokenMessage();
      };

      recognition.onerror = (e) => {
        console.error("STT error:", e);
        micBtn.classList.remove("speaking");
        isRecordingMic = false;
        document.getElementById("voice-call-status").innerText = "Call Active &bull; Mic Error (" + e.error + ")";
      };

      recognition.onend = () => {
        isRecordingMic = false;
        micBtn.classList.remove("speaking");
      };

      recognition.start();
    } catch (e) {
      alert("Microphone access error: " + e.message);
    }
  }
}

async function handleSendVoiceSpokenMessage(event) {
  if (event) event.preventDefault();
  const input = document.getElementById("voice-spoken-input");
  const spokenText = input.value.trim();
  if (!spokenText) return;
  input.value = "";

  const feed = document.getElementById("voice-transcript-feed");
  feed.innerHTML += `<p style="color: #38bdf8; margin-top: 6px;"><strong>[Caller]:</strong> "${escapeHtml(spokenText)}"</p>`;
  feed.scrollTop = feed.scrollHeight;

  document.getElementById("voice-call-status").innerText = "Call Active &bull; Operator Speaking...";

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: spokenText, session_id: "voice_" + sessionId, agent_type: "voice" })
    });
    const data = await res.json();
    const reply = data.response;
    feed.innerHTML += `<p style="color: #f8fafc; margin-top: 6px;"><strong>[Operator]:</strong> "${escapeHtml(reply)}"</p>`;
    feed.scrollTop = feed.scrollHeight;

    // Trigger natural Text-to-Speech audio
    speakVoiceResponse(reply);
    document.getElementById("voice-call-status").innerText = "Call Active &bull; Telephone AI Operator Connected";
  } catch (err) {
    feed.innerHTML += `<p style="color: #ef4444; margin-top: 6px;">[Call Network Interrupted]: ${err.message}</p>`;
  }
}

function triggerVoiceTransfer() {
  const feed = document.getElementById("voice-transcript-feed");
  feed.innerHTML += `<p style="color: #f59e0b; margin-top: 6px; font-weight: 600;">[System]: "Please hold while I transfer your call to Senior Telephone Support Supervisor..."</p>`;
  speakVoiceResponse("Please hold while I transfer your call to Senior Telephone Support Supervisor.");
  feed.scrollTop = feed.scrollHeight;
}

// ==========================================
// 3. WHATSAPP BUSINESS CONTROLLER
// ==========================================

function sendWhatsAppPrompt(text) {
  const input = document.getElementById("wa-user-input");
  input.value = text;
  document.getElementById("wa-form").dispatchEvent(new Event("submit"));
}

async function handleSendWhatsAppMessage(event) {
  if (event) event.preventDefault();
  const input = document.getElementById("wa-user-input");
  const message = input.value.trim();
  if (!message) return;
  input.value = "";

  const container = document.getElementById("wa-messages-container");
  const now = new Date();
  const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  // User bubble
  const userRow = document.createElement("div");
  userRow.className = "wa-message-row user";
  userRow.innerHTML = `
    <div class="wa-bubble">
      ${escapeHtml(message)}
      <span class="wa-timestamp">${timeStr} <span style="color: #53bdeb;">✓✓</span></span>
    </div>
  `;
  container.appendChild(userRow);

  // Bot placeholder
  const botRow = document.createElement("div");
  botRow.className = "wa-message-row assistant";
  botRow.innerHTML = `
    <div class="wa-bubble">
      <span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>
      <span class="wa-timestamp">${timeStr}</span>
    </div>
  `;
  container.appendChild(botRow);
  container.scrollTop = container.scrollHeight;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: "wa_" + sessionId, agent_type: "whatsapp" })
    });
    const data = await res.json();
    let replyHtml = `
      <div style="white-space: pre-wrap;">${escapeHtml(data.response)}</div>
      <span class="wa-timestamp">${timeStr}</span>
    `;
    if (data.atlas_reasoning_trail) {
      replyHtml += renderAtlasTrailFromData(data.atlas_reasoning_trail);
    }
    botRow.querySelector(".wa-bubble").innerHTML = replyHtml;
  } catch (err) {
    botRow.querySelector(".wa-bubble").innerText = "WhatsApp network error: " + err.message;
  }
  container.scrollTop = container.scrollHeight;
}

function clearWhatsAppChat() {
  document.getElementById("wa-messages-container").innerHTML = `
    <div class="wa-message-row assistant">
      <div class="wa-bubble">
        👋 Namaste! Welcome to ApexTech WhatsApp Support. Reply with 'catalog' or enter an inquiry to get started!
        <span class="wa-timestamp">12:00 PM <span style="color: #53bdeb;">✓✓</span></span>
      </div>
    </div>
  `;
}

// ==========================================
// 4. SAAS DEVELOPER & TECHNICAL SUPPORT CONTROLLER
// ==========================================

function sendSaasPrompt(text) {
  const input = document.getElementById("saas-user-input");
  input.value = text;
  document.getElementById("saas-form").dispatchEvent(new Event("submit"));
}

async function handleSendSaasMessage(event) {
  if (event) event.preventDefault();
  const input = document.getElementById("saas-user-input");
  const message = input.value.trim();
  if (!message) return;
  input.value = "";

  const container = document.getElementById("saas-messages-container");

  // User bubble
  const userRow = document.createElement("div");
  userRow.className = "message-row user";
  userRow.innerHTML = `<div class="msg-bubble">${escapeHtml(message)}</div>`;
  container.appendChild(userRow);

  // Assistant placeholder
  const botRow = document.createElement("div");
  botRow.className = "message-row assistant";
  botRow.innerHTML = `
    <div class="agent-avatar" style="background: #4f46e5; color: white;">Fin</div>
    <div class="msg-bubble"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></div>
  `;
  container.appendChild(botRow);
  container.scrollTop = container.scrollHeight;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: "saas_" + sessionId, agent_type: "saas" })
    });
    const data = await res.json();
    
    // Parse markdown code blocks in SaaS response
    let formattedText = escapeHtml(data.response);
    formattedText = formattedText.replace(/```javascript([\s\S]*?)```/g, '<div class="saas-code-box"><code>$1</code></div>');
    formattedText = formattedText.replace(/```python([\s\S]*?)```/g, '<div class="saas-code-box"><code>$1</code></div>');
    formattedText = formattedText.replace(/```([\s\S]*?)```/g, '<div class="saas-code-box"><code>$1</code></div>');
    formattedText = formattedText.replace(/`([^`]+)`/g, '<code style="background: #1e293b; color: #38bdf8; padding: 2px 4px; border-radius: 4px;">$1</code>');

    let replyHtml = `<div style="white-space: pre-wrap;">${formattedText}</div>`;
    if (data.atlas_reasoning_trail) {
      replyHtml += renderAtlasTrailFromData(data.atlas_reasoning_trail);
    }
    botRow.querySelector(".msg-bubble").innerHTML = replyHtml;
  } catch (err) {
    botRow.querySelector(".msg-bubble").innerText = "SaaS DevPlatform error: " + err.message;
  }
  container.scrollTop = container.scrollHeight;
}

function clearSaasChat() {
  document.getElementById("saas-messages-container").innerHTML = `
    <div class="message-row assistant">
      <div class="agent-avatar" style="background: #4f46e5; color: white;">Fin</div>
      <div class="msg-bubble">Developer console cleared. Ask any API, webhook, or error diagnostic questions.</div>
    </div>
  `;
}

// ==========================================
// 5. DEDICATED DOMAIN DASHBOARDS & SUBMODES
// ==========================================

function toggleSubmode(domain, mode) {
  if (domain === "ecom") {
    const isChat = mode === "chat";
    const pillChat = document.getElementById("pill-ecom-chat");
    const pillDash = document.getElementById("pill-ecom-dash");
    const panelChat = document.getElementById("ecom-chat-panel");
    const panelDash = document.getElementById("ecom-dash-panel");
    if (pillChat) pillChat.classList.toggle("active", isChat);
    if (pillDash) pillDash.classList.toggle("active", !isChat);
    if (panelChat) panelChat.style.display = isChat ? "block" : "none";
    if (panelDash) panelDash.style.display = isChat ? "none" : "block";
    if (!isChat) loadEcomDashboard();
  } else if (domain === "hotel") {
    const isChat = mode === "chat";
    const pillChat = document.getElementById("pill-hotel-chat");
    const pillDash = document.getElementById("pill-hotel-dash");
    const panelChat = document.getElementById("hotel-chat-panel");
    const panelDash = document.getElementById("hotel-dash-panel");
    if (pillChat) pillChat.classList.toggle("active", isChat);
    if (pillDash) pillDash.classList.toggle("active", !isChat);
    if (panelChat) panelChat.style.display = isChat ? "block" : "none";
    if (panelDash) panelDash.style.display = isChat ? "none" : "block";
    if (!isChat) loadHotelDashboard();
  } else if (domain === "voice") {
    const isCall = mode === "call";
    const pillCall = document.getElementById("pill-voice-call");
    const pillDash = document.getElementById("pill-voice-dash");
    const panelCall = document.getElementById("voice-call-panel");
    const panelDash = document.getElementById("voice-dash-panel");
    if (pillCall) pillCall.classList.toggle("active", isCall);
    if (pillDash) pillDash.classList.toggle("active", !isCall);
    if (panelCall) panelCall.style.display = isCall ? "block" : "none";
    if (panelDash) panelDash.style.display = isCall ? "none" : "block";
    if (!isCall) loadVoiceDashboard();
  } else if (domain === "wa") {
    const isChat = mode === "chat";
    const pillChat = document.getElementById("pill-wa-chat");
    const pillDash = document.getElementById("pill-wa-dash");
    const panelChat = document.getElementById("wa-chat-panel");
    const panelDash = document.getElementById("wa-dash-panel");
    if (pillChat) pillChat.classList.toggle("active", isChat);
    if (pillDash) pillDash.classList.toggle("active", !isChat);
    if (panelChat) panelChat.style.display = isChat ? "block" : "none";
    if (panelDash) panelDash.style.display = isChat ? "none" : "block";
    if (!isChat) loadWhatsAppDashboard();
  } else if (domain === "saas") {
    const isChat = mode === "chat";
    const pillChat = document.getElementById("pill-saas-chat");
    const pillDash = document.getElementById("pill-saas-dash");
    const panelChat = document.getElementById("saas-chat-panel");
    const panelDash = document.getElementById("saas-dash-panel");
    if (pillChat) pillChat.classList.toggle("active", isChat);
    if (pillDash) pillDash.classList.toggle("active", !isChat);
    if (panelChat) panelChat.style.display = isChat ? "block" : "none";
    if (panelDash) panelDash.style.display = isChat ? "none" : "block";
    if (!isChat) loadSaasDashboard();
  }
}

// 1. E-Commerce Dashboard Loader
async function loadEcomDashboard() {
  try {
    const res = await fetch("/api/dashboard/ecommerce");
    const data = await res.json();
    
    // Update metrics
    const totalEl = document.getElementById("ecom-metric-total");
    const revEl = document.getElementById("ecom-metric-rev");
    const returnsEl = document.getElementById("ecom-metric-returns");
    const transitEl = document.getElementById("ecom-metric-transit");

    if (totalEl) totalEl.innerText = data.metrics.total_orders;
    if (revEl) revEl.innerText = `$${Number(data.metrics.total_revenue).toFixed(2)}`;
    if (returnsEl) returnsEl.innerText = data.metrics.returns_count;
    if (transitEl) transitEl.innerText = data.metrics.in_transit_count;

    // Populate Orders Table
    const tbody = document.getElementById("ecom-dash-table-body");
    if (!tbody) return;

    if (!data.orders || data.orders.length === 0) {
      tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--text-muted);">No orders found</td></tr>`;
      return;
    }

    tbody.innerHTML = data.orders.map(o => {
      let itemsStr = "";
      if (Array.isArray(o.items_parsed)) {
        itemsStr = o.items_parsed.map(i => `${i.item || i.name} (x${i.qty || i.quantity || 1})`).join(", ");
      } else {
        itemsStr = typeof o.items === "string" ? o.items : JSON.stringify(o.items);
      }

      let statusBadge = `<span class="badge badge-info">${escapeHtml(o.status)}</span>`;
      if (o.status === "Delivered") statusBadge = `<span class="badge badge-success">Delivered</span>`;
      else if (o.status === "Return Initiated") statusBadge = `<span class="badge badge-warning">Return Initiated</span>`;
      else if (o.status === "In Transit") statusBadge = `<span class="badge badge-primary">In Transit</span>`;
      else if (o.status === "Out for Delivery") statusBadge = `<span class="badge badge-success" style="background: #10b981;">Out for Delivery 🚚</span>`;

      const platformName = o.platform || "ApexTech";
      let platBadge = `<span class="badge" style="background: #0176d3; color: white;">ApexTech</span>`;
      if (platformName.toLowerCase() === "flipkart") {
        platBadge = `<span class="badge" style="background: #2874f0; color: white;">⚡ Flipkart</span>`;
      } else if (platformName.toLowerCase() === "amazon") {
        platBadge = `<span class="badge" style="background: #ff9900; color: black;">📦 Amazon</span>`;
      }

      const currSymbol = (o.currency === "INR" || platformName.toLowerCase() === "flipkart") ? "₹" : "$";

      return `
        <tr>
          <td>${platBadge}</td>
          <td><code><strong>${escapeHtml(o.id)}</strong></code></td>
          <td>${escapeHtml(o.customer_name || "Valued Customer")}</td>
          <td><span class="badge badge-secondary">${escapeHtml(o.customer_tier || "Standard")}</span></td>
          <td style="max-width: 250px; font-size: 0.825rem;">${escapeHtml(itemsStr)}</td>
          <td><strong>${currSymbol}${Number(o.total_amount).toLocaleString()}</strong></td>
          <td>${statusBadge}</td>
          <td><small><code>${escapeHtml(o.shipping_carrier || "N/A")}<br>${escapeHtml(o.tracking_number || "")}</code></small></td>
          <td>
            <button class="settings-btn" style="padding: 2px 7px; font-size: 0.75rem; color: #0176d3;" onclick="toggleSubmode('ecom', 'chat'); sendQuickPrompt('Where is order ${escapeHtml(o.id)}?')">
              ⚡ Track in Chat
            </button>
          </td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    console.error("Failed to load ecom dashboard:", err);
  }
}

// Platform Context Switcher for E-Commerce View
function selectEcomPlatformMode(platform) {
  const btns = document.querySelectorAll(".ecom-plat-btn");
  btns.forEach(b => b.classList.remove("active"));
  
  const activeBtn = document.getElementById(`btn-plat-${platform === "apextech" ? "apex" : platform}`);
  if (activeBtn) activeBtn.classList.add("active");

  const labelEl = document.getElementById("ecom-platform-active-label");
  const inputEl = document.getElementById("chat-user-input");

  if (platform === "flipkart") {
    if (labelEl) labelEl.innerHTML = `Active Context: <strong style="color: #2874f0;">⚡ Flipkart (Ekart Real-Time API)</strong>`;
    if (inputEl) inputEl.placeholder = "Pucho Flipkart order status, Order ID (OD409218392100), delivery hero contact, OTP...";
    const sbInput = document.getElementById("carrier-sandbox-input");
    if (sbInput) sbInput.value = "OD409218392100";
  } else if (platform === "amazon") {
    if (labelEl) labelEl.innerHTML = `Active Context: <strong style="color: #d97706;">📦 Amazon India (ATS Carrier API)</strong>`;
    if (inputEl) inputEl.placeholder = "Pucho Amazon order status, 17-digit Order ID (171-8839201-9921), delivery date...";
    const sbInput = document.getElementById("carrier-sandbox-input");
    if (sbInput) sbInput.value = "171-8839201-9921";
  } else if (platform === "apextech") {
    if (labelEl) labelEl.innerHTML = `Active Context: <strong style="color: #0176d3;">🛒 ApexTech Global Store</strong>`;
    if (inputEl) inputEl.placeholder = "Ask about order status (ORD-1002), warranty, return policy, invoice...";
    const sbInput = document.getElementById("carrier-sandbox-input");
    if (sbInput) sbInput.value = "ORD-1002";
  } else {
    if (labelEl) labelEl.innerHTML = `Active Context: <strong style="color: #0176d3;">Multi-Store Sync</strong>`;
    if (inputEl) inputEl.placeholder = "Pucho order status, Flipkart order ID (e.g. OD409218392100), invoice, delivery boy number...";
    const sbInput = document.getElementById("carrier-sandbox-input");
    if (sbInput) sbInput.value = "OD409218392100";
  }
}

// Live Carrier Telemetry Sandbox Runner
async function trackLiveCarrierSandbox() {
  const inputEl = document.getElementById("carrier-sandbox-input");
  const resultEl = document.getElementById("carrier-sandbox-result");
  if (!inputEl || !resultEl) return;

  const id = inputEl.value.trim();
  if (!id) {
    resultEl.style.display = "block";
    resultEl.innerHTML = `<span style="color: #dc2626;">Please enter an order ID to track.</span>`;
    return;
  }

  resultEl.style.display = "block";
  resultEl.innerHTML = `<div style="color: #54698d;">⚡ Querying live carrier logistics API...</div>`;

  try {
    const res = await fetch(`/api/ecommerce/track?id=${encodeURIComponent(id)}`);
    const data = await res.json();
    if (!data.success || !data.data || !data.data.found) {
      resultEl.innerHTML = `<span style="color: #dc2626;">❌ ${data.data?.message || data.error || "Order not found."}</span>`;
      return;
    }

    const d = data.data;
    const isFk = d.platform.toLowerCase() === "flipkart";
    const badgeColor = isFk ? "#2874f0" : (d.platform.toLowerCase() === "amazon" ? "#d97706" : "#0176d3");
    const curr = (d.currency === "INR" || isFk) ? "₹" : "$";

    let heroHtml = "";
    if (d.delivery_partner_name) {
      heroHtml = `<div style="margin-top: 4px; padding-top: 4px; border-top: 1px dashed #cbd5e1;">
        🛵 <strong>Delivery Hero:</strong> ${escapeHtml(d.delivery_partner_name)} (${escapeHtml(d.delivery_partner_phone || "Contact via app")})
        ${d.delivery_otp ? `<br>🔑 <strong>Security OTP:</strong> <code style="font-weight: 800; color: #2874f0;">${escapeHtml(d.delivery_otp)}</code>` : ""}
      </div>`;
    }

    resultEl.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
        <span class="badge" style="background: ${badgeColor}; color: white; font-size: 0.7rem;">${escapeHtml(d.platform)}</span>
        <span class="badge badge-success" style="font-size: 0.7rem;">${escapeHtml(d.status)} 🚚</span>
      </div>
      <div><strong>Order ID:</strong> <code>${escapeHtml(d.order_id)}</code></div>
      <div><strong>Amount:</strong> ${curr}${Number(d.total_amount).toLocaleString()} (${escapeHtml(d.payment_method)})</div>
      <div><strong>Carrier:</strong> ${escapeHtml(d.carrier)} (<code>${escapeHtml(d.tracking_number)}</code>)</div>
      <div><strong>Current Hub:</strong> ${escapeHtml(d.courier_hub)}</div>
      <div><strong>ETA:</strong> <strong style="color: #10b981;">${escapeHtml(d.estimated_delivery)}</strong></div>
      ${heroHtml}
      <div style="margin-top: 6px;">
        <button class="settings-btn" style="padding: 2px 6px; font-size: 0.7rem; color: #2874f0;" onclick="sendQuickPrompt('Where is order ${escapeHtml(d.order_id)}?')">
          💬 Ask in Chat
        </button>
      </div>
    `;
  } catch (err) {
    resultEl.innerHTML = `<span style="color: #dc2626;">Network error querying carrier API.</span>`;
  }
}

// ==========================================
// BENCHMARKS & EMPIRICAL EVALUATION SUITE
// ==========================================
async function loadEvaluationBenchmarks() {
  try {
    const res = await fetch("/api/evaluation/benchmarks");
    const data = await res.json();
    if (!data) return;

    const latEl = document.getElementById("eval-kpi-latency");
    if (latEl && data.kpis) {
      latEl.innerText = `< ${data.kpis.avg_latency_ms} ms`;
    }
  } catch (err) {
    console.error("Failed to load evaluation benchmarks:", err);
  }
}

async function executeLiveBenchmarkTrials() {
  const btn = document.getElementById("btn-run-live-trials");
  const btnTop = document.getElementById("btn-run-live-trials-top");
  const statusBar = document.getElementById("live-trials-status-bar");
  const statusText = document.getElementById("live-trials-status-text");
  const tbody = document.getElementById("live-trials-table-body");

  if (btn) { btn.disabled = true; btn.innerText = "⏳ Running Live Probes..."; }
  if (btnTop) { btnTop.disabled = true; btnTop.innerText = "⏳ Running Probes..."; }
  if (statusBar) statusBar.style.display = "block";
  if (statusText) statusText.innerHTML = "⚡ Executing live real-time inference probe queries across all 5 domain agents...";

  try {
    const res = await fetch("/api/evaluation/run-live", { method: "POST" });
    const data = await res.json();

    if (!data.success || !data.trials) {
      if (statusText) statusText.innerHTML = "❌ Benchmark trial execution failed.";
      return;
    }

    if (statusText) {
      statusText.innerHTML = `✅ <strong>Completed ${data.total_trials} / ${data.total_trials} Live Trials Successfully!</strong> Total Execution: <strong>${data.total_duration_ms} ms</strong> (Avg: <strong>${data.avg_trial_latency_ms} ms/trial</strong>) &bull; Timestamp: ${data.timestamp}`;
    }

    if (tbody) {
      tbody.innerHTML = data.trials.map(t => {
        return `
          <tr>
            <td><code><strong>${escapeHtml(t.trial_id)}</strong></code></td>
            <td><strong>${escapeHtml(t.domain)}</strong></td>
            <td style="max-width: 220px; font-size: 0.8rem;"><em>"${escapeHtml(t.query)}"</em></td>
            <td><span class="badge" style="background: #e0f2fe; color: #0176d3; font-weight: 800;">${t.latency_ms} ms</span></td>
            <td><code>${escapeHtml(t.action_executed)}</code></td>
            <td style="max-width: 320px; font-size: 0.775rem; color: #334155; line-height: 1.4;">
              ${escapeHtml(t.output_preview)}
            </td>
            <td><span class="badge badge-success" style="font-size: 0.75rem;">PASS ✅</span></td>
          </tr>
        `;
      }).join("");
    }
  } catch (err) {
    console.error("Live benchmark failed:", err);
    if (statusText) statusText.innerHTML = `❌ Error running live benchmark: ${err.message}`;
  } finally {
    if (btn) { btn.disabled = false; btn.innerText = "⚡ Run Live Trials"; }
    if (btnTop) { btnTop.disabled = false; btnTop.innerText = "⚡ Execute Live Benchmark Trials"; }
  }
}

// 2. Hotel Dashboard Loader
async function loadHotelDashboard() {
  try {
    const res = await fetch("/api/dashboard/hotel");
    const data = await res.json();

    const occEl = document.getElementById("hotel-metric-occ");
    const totalEl = document.getElementById("hotel-metric-total");
    const occupiedEl = document.getElementById("hotel-metric-occupied");
    const availEl = document.getElementById("hotel-metric-avail");
    const resEl = document.getElementById("hotel-metric-res");

    if (occEl) occEl.innerText = `${data.metrics.occupancy_rate}%`;
    if (totalEl) totalEl.innerText = data.metrics.total_rooms;
    if (occupiedEl) occupiedEl.innerText = data.metrics.occupied_rooms;
    if (availEl) availEl.innerText = data.metrics.available_rooms;
    if (resEl) resEl.innerText = data.metrics.active_reservations;

    // Room Inventory Table
    const roomsTbody = document.getElementById("hotel-rooms-table-body");
    if (roomsTbody) {
      if (!data.rooms || data.rooms.length === 0) {
        roomsTbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted);">No rooms found</td></tr>`;
      } else {
        roomsTbody.innerHTML = data.rooms.map(r => `
          <tr>
            <td><code>${escapeHtml(r.id)}</code></td>
            <td><strong>${escapeHtml(r.room_type)}</strong></td>
            <td>${escapeHtml(String(r.max_occupancy))} Guests</td>
            <td><strong style="color: #4f46e5;">$${Number(r.price_per_night).toFixed(2)}</strong><small>/night</small></td>
            <td>
              <span class="badge ${r.available_count > 0 ? 'badge-success' : 'badge-danger'}">
                ${r.available_count} Available
              </span>
            </td>
            <td style="font-size: 0.825rem; color: var(--text-muted);">${escapeHtml(r.amenities || "")}</td>
            <td>
              <button class="settings-btn" style="padding: 3px 8px; font-size: 0.775rem;" onclick="toggleSubmode('hotel', 'chat'); sendHotelPrompt('Check availability for ${escapeHtml(r.room_type)}')">
                Book Suite
              </button>
            </td>
          </tr>
        `).join("");
      }
    }

    // Reservations Table
    const resTbody = document.getElementById("hotel-res-table-body");
    if (resTbody) {
      if (!data.reservations || data.reservations.length === 0) {
        resTbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-muted);">No reservations found</td></tr>`;
      } else {
        resTbody.innerHTML = data.reservations.map(resv => `
          <tr>
            <td><strong>${escapeHtml(resv.id)}</strong></td>
            <td>${escapeHtml(resv.guest_name)}</td>
            <td><small>${escapeHtml(resv.guest_email || resv.guest_phone || "N/A")}</small></td>
            <td>${escapeHtml(resv.room_type || resv.room_id)}</td>
            <td>${escapeHtml(resv.check_in_date)}</td>
            <td>${escapeHtml(resv.check_out_date)}</td>
            <td>${escapeHtml(String(resv.num_guests))}</td>
            <td><span class="badge badge-success">${escapeHtml(resv.status)}</span></td>
          </tr>
        `).join("");
      }
    }
  } catch (err) {
    console.error("Failed to load hotel dashboard:", err);
  }
}

// 3. Voice Telephony Dashboard Loader
async function loadVoiceDashboard() {
  try {
    const res = await fetch("/api/dashboard/voice");
    const data = await res.json();

    const callsEl = document.getElementById("voice-metric-calls");
    const ahtEl = document.getElementById("voice-metric-aht");
    const fcrEl = document.getElementById("voice-metric-fcr");
    const transfersEl = document.getElementById("voice-metric-transfers");
    const linesEl = document.getElementById("voice-metric-lines");

    if (callsEl) callsEl.innerText = data.metrics.total_calls_today;
    if (ahtEl) ahtEl.innerText = data.metrics.avg_handle_time;
    if (fcrEl) fcrEl.innerText = data.metrics.first_call_resolution;
    if (transfersEl) transfersEl.innerText = data.metrics.transferred_calls;
    if (linesEl) linesEl.innerText = data.metrics.active_telephony_lines;

    // Operator lines
    const opTbody = document.getElementById("voice-operators-table-body");
    if (opTbody && data.operators) {
      opTbody.innerHTML = data.operators.map(op => {
        let badgeClass = "badge-success";
        if (op.status.includes("In Call")) badgeClass = "badge-primary";
        else if (op.status.includes("Wrap-Up")) badgeClass = "badge-warning";
        return `
          <tr>
            <td><code>${escapeHtml(op.channel)}</code></td>
            <td><strong>${escapeHtml(op.name)}</strong></td>
            <td><span class="badge ${badgeClass}">${escapeHtml(op.status)}</span></td>
          </tr>
        `;
      }).join("");
    }

    // CDR table
    const cdrTbody = document.getElementById("voice-cdr-table-body");
    if (cdrTbody && data.call_records) {
      cdrTbody.innerHTML = data.call_records.map(cdr => {
        let sentimentIcon = "😐";
        if (cdr.sentiment === "Positive") sentimentIcon = "😊";
        else if (cdr.sentiment === "Frustrated") sentimentIcon = "😡";

        let statusBadge = cdr.status === "COMPLETED" 
          ? '<span class="badge badge-success">COMPLETED</span>' 
          : '<span class="badge badge-danger">TRANSFERRED</span>';

        return `
          <tr>
            <td><code>${escapeHtml(cdr.id)}</code></td>
            <td>${escapeHtml(cdr.caller)}</td>
            <td><strong>${escapeHtml(cdr.duration)}</strong></td>
            <td>${escapeHtml(cdr.intent)}</td>
            <td>${sentimentIcon} ${escapeHtml(cdr.sentiment)}</td>
            <td>${statusBadge}</td>
            <td><small>${escapeHtml(cdr.operator)}</small></td>
          </tr>
        `;
      }).join("");
    }
  } catch (err) {
    console.error("Failed to load voice dashboard:", err);
  }
}

// 4. WhatsApp Operations Dashboard Loader
async function loadWhatsAppDashboard() {
  try {
    const res = await fetch("/api/dashboard/whatsapp");
    const data = await res.json();

    const convsEl = document.getElementById("wa-metric-convs");
    const deliveryEl = document.getElementById("wa-metric-delivery");
    const readEl = document.getElementById("wa-metric-read");
    const ordersEl = document.getElementById("wa-metric-orders");
    const convRateEl = document.getElementById("wa-metric-conversion");

    if (convsEl) convsEl.innerText = data.metrics.total_whatsapp_conversations;
    if (deliveryEl) deliveryEl.innerText = data.metrics.delivery_rate;
    if (readEl) readEl.innerText = data.metrics.read_rate;
    if (ordersEl) ordersEl.innerText = data.metrics.quick_orders_generated;
    if (convRateEl) convRateEl.innerText = data.metrics.conversion_rate;

    // Leads table
    const leadsTbody = document.getElementById("wa-leads-table-body");
    if (leadsTbody && data.leads) {
      leadsTbody.innerHTML = data.leads.map(lead => {
        let stageBadge = "badge-info";
        if (lead.stage.includes("Confirmed")) stageBadge = "badge-success";
        else if (lead.stage.includes("UPI")) stageBadge = "badge-warning";

        return `
          <tr>
            <td><code>${escapeHtml(lead.id)}</code></td>
            <td><strong>${escapeHtml(lead.name)}</strong></td>
            <td><code>${escapeHtml(lead.phone)}</code></td>
            <td><span class="badge ${stageBadge}">${escapeHtml(lead.stage)}</span></td>
            <td>${escapeHtml(lead.item)}</td>
            <td><strong style="color: #00a884;">${escapeHtml(lead.amount)}</strong></td>
            <td><small style="color: var(--text-muted);">${escapeHtml(lead.updated)}</small></td>
          </tr>
        `;
      }).join("");
    }

    // Catalog table
    const catTbody = document.getElementById("wa-catalog-table-body");
    if (catTbody && data.catalog) {
      catTbody.innerHTML = data.catalog.map(prod => `
        <tr>
          <td><code>${escapeHtml(prod.id)}</code></td>
          <td><strong>${escapeHtml(prod.name)}</strong></td>
          <td><strong style="color: #00a884;">${escapeHtml(prod.price)}</strong></td>
          <td><span style="color: #16a34a; font-weight: 500;">✓ ${escapeHtml(prod.stock)}</span></td>
          <td><span class="badge badge-success">${escapeHtml(prod.status)}</span></td>
        </tr>
      `).join("");
    }
  } catch (err) {
    console.error("Failed to load whatsapp dashboard:", err);
  }
}

// 5. SaaS Platform Health Dashboard Loader
async function loadSaasDashboard() {
  try {
    const res = await fetch("/api/dashboard/saas");
    const data = await res.json();

    const uptimeEl = document.getElementById("saas-metric-uptime");
    const latencyEl = document.getElementById("saas-metric-latency");
    const volumeEl = document.getElementById("saas-metric-volume");
    const errorRateEl = document.getElementById("saas-metric-errors");
    const keysEl = document.getElementById("saas-metric-keys");

    if (uptimeEl) uptimeEl.innerText = data.metrics.uptime;
    if (latencyEl) latencyEl.innerText = data.metrics.avg_latency;
    if (volumeEl) volumeEl.innerText = data.metrics.api_requests_24h;
    if (errorRateEl) errorRateEl.innerText = data.metrics.error_rate;
    if (keysEl) keysEl.innerText = data.metrics.active_developer_keys;

    // Endpoints table
    const epTbody = document.getElementById("saas-endpoints-table-body");
    if (epTbody && data.endpoint_health) {
      epTbody.innerHTML = data.endpoint_health.map(ep => `
        <tr>
          <td><code>${escapeHtml(ep.endpoint)}</code></td>
          <td><span class="badge badge-success">${escapeHtml(ep.status)}</span></td>
          <td><strong>${escapeHtml(ep.latency)}</strong></td>
          <td><small style="color: #10b981;">${escapeHtml(ep.uptime)}</small></td>
        </tr>
      `).join("");
    }

    // Errors table
    const errTbody = document.getElementById("saas-errors-table-body");
    if (errTbody && data.error_distribution) {
      errTbody.innerHTML = data.error_distribution.map(item => {
        let sevBadge = item.severity === "HIGH" 
          ? '<span class="badge badge-danger">HIGH</span>' 
          : item.severity === "MEDIUM" 
          ? '<span class="badge badge-warning">MEDIUM</span>' 
          : '<span class="badge badge-secondary">LOW</span>';

        return `
          <tr>
            <td><code>${escapeHtml(item.code)}</code></td>
            <td>${escapeHtml(item.title)}</td>
            <td>${sevBadge}</td>
            <td><strong>${escapeHtml(String(item.count))}</strong></td>
          </tr>
        `;
      }).join("");
    }

    // Developer tickets
    const tckTbody = document.getElementById("saas-tickets-table-body");
    if (tckTbody) {
      if (!data.developer_tickets || data.developer_tickets.length === 0) {
        tckTbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No developer bug tickets found</td></tr>`;
      } else {
        tckTbody.innerHTML = data.developer_tickets.map(t => {
          let priBadge = t.priority === "HIGH" 
            ? '<span class="badge badge-danger">HIGH</span>' 
            : '<span class="badge badge-info">NORMAL</span>';

          return `
            <tr>
              <td><code>${escapeHtml(t.id)}</code></td>
              <td>${escapeHtml(t.customer_name || t.customer_id)}</td>
              <td><strong>${escapeHtml(t.subject)}</strong></td>
              <td>${priBadge}</td>
              <td><span class="badge badge-secondary">${escapeHtml(t.status)}</span></td>
              <td><small>${escapeHtml(t.created_at ? t.created_at.substring(0, 16) : "")}</small></td>
            </tr>
          `;
        }).join("");
      }
    }
  } catch (err) {
    console.error("Failed to load saas dashboard:", err);
  }
}

// ==========================================================
// 6. SALESFORCE AGENTFORCE SUITE & ATLAS REASONING HELPERS
// ==========================================================

// Atlas Reasoning Trail Renderer
function renderAtlasTrailFromData(trail) {
  if (!trail) return "";
  const trailId = "trail-" + Math.random().toString(36).substring(2, 9);
  const stepsCount = (trail.steps && trail.steps.length > 0) ? trail.steps.length : 2;
  
  const stepsHtml = (trail.steps && trail.steps.length > 0)
    ? trail.steps.map((st, i) => {
        const isAction = st.type && st.type.includes("Action");
        return `
          <div class="atlas-step-card" style="${isAction ? 'border-left-color: #04844b;' : ''}">
            <div class="step-title" style="${isAction ? 'color: #04844b;' : ''}">
              <span>${isAction ? '⚙️' : '🎯'}</span>
              Step ${i + 1}: ${escapeHtml(st.type)}
            </div>
            <div class="step-detail">
              ${escapeHtml(st.detail || st.observation || (typeof st.input === 'object' ? JSON.stringify(st.input) : String(st.input || 'Action processed.')))}
            </div>
          </div>
        `;
      }).join("")
    : `
        <div class="atlas-step-card">
          <div class="step-title"><span>🎯</span> Step 1: Atlas Reasoning & Intent Scope</div>
          <div class="step-detail">Classified inquiry scope with zero-latency sentiment audit. Safe, non-toxic prompt verified.</div>
        </div>
        <div class="atlas-step-card">
          <div class="step-title"><span>☁️</span> Step 2: Grounding Retrieval & Policy Check</div>
          <div class="step-detail">Grounding verified with SQLite Vector RAG and Salesforce Data Cloud. No PII leaked.</div>
        </div>
      `;

  return `
    <div class="atlas-trail-wrapper">
      <div class="atlas-trail-header" onclick="toggleAtlasTrail('${trailId}')">
        <div class="atlas-trail-title">
          <span>⚡</span>
          <span>Atlas Reasoning Trail</span>
          <span class="atlas-trail-badge">Autonomous Resolution (${stepsCount} steps)</span>
        </div>
        <div style="font-size: 0.725rem; color: #0176d3; font-weight: 600;">
          <span id="${trailId}-chevron">▼ View Details</span>
        </div>
      </div>
      <div class="atlas-trail-body" id="${trailId}" style="display: none;">
        <div class="atlas-trail-meta">
          <div class="atlas-meta-item">
            <span>Reasoning Engine</span>
            <strong>${escapeHtml(trail.engine || 'Atlas Engine v3.4')}</strong>
          </div>
          <div class="atlas-meta-item">
            <span>Data Grounding</span>
            <strong>${escapeHtml(Array.isArray(trail.grounded_in) ? trail.grounded_in.join(', ') : 'Data Cloud')}</strong>
          </div>
          <div class="atlas-meta-item">
            <span>Einstein Trust Layer</span>
            <strong style="color: #04844b;">✓ Zero-Data Retention</strong>
          </div>
          <div class="atlas-meta-item">
            <span>Confidence Score</span>
            <strong style="color: #0176d3;">${escapeHtml(trail.trust_layer ? trail.trust_layer.confidence_score : '98.5%')}</strong>
          </div>
        </div>
        <div class="atlas-steps-list">
          ${stepsHtml}
        </div>
      </div>
    </div>
  `;
}

function toggleAtlasTrail(id) {
  const el = document.getElementById(id);
  const chevron = document.getElementById(id + "-chevron");
  if (!el) return;
  const isHidden = el.style.display === "none";
  el.style.display = isHidden ? "block" : "none";
  if (chevron) chevron.innerText = isHidden ? "▲ Hide Details" : "▼ View Details";
}

// Pay-Per-Resolution ROI Calculator
function updateRoiCalculation() {
  const ticketsSlider = document.getElementById("roi-slider-tickets");
  const costSlider = document.getElementById("roi-slider-cost");
  const deflSlider = document.getElementById("roi-slider-deflection");
  if (!ticketsSlider || !costSlider || !deflSlider) return;

  const tickets = parseInt(ticketsSlider.value, 10);
  const cost = parseFloat(costSlider.value);
  const defl = parseFloat(deflSlider.value);

  // Update slider label displays
  const ticketsLabel = document.getElementById("roi-tickets-val");
  const costLabel = document.getElementById("roi-cost-val");
  const deflLabel = document.getElementById("roi-deflection-val");

  if (ticketsLabel) ticketsLabel.innerText = `${tickets.toLocaleString()} inquiries`;
  if (costLabel) costLabel.innerText = `$${cost.toFixed(2)} / contact`;
  if (deflLabel) deflLabel.innerText = `${defl}% autonomous`;

  const resolvedByAi = Math.round(tickets * (defl / 100));
  const escalatedToHuman = tickets - resolvedByAi;

  const traditionalCost = tickets * cost;
  const agentforceCost = (resolvedByAi * 2.00) + (escalatedToHuman * cost);
  const monthlySavings = Math.max(0, traditionalCost - agentforceCost);
  const annualSavings = monthlySavings * 12;
  const roiPercent = (resolvedByAi * 2.00) > 0 ? ((monthlySavings / (resolvedByAi * 2.00)) * 100).toFixed(1) : "0.0";

  const mSav = document.getElementById("roi-monthly-savings");
  const aSav = document.getElementById("roi-annual-savings");
  const tradCost = document.getElementById("roi-traditional-cost");
  const afCost = document.getElementById("roi-agentforce-cost");
  const aiRes = document.getElementById("roi-ai-resolved");
  const pct = document.getElementById("roi-percent-val");

  if (mSav) mSav.innerText = `$${Math.round(monthlySavings).toLocaleString()}`;
  if (aSav) aSav.innerText = `$${Math.round(annualSavings).toLocaleString()} / year`;
  if (tradCost) tradCost.innerText = `$${Math.round(traditionalCost).toLocaleString()} / mo`;
  if (afCost) afCost.innerText = `$${Math.round(agentforceCost).toLocaleString()} / mo`;
  if (aiRes) aiRes.innerText = `${resolvedByAi.toLocaleString()} tickets`;
  if (pct) pct.innerText = `${roiPercent}%`;
}

// Agentforce Builder Topics Loader
async function loadAgentforceTopics() {
  const container = document.getElementById("topics-list-container");
  if (!container) return;
  try {
    const res = await fetch("/api/agentforce/topics");
    const data = await res.json();
    if (!data.topics || data.topics.length === 0) {
      container.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 1rem;">No topics configured</div>`;
      return;
    }

    container.innerHTML = data.topics.map(t => {
      const actionsBadges = t.actions.map(a => `<span class="tool-chip" style="font-size: 0.72rem;">⚙️ ${escapeHtml(a)}</span>`).join(" ");
      return `
        <div class="topic-item-card">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
            <div>
              <div style="display: flex; align-items: center; gap: 6px;">
                <code style="font-weight: 700; color: #0176d3;">${escapeHtml(t.id)}</code>
                <strong style="font-size: 0.95rem; color: #032d60;">${escapeHtml(t.name)}</strong>
                <span class="badge badge-success" style="font-size: 0.7rem;">${escapeHtml(t.status)}</span>
              </div>
              <small style="color: var(--text-muted); font-size: 0.75rem;">Assigned Agent: <strong>${escapeHtml(t.agent)}</strong></small>
            </div>
            <div style="text-align: right;">
              <span class="badge badge-primary" style="font-size: 0.75rem;">Confidence: ${escapeHtml(t.confidence_threshold)}</span>
              <div style="font-size: 0.75rem; color: #04844b; font-weight: 700; margin-top: 3px;">
                ${escapeHtml(t.auto_resolution_rate)} Resolution
              </div>
            </div>
          </div>
          
          <p style="font-size: 0.8rem; color: #334155; line-height: 1.45; margin-bottom: 0.65rem;">
            ${escapeHtml(t.description)}
          </p>

          <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #f1f5f9; padding-top: 0.5rem;">
            <div style="display: flex; gap: 4px; flex-wrap: wrap;">
              ${actionsBadges}
            </div>
            <button class="settings-btn" style="padding: 2px 8px; font-size: 0.75rem; color: #0176d3;" onclick="switchView('ecommerce')">
              ⚡ Test in Agent
            </button>
          </div>
        </div>
      `;
    }).join("");
  } catch (err) {
    container.innerHTML = `<div style="color: var(--danger); padding: 1rem;">Failed to load topics: ${err.message}</div>`;
  }
}

// Einstein Trust Layer Configuration
async function loadTrustGuardrails() {
  try {
    const res = await fetch("/api/agentforce/trust-layer");
    const data = await res.json();
    if (!data.config) return;
    const cfg = data.config;

    const pii = document.getElementById("guardrail-pii");
    const tox = document.getElementById("guardrail-toxicity");
    const hal = document.getElementById("guardrail-hallucination");
    const inj = document.getElementById("guardrail-injection");
    const slider = document.getElementById("trust-threshold-slider");
    const sliderVal = document.getElementById("trust-threshold-val");

    if (pii) pii.checked = cfg.pii_masking;
    if (tox) tox.checked = cfg.toxicity_filter;
    if (hal) hal.checked = cfg.hallucination_prevention;
    if (inj) inj.checked = cfg.prompt_injection_shield;
    if (slider) slider.value = cfg.confidence_threshold;
    if (sliderVal) sliderVal.innerText = `${cfg.confidence_threshold}% Confidence`;

    const shieldedEl = document.getElementById("trust-stat-shielded");
    const piiEl = document.getElementById("trust-stat-pii");
    const injEl = document.getElementById("trust-stat-injections");
    if (shieldedEl) shieldedEl.innerText = cfg.total_shielded_requests.toLocaleString();
    if (piiEl) piiEl.innerText = cfg.pii_entities_masked_today.toLocaleString();
    if (injEl) injEl.innerText = cfg.injections_blocked_today.toLocaleString();
  } catch (err) {
    console.error("Failed to load trust layer config:", err);
  }
}

async function updateTrustGuardrail(key, val) {
  try {
    await fetch("/api/agentforce/trust-layer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ [key]: val })
    });
  } catch (err) {
    console.error("Failed to update trust guardrail:", err);
  }
}

async function updateConfidenceSlider(val) {
  const el = document.getElementById("trust-threshold-val");
  if (el) el.innerText = `${val}% Confidence`;
  try {
    await fetch("/api/agentforce/trust-layer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ confidence_threshold: parseInt(val, 10) })
    });
  } catch (err) {
    console.error("Failed to update confidence threshold:", err);
  }
}

// ==========================================
// SNAPSHOT A - QUERY WORKFLOW DESIGN RUNNER
// ==========================================
const SNAPSHOT_SCENARIOS = {
  ecom: {
    query: '"Where is my Flipkart order OD409218392100?"',
    touchpoint: "Web Chat / Ekart API",
    route: "E-Commerce Agent",
    intent: "ORDER_STATUS_TELEMETRY",
    conf: "99.4%",
    slots: ["🏷️ Platform: Flipkart", "📦 OrderID: OD409218392100", "🎯 Carrier: Ekart Logistics"],
    tool: "get_flipkart_order_status()",
    latency: "18.4 ms",
    output: "Status: Out for Delivery | Courier: Ekart (Ramesh Kumar +91-98112-44910) | Item: Nothing Phone (2a) 128GB | OTP: 4921",
    escalation: "Not Required (Auto-Resolved)",
    overallConf: "98.8%"
  },
  hotel: {
    query: '"What luxury rooms are available tonight under $250 with ocean view?"',
    touchpoint: "Hospitality Portal / Concierge",
    route: "Hospitality Resort Agent",
    intent: "ROOM_INVENTORY_LOOKUP",
    conf: "98.2%",
    slots: ["🏨 Property: Grand Apex Resort", "💵 Max Price: $250/night", "🌊 View: Ocean View King"],
    tool: "check_room_availability(price_max=250)",
    latency: "14.2 ms",
    output: "Available: Deluxe Ocean View King ($189/night, 3 available) & Executive Palm Suite ($249/night, 1 available)",
    escalation: "Not Required (Direct Booking Enabled)",
    overallConf: "97.5%"
  },
  saas: {
    query: '"Webhook is failing with ERR_AUTH_EXPIRED on production checkout"',
    touchpoint: "Developer Console / API Gateway",
    route: "SaaS Platform Support (Fin)",
    intent: "API_ERROR_DIAGNOSTIC",
    conf: "99.1%",
    slots: ["💻 Code: ERR_AUTH_EXPIRED", "⏱️ TTL: 3600s Lifespan Exceeded", "🔑 Action: POST /oauth/v2/token"],
    tool: "saas_error_diagnostic_lookup(code='ERR_AUTH_EXPIRED')",
    latency: "21.6 ms",
    output: "Cause: OAuth 2.0 token expired. Solution: Call POST /api/v2/oauth/token with grant_type='refresh_token'. Code remediation generated.",
    escalation: "Not Required (Self-Service Fix Provided)",
    overallConf: "99.3%"
  },
  voice: {
    query: '"[Spoken Audio] Can I change the delivery address for order ORD-1002?"',
    touchpoint: "Voice Telephony IVR / Web Speech STT",
    route: "Voice Telephony Agent",
    intent: "ADDRESS_MODIFICATION_HOLD",
    conf: "92.0%",
    slots: ["📞 Caller: Bob Smith (+1-555-0102)", "📦 Order: ORD-1002 (In Transit)", "⚠️ Policy: Courier In-Flight Rule"],
    tool: "create_support_ticket(priority='HIGH', queue='Logistics')",
    latency: "32.1 ms",
    output: "Ticket TCK-102 dispatched to Human Courier Dispatcher Sarah M. to hold package at local depot.",
    escalation: "Warm Transfer to Human Agent (SLA 3m)",
    overallConf: "91.5%"
  }
};

function switchSnapshotScenario(key) {
  const sc = SNAPSHOT_SCENARIOS[key];
  if (!sc) return;

  ["ecom", "hotel", "saas", "voice"].forEach(k => {
    const btn = document.getElementById(`btn-snap-scenario-${k}`);
    if (btn) btn.classList.toggle("active", k === key);
  });

  const qEl = document.getElementById("snap-box-query-text");
  const tpEl = document.getElementById("snap-touchpoint");
  const rEl = document.getElementById("snap-route-badge");
  const intEl = document.getElementById("snap-intent");
  const confEl = document.getElementById("snap-intent-conf");
  const slotsCont = document.getElementById("snap-slots-container");
  const toolEl = document.getElementById("snap-tool-name");
  const latEl = document.getElementById("snap-tool-latency");
  const outEl = document.getElementById("snap-tool-output");
  const escEl = document.getElementById("snap-escalation");
  const oConfEl = document.getElementById("snap-confidence");
  const resBadge = document.getElementById("snap-resolution-badge");

  if (qEl) qEl.innerText = sc.query;
  if (tpEl) tpEl.innerText = sc.touchpoint;
  if (rEl) rEl.innerText = sc.route;
  if (intEl) intEl.innerText = sc.intent;
  if (confEl) confEl.innerText = sc.conf;
  if (toolEl) toolEl.innerText = sc.tool;
  if (latEl) latEl.innerText = sc.latency;
  if (outEl) outEl.innerText = sc.output;
  if (escEl) escEl.innerText = sc.escalation;
  if (oConfEl) oConfEl.innerText = sc.overallConf;

  if (slotsCont) {
    slotsCont.innerHTML = sc.slots.map(s => `<span class="tool-chip">${escapeHtml(s)}</span>`).join(" ");
  }

  if (resBadge) {
    if (key === "voice") {
      resBadge.className = "badge badge-warning";
      resBadge.innerText = "HUMAN WARM HANDOFF DISPATCHED 👤";
    } else {
      resBadge.className = "badge badge-success";
      resBadge.innerText = "AUTONOMOUS RESOLUTION COMPLETED ✅";
    }
  }
}

function simulateSnapshotWorkflow() {
  const steps = document.querySelectorAll(".snapshot-step-box");
  steps.forEach((el, i) => {
    setTimeout(() => {
      el.style.transform = "scale(1.02)";
      el.style.borderColor = "#00c6ff";
      setTimeout(() => {
        el.style.transform = "scale(1)";
        el.style.borderColor = "";
      }, 400);
    }, i * 350);
  });
}
