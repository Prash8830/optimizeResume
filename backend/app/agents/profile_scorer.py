from app.agents.state import ResumeState
from app.storage.bm25 import BM25
from app.storage.vector_store import embed_query, query_profile_chunks

COSINE_WEIGHT = 0.6
BM25_WEIGHT = 0.4


async def profile_scorer(state: ResumeState) -> ResumeState:
    jd_analysis = state["jd_analysis"]
    user_id = state["user_id"]

    # Build JD query text from required + preferred keywords
    all_keywords = list(jd_analysis.get("required_keywords", {}).keys()) + \
                   list(jd_analysis.get("preferred_keywords", {}).keys())
    jd_query_text = " ".join(all_keywords) + " " + state["job_description"][:500]

    # Step 1: Dense vector search via ChromaDB
    jd_embedding = embed_query(jd_query_text)
    chunks = query_profile_chunks(user_id, jd_embedding, n_results=100)

    if not chunks:
        return {**state, "scored_chunks": []}

    # Step 2: BM25 sparse search on same corpus
    corpus_texts = [chunk["content"] for chunk in chunks]
    bm25 = BM25().fit(corpus_texts)
    bm25_scores = bm25.get_scores(all_keywords)

    # Step 3: Hybrid score = weighted combination
    for i, chunk in enumerate(chunks):
        cosine = chunk["cosine_score"]
        bm25_score = bm25_scores[i] if i < len(bm25_scores) else 0.0
        chunk["bm25_score"] = bm25_score
        chunk["final_score"] = round(COSINE_WEIGHT * cosine + BM25_WEIGHT * bm25_score, 4)

    # Sort by final score descending
    scored_chunks = sorted(chunks, key=lambda x: x["final_score"], reverse=True)

    return {**state, "scored_chunks": scored_chunks}
