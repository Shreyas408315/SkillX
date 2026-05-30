from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import courses, gap_analysis, health, matching, resume, roadmap, recruiter, auth
from app.core.config import settings
from app.db.session import engine, SessionLocal
from app.db.models import Base, Job
import json

# Create database tables
Base.metadata.create_all(bind=engine)

# Seed initial jobs if none exist
def seed_jobs():
    db = SessionLocal()
    try:
        if db.query(Job).count() == 0:
            initial_jobs = [
                Job(title="Senior Frontend Developer", company="TechCorp Inc.", tags=json.dumps(["React", "TypeScript", "Remote"]), candidates_count=45, posted_ago="2d ago"),
                Job(title="Backend Python Engineer", company="Dataflow Systems", tags=json.dumps(["Python", "Django", "AWS"]), candidates_count=28, posted_ago="1w ago"),
                Job(title="UI/UX Designer", company="Creative Solutions", tags=json.dumps(["Figma", "User Research"]), candidates_count=124, posted_ago="3w ago", tag_colors=json.dumps({"background": "rgba(52, 152, 219, 0.1)", "color": "#3498db"})),
                Job(title="Lead Data Scientist", company="AI Innovations", tags=json.dumps(["Machine Learning", "NLP"]), candidates_count=12, posted_ago="1d ago", tag_colors=json.dumps({"background": "rgba(46, 213, 115, 0.1)", "color": "#2ed573"}))
            ]
            db.add_all(initial_jobs)
            db.commit()
    finally:
        db.close()

seed_jobs()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AI resume screening and skill gap analysis backend scaffold.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(resume.router, prefix="/api/resume", tags=["resume"])
app.include_router(matching.router, prefix="/api/match", tags=["matching"])
app.include_router(gap_analysis.router, prefix="/api/gap", tags=["gap-analysis"])
app.include_router(roadmap.router, prefix="/api/roadmap", tags=["roadmap"])
app.include_router(courses.router, prefix="/api/courses", tags=["courses"])
app.include_router(recruiter.router, prefix="/api/recruiter", tags=["recruiter"])


@app.get("/")
def root():
    return {
        "message": "FastAPI AI backend is running.",
        "docs": "/docs",
        "llm_mode": settings.llm_mode,
    }
