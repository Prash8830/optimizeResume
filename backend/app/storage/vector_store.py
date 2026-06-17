import os
from typing import Optional

import chromadb
from chromadb.config import Settings
import google.generativeai as genai

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

genai.configure(api_key=GEMINI_API_KEY)

_chroma_client: Optional[chromadb.PersistentClient] = None


def get_chroma_client() -> chromadb.PersistentClient:
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
    return _chroma_client


def get_collection(user_id: str):
    client = get_chroma_client()
    collection_name = f"profile_{user_id.replace('-', '_')}"
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def embed_text(text: str) -> list[float]:
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=text,
        task_type="retrieval_document",
    )
    return result["embedding"]


def embed_query(text: str) -> list[float]:
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=text,
        task_type="retrieval_query",
    )
    return result["embedding"]


async def index_user_profile(user_id: str, profile_data) -> None:
    """Embed all profile chunks and store in ChromaDB."""
    collection = get_collection(user_id)

    # Clear existing documents for this user
    try:
        existing = collection.get()
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
    except Exception:
        pass

    documents = []
    embeddings = []
    metadatas = []
    ids = []

    # Index projects
    for i, project in enumerate(profile_data.projects or []):
        text = _project_to_text(project)
        doc_id = f"project_{i}"
        documents.append(text)
        embeddings.append(embed_text(text))
        metadatas.append({
            "type": "project",
            "title": project.title,
            "word_count": len(text.split()),
            "role_types": ",".join(project.role_types or []),
        })
        ids.append(doc_id)

    # Index experience bullets (each bullet as separate chunk)
    for i, exp in enumerate(profile_data.experiences or []):
        for j, bullet in enumerate(exp.bullets or []):
            text = f"{exp.role} at {exp.company}: {bullet}"
            doc_id = f"exp_{i}_bullet_{j}"
            documents.append(text)
            embeddings.append(embed_text(text))
            metadatas.append({
                "type": "experience",
                "company": exp.company,
                "role": exp.role,
                "word_count": len(text.split()),
            })
            ids.append(doc_id)

    # Index skills as grouped categories
    from collections import defaultdict
    skill_groups: dict[str, list[str]] = defaultdict(list)
    for skill in profile_data.skills or []:
        category = skill.category or "General"
        skill_groups[category].append(skill.name)

    for i, (category, names) in enumerate(skill_groups.items()):
        text = f"{category} skills: {', '.join(names)}"
        doc_id = f"skill_group_{i}"
        documents.append(text)
        embeddings.append(embed_text(text))
        metadatas.append({
            "type": "skill",
            "category": category,
            "word_count": len(text.split()),
        })
        ids.append(doc_id)

    if documents:
        collection.add(documents=documents, embeddings=embeddings, metadatas=metadatas, ids=ids)


def query_profile_chunks(user_id: str, jd_embedding: list[float], n_results: int = 50) -> list[dict]:
    """Query ChromaDB for top N chunks most similar to the JD embedding."""
    collection = get_collection(user_id)
    total = collection.count()
    if total == 0:
        return []

    results = collection.query(
        query_embeddings=[jd_embedding],
        n_results=min(n_results, total),
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for i, doc_id in enumerate(results["ids"][0]):
        distance = results["distances"][0][i]
        cosine_score = max(0.0, 1.0 - distance)
        chunks.append({
            "id": doc_id,
            "content": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "cosine_score": cosine_score,
            "type": results["metadatas"][0][i].get("type", "unknown"),
            "word_count": results["metadatas"][0][i].get("word_count", 0),
        })
    return chunks


def _project_to_text(project) -> str:
    parts = [project.title]
    if project.description:
        parts.append(project.description)
    if project.tech_stack:
        parts.append("Technologies: " + ", ".join(project.tech_stack))
    if project.outcomes:
        parts.append("Outcomes: " + ". ".join(project.outcomes))
    return " ".join(parts)
