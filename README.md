# ApexTech AI Agent-Based Customer Support System

An enterprise-ready, autonomous AI Customer Support system featuring **Multi-Tool ReAct Agent Reasoning**, **Retrieval-Augmented Generation (RAG) with Vector Search**, a **Relational SQLite CRM & Knowledge Store**, and a **Dual-View Web Interface (Customer Support Portal & Admin CRM Dashboard)**.

---

## 🌟 Key Highlights

- **Autonomous ReAct Agent Core**:
  - Implements the **Reasoning + Acting (ReAct)** pattern (`Thought -> Action -> Observation -> Final Answer`).
  - Equipped with 5 operational tools:
    1. `search_knowledge_base(query)`: RAG tool querying company policy documents.
    2. `check_order_status(order_id)`: Fetches real-time shipping carrier tracking and status.
    3. `process_refund_return(order_id, reason)`: Validates 30-day return policy and generates RMA return authorizations.
    4. `create_support_ticket(subject, description, priority)`: Creates persistent customer issues.
    5. `escalate_to_human(reason, priority)`: Escalates unresolved or sensitive issues into the Tier-2 human queue.
- **RAG & Vector Retrieval Engine**:
  - Semantic vector search with cosine similarity and subword n-gram fuzzy matching.
  - Chunking and metadata filtering with zero heavy C++ dependency constraints.
  - Pre-seeded with company policies on returns, shipping, warranties, and account security.
- **Pluggable Multi-LLM Provider Architecture**:
  - **Built-in Autonomous Engine (Demo Mode)**: Works out-of-the-box immediately without requiring an API key.
  - **Google Gemini**: Gemini 2.5 / 2.0 Flash support via REST/SSE.
  - **OpenAI**: GPT-4o / GPT-4o-mini support.
  - **Groq Cloud**: Ultra-fast Llama 3.3 70B inference.
  - **Local Ollama**: Offline LLM serving on `http://localhost:11434`.
  - Dynamic runtime switching right from the Web UI Settings panel!
- **Dual-View Responsive Web Application**:
  - **Customer Chat Portal**: Real-time streaming responses, interactive agent thinking & tool execution chips, suggested quick prompts, and sample IDs helper.
  - **Support Agent & Admin CRM**: Real-time ticket queue with status badges (`OPEN`, `ESCALATED`, `IN_PROGRESS`, `RESOLVED`), knowledge base manager with interactive vector search tester, and customer order database.

---

## 🏛️ System Architecture

```
+---------------------------------------------------------------------------------------+
|                                    FRONTEND LAYER                                     |
|  +---------------------------------------------+  +--------------------------------+  |
|  |       Customer Interactive Support Widget   |  |   Human Agent / Admin Dashboard|  |
|  | - Chat messages (User / Bot / Tool actions) |  | - Live Ticket Queue & Status   |  |
|  | - Real-time agent thought streaming         |  | - KB Document Management       |  |
|  | - Order lookup / Refund request UI cards    |  | - System Analytics & Metrics   |  |
|  | - Escalation notification pill & banner     |  | - LLM & Vector Store Config    |  |
|  +---------------------------------------------+  +--------------------------------+  |
+-------------------------------------------|-------------------------------------------+
                                            | REST API / SSE Streams
+-------------------------------------------v-------------------------------------------+
|                                BACKEND APPLICATION (FLASK)                            |
|                                                                                       |
|  [routes/api.py]                                                                      |
|   - /api/chat & /api/chat/stream  -> Message streaming & Agent execution loop         |
|   - /api/tickets                  -> CRUD support tickets & human escalations        |
|   - /api/knowledge                -> Upload, index & semantic search documents        |
|   - /api/orders                   -> Mock e-commerce order verification               |
|   - /api/settings                 -> Configure LLMs, models, fallback modes           |
|                                                                                       |
|  [agent/support_agent.py] (ReAct Agent Engine)                                        |
|   - Autonomous Reasoning Cycle: Thought -> Action -> Observation -> Final Answer      |
|   - Multi-tool coordination & safety checks                                           |
|   - Intent detection & sentiment classification                                       |
|   - Automated fallback to Human Agent Escalation when confidence is low or requested  |
|                                                                                       |
|  [agent/tools.py]                                                                     |
|   1. search_knowledge_base: RAG tool querying vector store for policies/troubleshooting|
|   2. check_order_status: Looks up order details (status, items, tracking)             |
|   3. create_support_ticket: Opens support ticket in DB with priority & issue tag       |
|   4. process_refund_return: Verifies 30-day policy, checks order status, issues refund|
|   5. escalate_to_human: Marks ticket as ESCALATED, assigns to queue, alerts admin     |
|                                                                                       |
|  [rag/vector_store.py & rag/embeddings.py]                                            |
|   - Hybrid Vector Search Engine:                                                      |
|     * Semantic dense vectors (OpenAI, Gemini, or local FastText-style vector store)   |
|     * Chunking & text preprocessing with metadata (title, category, source)           |
|     * Persistent storage in SQLite / JSON vector store                                |
|                                                                                       |
|  [llm/factory.py] (Pluggable Multi-LLM Adapter)                                       |
|   - Demo Provider (Zero-config offline testing)                                       |
|   - Gemini Provider, OpenAI Provider, Groq Provider, Ollama Provider                  |
|                                                                                       |
|  [database/db.py & database/seed_data.py]                                             |
|   - SQLite Database (schema):                                                         |
|     * customers: id, name, email, tier, created_at                                    |
|     * orders: id, customer_id, items, total, status, tracking_no, date                |
|     * tickets: id, customer_id, subject, status, priority, resolution_notes           |
|     * chat_messages: id, session_id, role, content, tool_calls, timestamp             |
|     * knowledge_documents: id, title, content, category, embedding                    |
+---------------------------------------------------------------------------------------+
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ (Tested up to Python 3.14)
- Git

### 2. Installation
Clone the repository and install the dependencies:
```bash
git clone <your-repo-url>
cd "AI AGENT-RAG PROJECT"
python -m pip install -r requirements.txt
```

### 3. Run the Application
Launch the server with a single command:
```bash
python run.py
```
Open your browser and navigate to:
👉 **`http://127.0.0.1:5000`**

