# LangGraph Agent Pipeline — Deep Dive

> This document explains every agent node in detail. Read this before touching any file in `backend/app/agents/`.

---

## Overview

The pipeline is a `StateGraph` from LangGraph. Every node receives the full `ResumeState`, mutates the relevant fields, and returns the updated state. Nodes are pure functions — no side effects except the final PostgreSQL write in Node 6.

```
START
  │
  ▼
Node 1: JD Analyzer          (LLM: gemini-2.0-flash)
  │
  ▼
Node 2: Profile Scorer        (ChromaDB + BM25, no LLM)
  │
  ▼
Node 3: Content Selector      (pure Python, no LLM)
  │
  ▼
Node 4: Resume Writer         (LLM: gemini-2.0-flash, grounded)
  │
  ▼
Node 5: ATS Checker           (LLM: gemini-1.5-flash-8b)
  │
  ├── score < 0.75 AND iter < 3 ──► back to Node 4
  │
  ▼
Node 6: Report Generator      (pure Python + PostgreSQL write)
  │
  ▼
END
```

---

## Node 1 — JD Analyzer

**File:** `backend/app/agents/jd_analyzer.py`

**Purpose:** Parse the raw job description into a structured keyword map.

**Input fields used:** `state.job_description`, `state.role_title`, `state.company`

**LLM prompt strategy:**
```
System: You are a precise job description analyzer. Extract structured data only.
        Return valid JSON only — no markdown, no explanation.

User:   Analyze this job description:
        {job_description}

        Return JSON:
        {
          "role_type": "<one of: MLOps|GenAI|Agentic AI|Conversational AI|Full-stack|Data Science|Other>",
          "seniority": "<Junior|Mid|Senior|Lead>",
          "required_keywords": {"keyword": weight_float, ...},
          "preferred_keywords": {"keyword": weight_float, ...},
          "company_context": "<one sentence about company tech culture>"
        }

        Weight rules:
        - Title keywords: 3.0
        - "required"/"must have" keywords: 2.0
        - "preferred"/"nice to have": 1.0
        - Mentioned once with no qualifier: 1.0
```

**Output fields set:** `state.jd_analysis`

---

## Node 2 — Profile Scorer

**File:** `backend/app/agents/profile_scorer.py`

**Purpose:** Score every profile chunk against the JD using hybrid search.

**Input fields used:** `state.jd_analysis`, `state.user_id`

**Algorithm:**
```python
# 1. Get JD embedding
jd_text = " ".join(state.jd_analysis["required_keywords"].keys())
jd_embedding = gemini_embed(jd_text)

# 2. ChromaDB cosine query — top 50 chunks
cosine_results = chroma_collection.query(
    query_embeddings=[jd_embedding],
    n_results=50,
    include=["documents", "metadatas", "distances"]
)
# distance → similarity: cosine_score = 1 - distance

# 3. BM25 sparse query
corpus = [chunk.content for chunk in all_chunks]
bm25 = BM25Okapi([doc.split() for doc in corpus])
jd_keywords = list(state.jd_analysis["required_keywords"].keys())
bm25_scores = bm25.get_scores(jd_keywords)
# normalize to [0, 1]

# 4. Hybrid score
final_score = 0.6 * cosine_score + 0.4 * bm25_score
```

**Output fields set:** `state.scored_chunks` (sorted desc by score)

---

## Node 3 — Content Selector

**File:** `backend/app/agents/content_selector.py`

**Purpose:** Select the highest-scoring subset of chunks that fits within one page (~580 words).

**Input fields used:** `state.scored_chunks`

**Algorithm (greedy knapsack):**
```python
WORD_BUDGET = 580
MIN_SCORE_THRESHOLD = 0.4
selected = {"projects": [], "skills": [], "bullets": [], "education": []}
word_count = 0

# Sort chunks by score descending
for chunk in sorted(scored_chunks, key=lambda x: x["score"], reverse=True):
    if chunk["score"] < MIN_SCORE_THRESHOLD:
        break  # everything below threshold is excluded

    if word_count + chunk["word_count"] <= WORD_BUDGET:
        selected[chunk["type"]].append(chunk)
        word_count += chunk["word_count"]
```

