# Architecture & Implementation Guide

> This document is the handoff bible. If you're picking this up mid-build in a new IDE or context, start here.

---

## Problem Statement (Detailed)

ATS (Applicant Tracking System) scoring formula:
```
ATS Score ≈ matched_keywords / total_words
```

To maximize this ratio with a 1-page resume (~580 words), we must:
1. Only include keywords that match the JD
2. Select only the projects/experience that demonstrate those keywords
3. Rephrase using the JD's exact terminology (without fabricating)

The candidate has a **Master Profile** — a complete database of all their real experience. The system's job is to **select and rephrase**, never invent.

---

## Core Design Decisions

### Why Hybrid Search (BM25 + Cosine)?
- ATS systems use keyword matching (sparse/BM25), not semantics
- Pure vector search optimizes for semantic meaning but misses exact keyword hits
- Hybrid = `0.6 × cosine_similarity + 0.4 × BM25_score`
- This mimics real ATS while also catching synonyms ("chatbot" ↔ "conversational AI")

### Why ChromaDB over Pinecone/Qdrant?
- Runs embedded (in-process), no separate server
- Persists to disk
- Free, zero-ops for V1
- Easy migration to Qdrant in V2

### Why Skip Knowledge Graph for V1?
- Neo4j adds infra complexity before product-market fit
- Skill → domain relationships encoded in `skill_taxonomy.json` (flat JSON)
- Example: `{"LangChain": {"category": "Agentic AI", "domain": "AI/ML", "aliases": ["langchain"]}}`
- Covers 90% of KG use case for matching purposes

### Why LangGraph?
- The ATS Checker → Resume Writer loop is a stateful conditional edge — exactly what LangGraph is built for
- StateGraph carries `ResumeState` through all nodes without manual state passing
- Built-in support for conditional branching (score < 0.75 → loop back)

### Why Streamlit for V1?
- Fastest path to a working product Prashant can personally use
- Avoids React build complexity while validating the core agentic pipeline
- V2 switches to React once pipeline is proven

### Truthfulness Guardrail (Critical)
The Resume Writer Agent uses **grounded generation**:
- Each profile chunk is passed as explicit context to Gemini
- System prompt: "You may only rephrase using JD terminology. You cannot add metrics, outcomes, or facts not present in the source chunk."
- This is enforced by prompt design, not code — the quality of this prompt is the core IP

---

## Data Flow (Step by Step)

```
User → pastes JD
     → FastAPI POST /resume/generate
     → loads user's master profile from PostgreSQL
     → LangGraph graph.invoke(ResumeState)

Node 1 - JD Analyzer:
  Input:  raw JD text
  LLM:    gemini-2.0-flash
  Output: {role_type, required_keywords:{kw:weight}, preferred_keywords:{kw:weight}, seniority}

Node 2 - Profile Scorer:
  Input:  jd_analysis + all profile chunks from ChromaDB
  Logic:  For each chunk:
            cosine_score = chromadb.query(jd_embedding, chunk_embedding)
            bm25_score   = BM25(jd_keywords, chunk_text)
            final_score  = 0.6 * cosine + 0.4 * bm25
  Output: scored_chunks[] sorted by final_score desc

Node 3 - Content Selector:
  Input:  scored_chunks[]
  Logic:  Greedy knapsack — iterate chunks by score desc,
          add to selection if (current_word_count + chunk.words) ≤ 580
          Never include chunks with score < 0.4
  Output: selected_content{projects:[], skills:[], bullets:[], education:[]}

Node 4 - Resume Writer:
  Input:  selected_content + jd_analysis
  LLM:    gemini-2.0-flash (grounded)
  Output: draft_resume (plain text, structured)
          iteration_count += 1

Node 5 - ATS Checker:
  Input:  draft_resume + jd_analysis.required_keywords
  LLM:    gemini-1.5-flash-8b (fast/cheap)
  Logic:  keyword_coverage = matched_required / total_required
          if coverage < 0.75 AND iteration_count < 3:
            add missing keywords to ats_feedback
            → conditional edge back to Node 4
          else:
            → continue to Node 6
  Output: ats_score, ats_feedback

Node 6 - Report Generator:
  Input:  draft_resume + ats_score + scored_chunks (all, not just selected)
  Logic:  - Overall match % = ats_score * 100
          - Gap analysis = JD required skills NOT in selected_content
          - Swappable items = chunks with score > 0.4 that didn't fit (space)
  Output: optimization_report{}, saves resume version to PostgreSQL
```

---

## Database Schema

### PostgreSQL Tables

```sql
-- users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- master_profiles
CREATE TABLE master_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    name VARCHAR,
    email VARCHAR,
    phone VARCHAR,
    linkedin VARCHAR,
    github VARCHAR,
    summary TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- projects (linked to profile)
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID REFERENCES master_profiles(id),
    title VARCHAR NOT NULL,
    description TEXT,
    tech_stack TEXT[],         -- array of strings
    outcomes TEXT[],           -- quantified results
    role_types TEXT[],         -- ['Agentic AI', 'Conversational AI']
    duration VARCHAR,
    github_url VARCHAR,
    word_count INT             -- pre-computed for knapsack
);

-- skills
CREATE TABLE skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID REFERENCES master_profiles(id),
    name VARCHAR NOT NULL,
    category VARCHAR,          -- from skill_taxonomy.json
    domain VARCHAR,
    proficiency VARCHAR        -- 'expert'|'proficient'|'familiar'
);

-- experiences
CREATE TABLE experiences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID REFERENCES master_profiles(id),
    company VARCHAR,
    role VARCHAR,
    start_date VARCHAR,
    end_date VARCHAR,
    bullets TEXT[]             -- each bullet stored separately
);

-- resume_versions
CREATE TABLE resume_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    jd_text TEXT,
    company VARCHAR,
    role_title VARCHAR,
    resume_text TEXT,
    ats_score FLOAT,
    optimization_report JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### ChromaDB Collections

```
Collection: "profile_chunks_{user_id}"
  Documents: one per project/experience bullet/skill group
  Metadata:  {type: "project"|"experience"|"skill", item_id: UUID, word_count: int}
  Embeddings: text-embedding-004 via Gemini API
