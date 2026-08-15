# 🩺 Clinexa — Multi-Agent AI Healthcare-Intelligence Platform

**Clinexa** is an end-to-end multi-agent AI healthcare platform designed for processing, analyzing, and explaining medical lab reports with strict medical safety guardrails, deterministic parameter classification, and hybrid RAG search.

---

## ✨ Key Features

- **📄 Document Processing Pipeline**: Extracts selectable PDF text via PDFPlumber, falls back to PyMuPDF page rasterization and Tesseract/PaddleOCR for scanned documents.
- **⚙️ Deterministic Rule Engine**: Algorithmic parameter classification (`NORMAL`, `HIGH`, `LOW`, `UNKNOWN`). **LLMs never decide lab status** — they only explain statuses computed by the rule engine.
- **🔍 Hybrid RAG Engine**: Combines 384-dimensional vector embeddings (sentence-transformers `all-MiniLM-L6-v2`) with PostgreSQL full-text search via **Reciprocal Rank Fusion (RRF)** reranking.
- **🤖 Multi-Agent System**:
  - `SafetyAgent`: Detects red-flag emergency symptoms and enforces mandatory disclaimers.
  - `AnalysisAgent`: Formulates patient-friendly explanations of lab parameters.
  - `TrendAgent`: Tracks time-series trajectories (increasing, decreasing, stable) using linear regression slope analysis.
  - `ResponseAgent`: Formulates synthesized, empathetic responses with source citations.
  - `Orchestrator`: LangGraph / state-machine intent routing.
- **🎨 Modern Dark Glassmorphic Frontend**: Next.js 14 App Router, Tailwind CSS, Recharts, Lucide Icons, and Supabase Authentication.

---

## 🛠️ Architecture Overview

```
Clinexa Architecture
├── 🗄️ Database: PostgreSQL (Supabase) + RLS Policies + pgvector + FTS
├── ⚙️ Rule Engine: Pure-Python range classifier (unit compatibility check)
├── 📄 Ingestion: PDFPlumber + PyMuPDF + Tesseract OCR
├── 🔍 Hybrid RAG: pgvector cosine + Postgres tsvector + RRF Reranker
├── 🤖 Agent Framework: Orchestrator + Safety + Analysis + Trend + Response Agents
├── 🌐 Backend API: FastAPI + Pydantic v2 + BackgroundTasks
└── 🎨 Frontend UI: Next.js 14 + Tailwind CSS + Recharts + Supabase Auth
```

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+
- Node.js 18+
- (Optional) Docker & Docker Desktop

### 1. Set Up Environment Variables

Create `backend/.env`:
```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
DATABASE_URL=postgresql+asyncpg://postgres:password@db.your-project-ref.supabase.co:5432/postgres

GROQ_API_KEY=gsk_your_groq_api_key
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=your-jwt-secret-key
OCR_ENGINE=tesseract
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
ENVIRONMENT=development
LOG_LEVEL=INFO
ALLOWED_ORIGINS=["http://localhost:3000"]
```

Create `frontend/.env.local`:
```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project-ref.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 2. Database Migration

Run the SQL migration in your Supabase SQL Editor:
- 📄 [001_initial_schema.sql](file:///c:/Users/arkap/Desktop/Clinexa/backend/app/db/migrations/001_initial_schema.sql)

### 3. Run Locally

#### Option A: Native Development Servers

**Terminal 1 — Backend (FastAPI)**:
```powershell
$env:PYTHONPATH="backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 — Frontend (Next.js)**:
```powershell
cd frontend
npm run dev
```

- **Frontend App**: `http://localhost:3000`
- **FastAPI Interactive Docs**: `http://127.0.0.1:8000/docs`

#### Option B: Docker Compose
```bash
docker compose up --build
```

---

## 🧪 Running the Test Suite

Run the full test suite (114+ tests covering Rule Engine, PDF Parser, OCR, Extractor, Hybrid RAG, Safety, Agents, Trends, Evaluation):

```powershell
$env:PYTHONPATH="backend"
python -m pytest tests/ -v
```

---

## 🔒 Security & Medical Compliance

- **Row Level Security (RLS)**: Enforced across all 8 PostgreSQL tables using `auth.uid()`.
- **Medical Emergency Notice**: Any query indicating acute medical risk (e.g. chest pain, stroke, self-harm) immediately overrides with emergency contact numbers and short-circuits execution.
- **Mandatory Disclaimers**: Educational medical disclaimers are automatically appended to all informational AI responses.
