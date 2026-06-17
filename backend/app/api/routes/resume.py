import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from app.agents.graph import build_graph
from app.agents.state import ResumeState
from app.models.resume import GenerateRequest, ResumeVersion, ResumeVersionOut
from app.storage.database import get_db
from app.utils.auth_dep import get_current_user_id, DEFAULT_USER_ID

router = APIRouter()


@router.post("/generate")
async def generate_resume(body: GenerateRequest):
    """
    Triggers the LangGraph pipeline and streams progress via SSE.
    Each agent node emits a progress event so the Streamlit UI can show live updates.
    """
    async def event_stream():
        graph = build_graph()
        initial_state = ResumeState(
            job_description=body.job_description,
            company=body.company or "",
            role_title=body.role_title or "",
            user_id=DEFAULT_USER_ID,
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

        async for event in graph.astream_events(initial_state, version="v2"):
            kind = event.get("event")
            name = event.get("name", "")

            if kind == "on_chain_start" and name in [
                "jd_analyzer", "profile_scorer", "content_selector",
                "resume_writer", "ats_checker", "report_generator"
            ]:
                yield f"data: {json.dumps({'type': 'progress', 'node': name, 'status': 'started'})}\n\n"

            elif kind == "on_chain_end" and name in [
                "jd_analyzer", "profile_scorer", "content_selector",
                "resume_writer", "ats_checker", "report_generator"
            ]:
                output = event.get("data", {}).get("output", {})
                payload = {"type": "progress", "node": name, "status": "done"}

                if name == "ats_checker":
                    payload["ats_score"] = output.get("ats_score", 0)
                    payload["iteration"] = output.get("iteration_count", 0)

                yield f"data: {json.dumps(payload)}\n\n"

            elif kind == "on_chain_end" and name == "LangGraph":
                final = event.get("data", {}).get("output", {})
                yield f"data: {json.dumps({'type': 'complete', 'resume_version_id': final.get('resume_version_id', ''), 'ats_score': final.get('ats_score', 0), 'optimization_report': final.get('optimization_report', {})})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/versions", response_model=list[ResumeVersionOut])
async def list_versions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ResumeVersion)
        .where(ResumeVersion.user_id == DEFAULT_USER_ID)
        .order_by(ResumeVersion.created_at.desc())
    )
    return result.scalars().all()


@router.get("/versions/{version_id}", response_model=ResumeVersionOut)
async def get_version(version_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ResumeVersion).where(ResumeVersion.id == version_id))
    version = result.scalar_one_or_none()
    if not version:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Resume version not found")
    return version
