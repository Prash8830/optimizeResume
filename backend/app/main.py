from pathlib import Path

from dotenv import load_dotenv

# Load root .env before any module imports read os.getenv()
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env")

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, profile, resume, export
from app.api.routes.admin import router as admin_router
from app.storage.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await _ensure_default_user()
    yield


async def _ensure_default_user():
    from sqlalchemy import select
    from app.storage.database import AsyncSessionLocal
    from app.models.user import User
    from app.utils.auth_dep import DEFAULT_USER_ID

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.id == DEFAULT_USER_ID))
        if not result.scalar_one_or_none():
            db.add(User(id=DEFAULT_USER_ID, email="default@optimizeresume.local", hashed_password=""))
            await db.commit()


app = FastAPI(
    title="OptimizeResume API",
    description="AI-powered resume optimizer — LangGraph agentic pipeline",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(profile.router, prefix="/profile", tags=["profile"])
app.include_router(resume.router, prefix="/resume", tags=["resume"])
app.include_router(export.router, prefix="/export", tags=["export"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "OptimizeResume API v1.0"}
