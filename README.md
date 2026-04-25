# 📄 InvoiceReader

> **Production-grade invoice extraction system** with self-correcting LangGraph pipeline, multi-LLM fallback, real-time streaming progress, and full role-based access control.

<p align="center">
  <a href="https://invoicereader.duckdns.org/">
    <img src="https://img.shields.io/badge/🚀_Live_Demo-Online-success?style=for-the-badge" alt="Live Demo" />
  </a>
  <a href="https://www.linkedin.com/in/leonardo-barretti/">
    <img src="https://img.shields.io/badge/LinkedIn-Leonardo_Barretti-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn" />
  </a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.109+-009688?style=flat&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/LangGraph-0.2+-1C3A5E?style=flat" />
  <img src="https://img.shields.io/badge/Pydantic-2.7+-E92063?style=flat&logo=pydantic&logoColor=white" />
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=flat&logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/TypeScript-5.8-3178C6?style=flat&logo=typescript&logoColor=white" />
  <img src="https://img.shields.io/badge/Tailwind-4.1-06B6D4?style=flat&logo=tailwindcss&logoColor=white" />
  <img src="https://img.shields.io/badge/Vite-6-646CFF?style=flat&logo=vite&logoColor=white" />
  <img src="https://img.shields.io/badge/Google_Gemini-Primary-4285F4?style=flat&logo=google&logoColor=white" />
  <img src="https://img.shields.io/badge/OpenAI-Fallback-412991?style=flat&logo=openai&logoColor=white" />
  <img src="https://img.shields.io/badge/Supabase-Database_+_Auth-3ECF8E?style=flat&logo=supabase&logoColor=white" />
  <img src="https://img.shields.io/badge/Tests-pytest-0A9EDC?style=flat&logo=pytest&logoColor=white" />
  <img src="https://img.shields.io/badge/Deploy-Hostinger_VPS-673AB7?style=flat" />
</p>

---

## 🎯 The Problem

Manual invoice processing is painful and expensive. Companies receive invoices in dozens of formats — PDFs, Word docs, plain text, scanned images — and someone has to read each one, copy the relevant fields (invoice number, date, total, vendor, line items), and paste them into spreadsheets or ERPs.

**Existing OCR tools are brittle:** they work on a specific layout, hallucinate when the format changes, have no way to validate their own output, and crash in production when the LLM provider has an outage.

## 💡 The Solution

InvoiceReader treats extraction as a **stateful, observable, self-correcting workflow** — not a single LLM call. Upload an invoice in any format and the system:

1. Routes the document to a cost-appropriate model based on complexity
2. Extracts structured fields using AI with **streaming progress events**
3. Validates the output against a strict Pydantic schema
4. **Self-corrects** failed fields with targeted retry prompts (no full re-extraction)
5. **Falls back** to a different LLM provider on quota errors or failures
6. Persists validated data to a normalized PostgreSQL schema
7. Lets users build custom column views, copy individual fields, or export to CSV

