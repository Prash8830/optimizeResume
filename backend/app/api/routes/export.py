from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import ResumeVersion
from app.storage.database import get_db
from app.utils.auth_dep import get_current_user_id
from app.utils.pdf_generator import generate_pdf
from app.utils.docx_generator import generate_docx

router = APIRouter()


async def _fetch_version(version_id: str, user_id: str, db: AsyncSession) -> ResumeVersion:
    result = await db.execute(
        select(ResumeVersion).where(
            ResumeVersion.id == version_id,
            ResumeVersion.user_id == user_id,
        )
    )
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Resume version not found")
    return version


@router.get("/pdf/{version_id}")
async def download_pdf(
    version_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    version = await _fetch_version(version_id, user_id, db)
    pdf_bytes = generate_pdf(version.resume_text or "", version.role_title or "Resume")
    filename = f"resume_{(version.company or 'job').replace(' ', '_')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/docx/{version_id}")
async def download_docx(
    version_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    version = await _fetch_version(version_id, user_id, db)
    docx_bytes = generate_docx(version.resume_text or "", version.role_title or "Resume")
    filename = f"resume_{(version.company or 'job').replace(' ', '_')}.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