The application automatically seeds the database with realistic sample customers, orders, tickets, and policies upon first launch.

---

## 🧪 Sample Demonstration Scenarios

Try typing or clicking the quick prompts on the customer chat page:

| Scenario | Input Query | Expected Agent Behavior |
| :--- | :--- | :--- |
| **Order Tracking** | *"Where is my order ORD-1002?"* | Invokes `check_order_status`, reports that Bob Smith's Mechanical Keyboard is in transit via UPS with tracking `UPS-9941235` arriving tomorrow. |
| **Return Policy RAG** | *"What is your 30-day return policy?"* | Invokes `search_knowledge_base`, cites exact 30-day calendar policy, return shipping rules, and refund turnaround (3-5 business days). |
| **Refund Request** | *"I want to return order ORD-1001 for a refund"* | Invokes `process_refund_return`, verifies within 30 days, generates Return ID `RET-XXXXXX`, and marks order status as *Return Initiated*. |
| **Expired Return Check** | *"Can I return order ORD-1003?"* | Checks policy, identifies order was delivered over 45 days ago, denies standard return but informs customer of their active 1-Year Manufacturer Warranty. |
| **Human Escalation** | *"I need to speak with a human representative"* | Invokes `escalate_to_human`, assigns ticket `ESC-XXXXXX` to the Tier-2 human queue, and alerts admin dashboard. |

---

## ⚙️ Configuring LLMs & API Keys

You can configure models either in `.env` or interactively at runtime in the **Settings** modal in the top-right corner of the web interface:

### `.env` File Options
```env
# Choose provider: "demo", "gemini", "openai", "groq", or "ollama"
DEFAULT_LLM_PROVIDER=demo

# Google Gemini
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash

# OpenAI
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini

# Groq
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile

# Ollama (Local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3:8b
```

---

## 📡 REST API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/health` | `GET` | Health check & active system status |
| `/api/chat` | `POST` | Synchronous ReAct chat (`{message, session_id}`) |
| `/api/chat/stream` | `POST` | Server-Sent Events (SSE) streaming chat endpoint |
| `/api/chat/history/<session_id>` | `GET` | Retrieves full chat message log for a session |
| `/api/chat/session/<session_id>` | `DELETE` | Clears conversation history for a session |
| `/api/tickets` | `GET`, `POST` | List and create support tickets |
| `/api/tickets/<ticket_id>` | `PATCH`, `DELETE` | Update ticket status (`OPEN`, `ESCALATED`, `RESOLVED`) |
| `/api/orders` | `GET` | List customer orders and delivery statuses |
| `/api/knowledge` | `GET`, `POST` | List and add indexed RAG knowledge articles |
| `/api/knowledge/search` | `POST` | Test semantic vector retrieval (`{query, top_k}`) |
| `/api/settings` | `GET`, `POST` | View and dynamically switch LLM provider and API keys |

---

## 🧪 Automated Testing

Execute the automated test suite covering vector embeddings, ReAct tools, agent loops, and REST endpoints:
```bash
python -m unittest discover -s tests -p "test_*.py"
```
All 14 unit and integration tests run in under 1 second.

---

## 📂 Repository Structure

```
.
├── backend/
│   ├── agent/                 # ReAct Agent logic, tools, and prompts
│   │   ├── prompts.py
│   │   ├── support_agent.py
│   │   └── tools.py
│   ├── database/              # SQLite manager, models, and seed data
│   │   ├── db.py
│   │   ├── models.py
│   │   └── seed_data.py
│   ├── llm/                   # Pluggable LLM interfaces (Gemini, OpenAI, Groq, Ollama, Demo)
│   │   ├── base.py
│   │   ├── demo_provider.py
│   │   ├── factory.py
│   │   ├── gemini_provider.py
│   │   ├── groq_provider.py
│   │   ├── ollama_provider.py
│   │   └── openai_provider.py
│   ├── rag/                   # Vector embeddings, chunking, and similarity search
│   │   ├── default_knowledge.py
│   │   ├── embeddings.py
│   │   └── vector_store.py
│   ├── routes/                # Flask Blueprints (Chat, Tickets, Orders, Knowledge, Settings)
│   │   ├── chat_routes.py
│   │   ├── knowledge_routes.py
│   │   ├── order_routes.py
│   │   ├── settings_routes.py
│   │   └── ticket_routes.py
│   ├── app.py                 # Flask server factory
│   └── config.py              # Environment configuration
│
├── frontend/                  # React modular source code
│   ├── src/
│   │   ├── components/
│   │   │   ├── AdminDashboard.jsx
│   │   │   └── ChatWidget.jsx
│   │   ├── App.jsx
│   └── package.json
│
├── static/                    # Zero-compile client served directly by Flask
│   ├── css/style.css
│   ├── js/app.js
│   └── index.html
│
├── tests/                     # Test suite
│   ├── test_agent.py
│   ├── test_api.py
│   └── test_rag.py
│
├── .env.example
├── .gitignore
├── requirements.txt
├── run.py                     # Root entry point
└── README.md
```

---

## 📄 License
MIT License. Free for open-source and commercial customer support development.