[**🌐 Try the live demo →**](https://invoicereader.duckdns.org/)

---

## ✨ Key Features

### Extraction Pipeline
- 📁 **Multi-format input** — PDF, DOCX, TXT, CSV, PNG, JPG/JPEG
- 🧠 **Multi-LLM strategy** — Gemini as primary, OpenAI as automatic fallback
- 🎯 **Cost-aware model routing** — `gemini_cheap` for simple docs, `gemini_expensive` for complex ones (images, long text)
- 🔁 **Targeted self-correction** — failed validations trigger surgical retries with field-specific prompts and document excerpts (not full re-extraction)
- ✅ **Schema-enforced output** — every AI response is validated against Pydantic models before being trusted
- 📡 **Real-time progress streaming** — Server-Sent Events (SSE) push pipeline state to the UI as each node runs

### Application Features
- 🔐 **Role-based access control** — admin/user roles with JWT validation on every endpoint
- 👥 **User management** — admin panel for creating, listing, and removing users
- 📊 **Customizable history view** — users select which of 30+ columns to display, with preferences persisted in `localStorage`
- 📤 **Flexible export** — copy by column, copy all visible data as TSV, or download CSV with proper UTF-8 BOM
- 🗑️ **Bulk operations** — multi-select and delete invoices safely with confirmation
- 🚀 **Production deploy** — running on Hostinger VPS with automated `git push` deployment

### Engineering Quality
- 🧪 **Comprehensive test suite** — pytest with fixtures, parametrized cases, and dedicated tests for schemas, nodes, graph routing, preprocessor, prompts, file processor, and security
- 📝 **Structured logging** — request-level logging middleware + named loggers per module
- 🛡️ **Security hardening** — file size limits, empty file detection, Bearer token enforcement, SQL injection protection, RLS on all Supabase tables
- 🔧 **Type safety end-to-end** — Pydantic on the backend, TypeScript on the frontend, shared interface contracts

---

## 🏗️ Architecture

The core differentiator of this project is **how** the extraction happens — not just *that* it happens.

### Why LangGraph instead of a single LLM call?

A direct call to Gemini or GPT-4 looks like this:

```
User upload → LLM call → "Trust the output" → Save
```

This is **brittle**. If the AI hallucinates a date format, forgets a tax ID, or hits a quota error, you get garbage in your database with no way to recover.

InvoiceReader uses LangGraph to manage extraction as a **stateful, decision-driven workflow**:

```
                    ┌──────────────────────┐
                    │   Document Upload    │
                    │  (PDF/DOCX/TXT/IMG)  │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Preprocess Document │
                    │  (clean + complexity)│
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │     Select Model     │
                    │  cheap / expensive   │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │      Extract         │ ◄────────┐
                    │   (Gemini/OpenAI)    │          │
                    └──────────┬───────────┘          │
                               │                      │
                    ┌──────────▼───────────┐          │
                    │     Validate         │          │
                    │  (Pydantic schema)   │          │
                    └──────────┬───────────┘          │
                               │                      │
                ┌──────────────┼──────────────┐       │
                │              │              │       │
        ✅ Valid         ⚠️ Field errors  ❌ API error│
                │              │              │       │
                ▼              ▼              ▼       │
         ┌──────────┐  ┌──────────────┐ ┌───────────┐ │
         │ Finalize │  │   Targeted   │ │ Fallback  │ │
         │ Success  │  │    Retry     │ │  Model    │─┘
         └──────────┘  │ (per-field)  │ │ (Gem→GPT) │
                      └──────┬───────┘ └───────────┘
                             │
                             └─► (back to Validate)
```

### Routing decisions (from `route_after_validate`)

| State                            | Decision         | Rationale                                                              |
|----------------------------------|------------------|------------------------------------------------------------------------|
| All fields valid ✅              | → finalize_success | Done. No retries needed.                                              |
| API error (429, quota, config)   | → fallback_model | Switch providers automatically — no manual intervention                |
| Field errors + retries available | → targeted_retry | Re-prompt only on failed fields with relevant document excerpt        |
| Retries exhausted, no fallback   | → fallback_model | Try a different LLM before giving up                                  |
| All paths exhausted              | → finalize_error | Fail loudly — never with bad data                                     |

This is the difference between a **demo** and a **production system**: demos trust the AI; production systems verify, retry, and gracefully degrade.

### Why targeted retry instead of full re-extraction

When validation fails on `supplier.name` and `totals.total_amount`, naive systems re-run the whole extraction. InvoiceReader extracts the **document excerpt most relevant to those failed fields** and sends a focused prompt asking only for corrections. This is faster, cheaper, and more accurate.

```python
# From backend/extraction/nodes.py
def targeted_retry_node(state: ExtractionState):
    failed_fields = state.get("failed_fields") or []
    # Find lines containing keywords from the failed field names
    relevant_lines = [
        line for line in cleaned_text.split("\n")
        if any(kw.lower() in line.lower() for kw in keywords)
    ]
    excerpt = "\n".join(relevant_lines)[:1500]
    prompt = build_targeted_retry_prompt(failed_fields, excerpt)
    # ...
```

### Why streaming progress (SSE) matters

Production AI systems need to feel **alive**, not frozen. The `/api/upload/stream` endpoint runs the LangGraph in a background thread and pushes progress events via Server-Sent Events:

```
data: {"type":"progress","step":"reading","detail":"Reading and parsing invoice file..."}
data: {"type":"progress","step":"sending_to_ai","detail":"gemini"}
data: {"type":"progress","step":"waiting_for_ai","detail":"gemini_cheap"}
data: {"type":"progress","step":"ai_failed","detail":"429 quota exceeded"}
data: {"type":"progress","step":"trying_new_ai","detail":"openai_cheap"}
data: {"type":"progress","step":"preparing_data","detail":"Structuring..."}
data: {"type":"result","data": {...full extracted invoice...}}
```

The React frontend reads this stream and animates a real-time pipeline visualization showing each step the agent takes — including fallback transitions when one LLM fails. This dramatically improves perceived reliability and gives users (and developers) real-time observability into the AI's decisions.

---

## 🛠️ Tech Stack

### Backend

| Component | Technology | Why |
|-----------|------------|-----|
| Language | **Python 3.11+** | Modern type hints, async support |
| API framework | **FastAPI** | Async, auto-validation, OpenAPI docs out of the box |
| LLM orchestration | **LangGraph 0.2+** | Stateful workflows with conditional routing |
| Validation | **Pydantic 2.7+** | Runtime schema enforcement at boundaries |
| Primary LLM | **Google Gemini** | `gemini-3-flash-preview`, fast and inexpensive |
| Fallback LLM | **OpenAI** | `gpt-4o-mini` / `gpt-4o`, automatic failover |
| Document parsing | **PyPDF2, python-docx, Pillow** | Multi-format file reading |
| Testing | **pytest** | Unit + integration + E2E + security tests |

### Frontend

| Component | Technology | Why |
|-----------|------------|-----|
| Framework | **React 19** | Latest stable with concurrent features |
| Language | **TypeScript 5.8** | Strict type safety end-to-end |
| Build tool | **Vite 6** | Fast HMR, optimized production builds |
| Styling | **Tailwind CSS 4.1** | Utility-first, oxide compiler |
| Routing | **React Router 7** | Latest data-router APIs |
| HTTP | **Axios** + **fetch (SSE)** | REST + Server-Sent Events for streaming |
| State | **React Context** | Auth state and admin role propagation |
| UI primitives | **lucide-react, react-dropzone, react-hot-toast** | Icons, drag-and-drop, notifications |

### Infrastructure

| Component | Technology | Why |
|-----------|------------|-----|
| Database | **Supabase (PostgreSQL)** | Managed Postgres + auth + RLS in one service |
| Auth | **Supabase Auth** | JWT-based, server-validated on every request |
| Hosting | **Hostinger VPS** | Cost-effective production hosting |
| CI/CD | **Git push → auto-deploy** | Direct VPS deployment on `main` branch push |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- A Supabase project ([supabase.com](https://supabase.com) — free tier is enough)
- API keys for Google Gemini and OpenAI

### Installation

```bash
# Clone the repository
git clone https://github.com/leopbar/InvoiceReader.git
cd InvoiceReader

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install
```

### Environment Variables

Create `backend/.env`:

```env
GOOGLE_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Create `frontend/.env`:

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_KEY=your_supabase_anon_key
VITE_API_URL=http://localhost:8000/api
```

### Database Setup

Run the SQL schema in your Supabase SQL editor (creates tables for `suppliers`, `invoices`, `invoice_items`, `invoice_addresses`, and `user_roles` with Row Level Security enabled). The full schema is in `backend/setup_db.sql`.

### Create the first admin user

```bash
cd backend
python create_admin.py
```

### Run the application

**Option 1: Single command (recommended)**
```bash
./start.sh
```

**Option 2: Run services separately**
```bash
# Terminal 1 — Backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Auto-generated API docs (dev only): `http://localhost:8000/docs`

---

## 🧪 Testing

The repository includes a comprehensive test suite covering schemas, graph logic, file processing, prompts, and security.

```bash
cd backend
pytest                              # Run all unit tests
pytest tests/test_schemas.py -v     # Pydantic validation tests
pytest tests/test_graph_routing.py  # LangGraph routing logic
pytest tests/test_nodes.py          # Individual graph nodes
pytest tests/test_preprocessor.py   # Text cleanup + complexity routing
pytest tests/test_file_processor.py # File reading + base64 encoding
pytest tests/test_prompts.py        # Prompt templates
```

### E2E and integration tests

```bash
# Multi-format upload integration test (requires running server)
python tests/test_multiformat_upload.py

# Full E2E test (upload → extract → save → verify)
python tests/test_upload_e2e.py

# Security boundary tests (auth, file size, SQL injection)
python tests/test_security_api.py
```

---

## 📚 Project Structure

```
InvoiceReader/
├── backend/
│   ├── extraction/                 # LangGraph extraction pipeline
│   │   ├── graph.py                # Workflow definition + routing logic
│   │   ├── nodes.py                # Individual graph nodes
│   │   ├── state.py                # TypedDict state contract
│   │   ├── schemas.py              # Pydantic models (Invoice, etc.)
│   │   ├── llm_clients.py          # Gemini / OpenAI client factory
│   │   ├── preprocessor.py         # Text cleanup + complexity heuristics
│   │   └── prompts.py              # Extraction + targeted retry prompts
│   ├── tests/                      # pytest test suite
│   ├── main.py                     # FastAPI app + endpoints
│   ├── database.py                 # Supabase client setup
│   ├── file_processor.py           # PDF/DOCX/image/text parsing
│   ├── supabase_service.py         # DB persistence (suppliers, invoices, items)
│   ├── setup_db.sql                # Schema migration for Supabase
│   ├── create_admin.py             # Bootstrap initial admin user
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/                  # UploadPage, HistoryPage, etc.
│   │   ├── components/             # ExtractedDataDisplay, etc.
│   │   ├── context/                # AuthContext (session + admin role)
│   │   ├── services/               # api.ts (axios + SSE), supabase.ts
│   │   ├── App.tsx                 # Routes + layout
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── start.sh                        # One-command startup
├── package.json                    # npm workspaces root
└── README.md
```

---

## 🔐 Security Considerations

This project applies several production security practices:

- **JWT validation on every protected endpoint** via `Depends(verify_token)`
- **Admin-only endpoints** double-check role membership in `user_roles` table
- **Service-role Supabase client** is server-only and never exposed to the frontend
- **Row Level Security (RLS)** enabled on every Supabase table
- **File size limit** (10 MB) and empty-file rejection on upload
- **Bearer token format enforced** — rejects Basic auth and missing headers
- **Cannot delete yourself** — admin user deletion guard
- **Production mode disables `/docs` and `/redoc`** to reduce attack surface

> ⚠️ **Note on initial development:** the SQL schema currently uses permissive RLS policies (`USING (true)`) for rapid iteration. Production deployments should tighten these to per-user policies (e.g., `USING (auth.uid() = user_id)`).

---

## 🛣️ Roadmap

- [ ] Per-user RLS policies on invoices and suppliers
- [ ] Langfuse integration for full LLM observability and cost tracking
- [ ] Quality metrics dashboard (per-field accuracy, retry rate, fallback frequency)
- [ ] Batch upload with parallel pipeline execution
- [ ] Golden invoice dataset + automated regression suite
- [ ] Multi-language invoice support (currently English-optimized)
- [ ] Webhook integration for ERP/accounting systems
- [ ] Confidence scores per extracted field (not just pass/fail)

---

## 🤔 What I Learned Building This

A few specific takeaways from building a real production AI system:

- **Pydantic at the boundary is the cheapest insurance.** Every malformed LLM response caught is a bug that never reached the database.
- **State machines beat chains for non-trivial AI flows.** LangGraph's conditional edges make retry and fallback logic explicit and debuggable; the equivalent in plain LangChain becomes a maze of nested `if`s.
- **Targeted retries are an order of magnitude cheaper than full re-extraction.** Sending only the failed fields + relevant document excerpt back to the LLM costs a fraction of running the full prompt again.
- **Multi-provider strategies aren't premature optimization.** Both Gemini and OpenAI had outages during development. Auto-fallback turned downtime into a transparent recovery — users never noticed.
- **Streaming progress changes UX dramatically.** The same pipeline feels twice as fast when users can *see* it working, even if total latency is identical.
- **Type safety end-to-end pays for itself.** Pydantic on the server + TypeScript on the client meant zero "field doesn't exist" bugs in production.

---

## 👤 About the Author

**Leonardo Barretti**

Building production AI systems with Python, focusing on robust LLM integration, agentic workflows, and clean engineering practices.

- 💼 **LinkedIn:** [linkedin.com/in/leonardo-barretti](https://www.linkedin.com/in/leonardo-barretti/)
- 🐙 **GitHub:** [@leopbar](https://github.com/leopbar)

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <em>If this project taught you something or sparked an idea, consider giving it a ⭐ — it helps other developers discover it.</em>
</p>
