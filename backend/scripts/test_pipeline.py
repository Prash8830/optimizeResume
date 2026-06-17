"""
Standalone pipeline test — runs without FastAPI.
Usage: python -m scripts.test_pipeline
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv("../.env")

from app.agents.graph import build_graph
from app.agents.state import ResumeState

SAMPLE_JD = """
We are looking for a Senior AI Engineer to build conversational AI systems and LLM-powered agents.

Required:
- Python, LangChain, LangGraph, RAG
- Experience with LLM APIs (Gemini, OpenAI, or similar)
- FastAPI, REST API design
- PostgreSQL, Vector databases (ChromaDB or Pinecone)

Preferred:
- MLOps, model deployment experience
- Docker, Kubernetes
- Experience with Rasa or Dialogflow
"""


async def main():
    graph = build_graph()
    state = ResumeState(
        job_description=SAMPLE_JD,
        company="TestCorp",
        role_title="Senior AI Engineer",
        user_id="test-user-123",
        jd_analysis={},
        scored_chunks=[],
        selected_content={},
        total_word_count=0,
        draft_resume="",
        iteration_count=0,
        ats_score=0.0,
        ats_feedback=[],
        optimization_report={},
        resume_version_id="",
    )

    print("Running pipeline...")
    result = await graph.ainvoke(state)

    print(f"\nATS Score: {round(result['ats_score'] * 100, 1)}%")
    print(f"Iterations: {result['iteration_count']}")
    print(f"\nMatch %: {result['optimization_report'].get('match_percentage')}%")
    print(f"Gap skills: {result['optimization_report'].get('gap_skills')}")
    print(f"\n--- RESUME ---\n{result['draft_resume'][:1000]}")


if __name__ == "__main__":
    asyncio.run(main())
