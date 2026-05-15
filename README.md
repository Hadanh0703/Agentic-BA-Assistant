# 🤖 AI-BA Assistant — Multi-Agent Project Management System

> An intelligent Business Analyst assistant powered by a 5-agent pipeline with RAG, self-correction loop, and Jira Cloud integration.

**🔗 Live Demo:** [agentic-ba-assistant-k3ih.vercel.app](https://agentic-ba-assistant-k3ih.vercel.app)

---

## ✨ Key Features

- **Multi-Agent Pipeline** — 5 specialized agents working in sequence: Interviewer → Standardizer → Architect → Risk Observer → Orchestrator
- **Self-Correction Loop** — Risk Observer automatically detects oversized tasks (≥8 SP) and triggers Architect to re-decompose
- **RAG System** — Upload project documents (PDF), AI grounds responses in your actual tech stack and business rules
- **Human-in-the-Loop** — Review and edit User Stories before task decomposition proceeds
- **Jira Cloud Integration** — Auto-export Stories, Tasks, Story Points, and Sprint assignment to Jira
- **Real-time Streaming** — WebSocket delivers live agent status updates ("Agent X is thinking...")
- **Google OAuth** — Per-user data isolation, each user manages their own projects independently
- **Hybrid AI Mode** — Intent classification routes between general chat and business pipeline

---

## 🏗️ System Architecture

```
User Input
    ↓
Intent Classifier ──→ General Chat (direct LLM response)
    ↓ (business intent)
Interviewer Agent   ──→ Clarifies WHO / WHAT / WHY
    ↓
Standardizer Agent  ──→ Generates Agile User Story + Acceptance Criteria
    ↓
[Human-in-the-Loop] ──→ User reviews and confirms User Story
    ↓
Architect Agent     ──→ RAG-powered technical task decomposition [FE/BE/DB]
    ↓
Risk Observer       ──→ Validates task quality, triggers retry if issues found
    ↓                    (self-correction loop, max 2 retries)
Orchestrator        ──→ Coordinates full pipeline, manages state
    ↓
Jira Cloud Export   ──→ Stories + Tasks + Story Points + Sprint auto-assignment
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 16 (App Router), TypeScript, Tailwind CSS |
| **Backend** | FastAPI, Python, SQLAlchemy |
| **AI/LLM** | LangChain, Groq (Llama 3.3 70B), Prompt Engineering |
| **RAG** | ChromaDB, FastEmbed (BAAI/bge-small-en-v1.5) |
| **Database** | PostgreSQL (production), SQLite (development) |
| **Real-time** | WebSocket |
| **Auth** | NextAuth v5, Google OAuth |
| **Integration** | Jira Cloud REST API, Jira Agile API |
| **Deploy** | Vercel (Frontend), Railway (Backend + PostgreSQL) |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Groq API Key ([console.groq.com](https://console.groq.com))

### Backend Setup

```bash
cd backend
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Fill in your API keys

uvicorn server:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install

# Create .env.local file
cp .env.local.example .env.local
# Fill in your credentials

npm run dev
```

### Environment Variables

**Backend `.env`:**
```env
GROQ_API_KEY=your_groq_api_key
JIRA_SITE_URL=https://yourcompany.atlassian.net
JIRA_USER_EMAIL=your@email.com
JIRA_API_TOKEN=your_jira_token
JIRA_PROJECT_KEY=SCRUM
```

**Frontend `.env.local`:**
```env
AUTH_SECRET=your_nextauth_secret
AUTH_GOOGLE_ID=your_google_client_id
AUTH_GOOGLE_SECRET=your_google_client_secret
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 📁 Project Structure

```
Agentic-BA-Assistant/
├── backend/
│   ├── agents/
│   │   ├── interviewer.py      # WHO/WHAT/WHY clarification
│   │   ├── standardizer.py     # Agile User Story generation
│   │   ├── architect.py        # RAG-powered task decomposition
│   │   ├── risk_observer.py    # Quality validation + self-correction
│   │   └── orchestrator.py     # Pipeline coordination + intent classification
│   ├── services/
│   │   ├── chat_service.py
│   │   ├── project_service.py
│   │   └── websocket_manager.py
│   ├── models.py               # SQLAlchemy DB models
│   ├── schema.py               # Pydantic schemas
│   ├── ingest_data.py          # RAG pipeline (ChromaDB + FastEmbed)
│   └── server.py               # FastAPI application
└── frontend/
    ├── app/                    # Next.js App Router pages
    ├── components/             # UI components
    │   ├── ChatWindow.tsx
    │   ├── TaskWorkspace.tsx
    │   ├── UserStoryConfirm.tsx
    │   └── Sidebar.tsx
    ├── hooks/                  # Custom React hooks
    │   ├── useChat.ts
    │   ├── useProjects.ts
    │   └── useWebSocket.ts
    └── lib/
        └── api.ts              # Axios API client
```

---

## 🔄 How It Works

1. **Describe your feature** — Type a requirement in natural language
2. **AI clarifies** — Interviewer Agent asks 1 targeted question if needed (WHO/WHAT/WHY)
3. **User Story generated** — Standardizer creates Agile-compliant User Story with Acceptance Criteria
4. **Review & confirm** — Human-in-the-loop: edit before proceeding
5. **Task decomposition** — Architect Agent uses RAG to generate technical tasks grounded in your project documents
6. **Quality check** — Risk Observer validates tasks, triggers self-correction if any task exceeds 8 Story Points
7. **Export to Jira** — One click exports everything to Jira Cloud with Sprint auto-creation

---

## 📊 Agent Details

| Agent | Role | Key Behavior |
|---|---|---|
| **Interviewer** | BA Analyst | Extracts WHO/WHAT/WHY, max 1 clarifying question, anti-loop logic |
| **Standardizer** | Story Writer | Converts requirements to Agile User Story + Acceptance Criteria |
| **Architect** | Solution Architect | RAG-powered task decomposition into [FE], [BE], [DB] layers |
| **Risk Observer** | QA Manager | Validates SP limits, layer balance, task description quality |
| **Orchestrator** | Conductor | Intent classification, pipeline coordination, self-correction loop |

---

## 🌐 Deployment

| Service | Platform | URL |
|---|---|---|
| Frontend | Vercel | [agentic-ba-assistant-k3ih.vercel.app](https://agentic-ba-assistant-k3ih.vercel.app) |
| Backend | Railway | agentic-ba-assistant-production.up.railway.app |
| Database | Railway PostgreSQL | Auto-managed |

---

## 👨‍💻 Author

**Hà Đức Anh** — Third-year CS Student at HUST

- GitHub: [@Hadanh0703](https://github.com/Hadanh0703)
- LinkedIn: [hadanhne](https://www.linkedin.com/in/hadanhne/)
- Email: ducanhhayb2005@gmail.com
