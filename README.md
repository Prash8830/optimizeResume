# OptimizeResume

**AI-powered resume optimizer that tailors your resume to any job description — automatically, honestly, and at ATS-beating quality.**

---

## The Problem

Job applicants lose out not because they lack skills, but because their resume fails the ATS (Applicant Tracking System) scan. The core issue:

- Every JD is different — even for the same role across companies
- You can't manually rewrite your resume for every application
- ATS score = `relevant_keywords / total_words` — you need to maximize this ratio
- Cramming all keywords is dishonest and fails at interview stage

## The Solution

OptimizeResume maintains a **Master Profile** — your complete, truthful experience database. For each job application:

1. You paste the JD
2. An agentic pipeline selects the most relevant subset of your experience
3. Rewrites it using the JD's exact language (without fabricating anything)
4. Validates ATS score and iterates until it passes threshold
5. Delivers a one-page, ATS-safe, downloadable resume

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend (V1) | Streamlit |
| Frontend (V2) | React + TypeScript + TailwindCSS |
| Backend | Python FastAPI (async) |
| Agentic Framework | LangGraph |
| LLM | Google Gemini 2.0 Flash (free tier) |
| Embeddings | Google text-embedding-004 (free) |
| Vector Store | ChromaDB (embedded) |
| Primary DB | PostgreSQL (via SQLAlchemy async) |
| Hybrid Search | ChromaDB cosine + BM25 (rank_bm25) |
| PDF Export | WeasyPrint |
| DOCX Export | python-docx |
| Containerization | Docker + docker-compose |

---

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL running locally or via Docker
- Google AI API key (free at [aistudio.google.com](https://aistudio.google.com))

### 1. Clone and setup
```bash
git clone https://github.com/Prash8830/optimizeResume.git
cd optimizeResume
cp .env.example .env
# Fill in your GEMINI_API_KEY and DATABASE_URL in .env
```

### 2. Run with Docker (recommended)
```bash
docker-compose up --build
```
- Streamlit UI: http://localhost:8501
- FastAPI docs: http://localhost:8000/docs

### 3. Run manually
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

---

## Project Structure

```
optimizeResume/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI app entry point
│   │   ├── api/routes/
│   │   │   ├── auth.py           # JWT authentication
│   │   │   ├── profile.py        # Master profile CRUD
│   │   │   ├── resume.py         # Pipeline trigger + SSE streaming
│   │   │   └── export.py         # PDF / DOCX download
│   │   ├── agents/
│   │   │   ├── graph.py          # LangGraph StateGraph definition
│   │   │   ├── state.py          # ResumeState TypedDict
│   │   │   ├── jd_analyzer.py    # Node 1: JD keyword extraction
│   │   │   ├── profile_scorer.py # Node 2: hybrid relevance scoring
│   │   │   ├── content_selector.py # Node 3: knapsack selection
│   │   │   ├── resume_writer.py  # Node 4: grounded rewrite
│   │   │   ├── ats_checker.py    # Node 5: ATS validation + loop
│   │   │   └── report_gen.py     # Node 6: optimization report
│   │   ├── models/
│   │   │   ├── user.py           # SQLAlchemy User model
│   │   │   ├── profile.py        # SQLAlchemy + Pydantic profile schemas
│   │   │   └── resume.py         # Resume version model
│   │   ├── storage/
│   │   │   ├── database.py       # Async PostgreSQL engine + session
│   │   │   ├── vector_store.py   # ChromaDB wrapper
│   │   │   ├── bm25.py           # BM25 sparse search implementation
│   │   │   └── skill_taxonomy.json # Skill → category → domain map
│   │   └── utils/
│   │       ├── pdf_generator.py  # WeasyPrint HTML→PDF
│   │       └── docx_generator.py # python-docx resume builder
│   └── requirements.txt
├── frontend/
│   ├── app.py                    # Streamlit entry point
│   ├── pages/
│   │   ├── 1_profile_builder.py  # One-time profile setup
│   │   ├── 2_generate_resume.py  # JD input + pipeline trigger
│   │   ├── 3_results.py          # Resume preview + ATS score
│   │   └── 4_history.py          # All past resume versions
│   ├── components/
│   │   ├── ats_score_card.py     # Reusable ATS score widget
│   │   └── resume_preview.py     # Resume section renderer
│   └── requirements.txt
├── docs/
│   ├── ARCHITECTURE.md           # Deep system design doc
│   ├── AGENT_PIPELINE.md         # LangGraph pipeline details
│   └── CONTRIBUTING.md           # How to contribute + commit conventions
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Current Stage

**V1 — In Active Development**

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for current implementation status and next steps.

---

## Commit Convention

Commits must include the author's identity. See [CONTRIBUTING.md](docs/CONTRIBUTING.md).