```

---

## LangGraph State Schema

```python
class ResumeState(TypedDict):
    # Inputs
    job_description: str
    company: str
    role_title: str
    user_id: str

    # Node 1 output
    jd_analysis: dict           # {role_type, required_keywords, preferred_keywords, seniority}

    # Node 2 output
    scored_chunks: list[dict]   # [{content, score, type, item_id, word_count}]

    # Node 3 output
    selected_content: dict      # {projects:[], skills:[], bullets:[], education:[]}
    total_word_count: int

    # Node 4 output (updated each loop)
    draft_resume: str
    iteration_count: int

    # Node 5 output
    ats_score: float
    ats_feedback: list[str]     # missing keywords to weave in

    # Node 6 output
    optimization_report: dict   # {match_pct, gap_skills, swappable_items}
    resume_version_id: str      # UUID of saved PostgreSQL record
```

---

## API Endpoints

```
POST   /auth/register          Register new user
POST   /auth/login             JWT login

GET    /profile/               Get master profile
POST   /profile/               Create/update master profile
POST   /profile/projects       Add project
DELETE /profile/projects/{id}  Delete project
POST   /profile/index          Re-embed profile into ChromaDB

POST   /resume/generate        Trigger LangGraph pipeline (returns SSE stream)
GET    /resume/versions        List all resume versions
GET    /resume/versions/{id}   Get specific version

GET    /export/pdf/{id}        Download PDF
GET    /export/docx/{id}       Download DOCX
```

---

## Gemini API Usage Per Pipeline Run

| Node | Model | Est. Tokens | Purpose |
|------|-------|-------------|---------|
| JD Analyzer | gemini-2.0-flash | ~800 | Extract keyword map |
| Profile Scorer | text-embedding-004 | ~600 | Embed JD + chunks |
| Resume Writer (×2 avg) | gemini-2.0-flash | ~2400 | Grounded rewrite |
| ATS Checker (×2 avg) | gemini-1.5-flash-8b | ~800 | Validation |
| Report Generator | gemini-2.0-flash | ~400 | Report JSON |
| **Total** | | **~5000** | |

Free tier: 1M tokens/day → ~200 resume generations/day.

---

## Current Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Git repo + structure | ✅ Done | Pushed to GitHub |
| Documentation (MD files) | ✅ Done | README, ARCHITECTURE, AGENT_PIPELINE, CONTRIBUTING |
| FastAPI app skeleton | ✅ Done | main.py, CORS, health check |
| Database models | ✅ Done | All SQLAlchemy models |
| Auth routes (JWT) | ✅ Done | Register + login |
| Profile routes | ✅ Done | CRUD + index trigger |
| Resume routes | ✅ Done | Generate + SSE stream |
| Export routes | ✅ Done | PDF + DOCX |
| LangGraph State | ✅ Done | state.py |
| LangGraph Graph | ✅ Done | graph.py with conditional edges |
| Node 1 — JD Analyzer | ✅ Done | Gemini extraction |
| Node 2 — Profile Scorer | ✅ Done | Hybrid BM25 + cosine |
| Node 3 — Content Selector | ✅ Done | Greedy knapsack |
| Node 4 — Resume Writer | ✅ Done | Grounded generation |
| Node 5 — ATS Checker | ✅ Done | Loop logic |
| Node 6 — Report Generator | ✅ Done | Gap analysis |
| ChromaDB vector store | ✅ Done | Wrapper + indexing |
| BM25 search | ✅ Done | rank_bm25 implementation |
| Skill taxonomy JSON | ✅ Done | 100+ skills mapped |
| PDF export | ✅ Done | WeasyPrint |
| DOCX export | ✅ Done | python-docx |
| Streamlit — Profile Builder | ✅ Done | |
| Streamlit — Generate Resume | ✅ Done | |
| Streamlit — Results Page | ✅ Done | |
| Streamlit — History | ✅ Done | |
| docker-compose | ✅ Done | |
| .env.example | ✅ Done | |

---

## Next Steps (V1 → V1.1)

1. **Auth UX** — Add password reset, email verification
2. **Profile import** — Parse an existing resume PDF to pre-fill master profile
3. **JD URL fetch** — Auto-scrape JD from LinkedIn/Indeed URL
4. **Template selection** — Multiple ATS-safe resume templates
5. **Cover letter mode** — Same pipeline, different output format

## Next Steps (V1 → V2)

1. Replace Streamlit with React + TypeScript + TailwindCSS
2. Add real-time SSE progress display in React
3. Add Neo4j knowledge graph for skill traversal
4. Add Redis job queue for concurrent pipeline runs
5. Deployment: Railway/Render for backend, Vercel for React frontend