**Skill selection special rule:**
Skills are not counted toward word budget individually. Instead:
- Filter skills with `score > 0.5`
- Group by category (from skill_taxonomy.json)
- Max 6 skill categories, max 5 skills per category

**Output fields set:** `state.selected_content`, `state.total_word_count`

---

## Node 4 — Resume Writer

**File:** `backend/app/agents/resume_writer.py`

**Purpose:** Rewrite selected content using JD language. Grounded generation only.

**The Truthfulness Guardrail — Core IP:**

```
System: You are a professional resume writer. You must follow these rules strictly:
        1. ONLY use information explicitly present in the source chunks provided.
        2. You MAY rephrase using terminology from the job description if semantically identical.
        3. You CANNOT add metrics, numbers, outcomes, or technologies not in the source.
        4. You CANNOT invent job titles, company names, or time periods.
        5. If the source says "built a chatbot" and the JD says "conversational AI system",
           you MAY write "built a conversational AI system" — semantically identical.
        6. Output format: plain text resume sections, no markdown, no headers with #.

User:   Job Description Keywords: {required_keywords}
        Role Type: {role_type}
        Company Context: {company_context}

        ATS Feedback (keywords to weave in if iteration > 1): {ats_feedback}

        Source chunks (USE ONLY THIS DATA):
        {selected_content_formatted}

        Write a complete 1-page resume with sections:
        SUMMARY | EXPERIENCE | PROJECTS | SKILLS | EDUCATION
```

**Output fields set:** `state.draft_resume`, `state.iteration_count += 1`

---

## Node 5 — ATS Checker

**File:** `backend/app/agents/ats_checker.py`

**Purpose:** Validate keyword coverage and decide whether to loop or continue.

**Scoring logic:**
```python
required_kws = set(state.jd_analysis["required_keywords"].keys())
resume_lower = state.draft_resume.lower()

matched = {kw for kw in required_kws if kw.lower() in resume_lower}
ats_score = len(matched) / len(required_kws) if required_kws else 1.0

missing = required_kws - matched
```

**LLM call (gemini-1.5-flash-8b) — only if score < 0.75:**
```
Find which of these missing keywords can be naturally inserted
into the resume without changing meaning: {missing_keywords}
Return JSON: {"insertable": ["kw1", "kw2"], "not_insertable": ["kw3"]}
```

**Conditional edge logic:**
```python
def should_loop(state: ResumeState) -> str:
    if state.ats_score < 0.75 and state.iteration_count < 3:
        return "resume_writer"   # loop back
    return "report_generator"    # continue
```

**Output fields set:** `state.ats_score`, `state.ats_feedback`

---

## Node 6 — Report Generator

**File:** `backend/app/agents/report_gen.py`

**Purpose:** Build the optimization report and save to PostgreSQL.

**Report structure:**
```python
{
    "match_percentage": round(state.ats_score * 100, 1),
    "required_keyword_coverage": {
        "matched": [...],
        "missing": [...]
    },
    "preferred_keyword_coverage": {
        "matched": [...],
        "missing": [...]
    },
    "gap_skills": [...],         # skills in JD you genuinely lack
    "swappable_items": [...],    # chunks with score > 0.4 left out due to space
    "iteration_count": state.iteration_count,
    "word_count": state.total_word_count
}
```

**Side effect:** Saves `ResumeVersion` to PostgreSQL, sets `state.resume_version_id`

---

## Adding a New Node

1. Create `backend/app/agents/your_node.py`
2. Define `async def your_node(state: ResumeState) -> ResumeState`
3. Import and add to `graph.py`:
   ```python
   graph.add_node("your_node", your_node)
   graph.add_edge("previous_node", "your_node")
   ```
4. Update `ARCHITECTURE.md` status table

---

## Debugging the Pipeline

Run the pipeline in isolation (no FastAPI needed):
```python
# backend/scripts/test_pipeline.py
from app.agents.graph import build_graph
from app.agents.state import ResumeState

graph = build_graph()
result = graph.invoke(ResumeState(
    job_description="...",
    company="Google",
    role_title="AI Engineer",
    user_id="test-user-id",
    ...
))
print(result["ats_score"])
print(result["optimization_report"])
```
