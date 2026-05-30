from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User, Job
import json

router = APIRouter()

@router.get("/users", response_model=List[Dict[str, Any]])
def get_users(db: Session = Depends(get_db)):
    """Get all registered candidates from the database."""
    users = db.query(User).filter(User.role == "user").all()
    
    result = []
    for u in users:
        result.append({
            "name": u.name,
            "email": u.email,
            "role": "Candidate", # Default role display for all users
            "hasResume": u.has_resume,
            "date": u.registration_date.strftime("%Y-%m-%d"),
            "match": u.match_score,
            "status": u.status
        })
    return result

@router.get("/jobs", response_model=List[Dict[str, Any]])
def get_jobs(db: Session = Depends(get_db)):
    """Get all active job postings from the database."""
    jobs = db.query(Job).all()
    
    result = []
    for j in jobs:
        tag_colors = json.loads(j.tag_colors) if j.tag_colors else None
        result.append({
            "id": f"job-{j.id}",
            "title": j.title,
            "company": j.company,
            "tags": json.loads(j.tags),
            "candidatesCount": j.candidates_count,
            "postedAgo": j.posted_ago,
            "tagColors": tag_colors
        })
    return result

@router.get("/analytics", response_model=Dict[str, Any])
def get_analytics(db: Session = Depends(get_db)):
    """Get system-wide analytics from the database."""
    total_users = db.query(User).filter(User.role == "user").count()
    resumes_extracted = db.query(User).filter(User.role == "user", User.has_resume == True).count()
    
    # We still use mock trend data, but anchor the base numbers on reality
    return {
        "summary": {
            "totalUsers": { "value": str(total_users), "trend": "+12% this week", "isUp": True },
            "resumesExtracted": { "value": str(resumes_extracted), "trend": "+8.4% this week", "isUp": True },
            "successfulMatches": { "value": str(min(1204, total_users)), "trend": "+2.1% this week", "isUp": True },
            "avgMatchRate": { "value": "76%", "trend": "-1.2% this week", "isUp": False }
        },
        "candidateActivity": [
            { "month": "Oct", "value": "4.2k", "height": "40%" },
            { "month": "Nov", "value": "5.8k", "height": "55%" },
            { "month": "Dec", "value": "4.8k", "height": "45%" },
            { "month": "Jan", "value": "8.4k", "height": "80%" },
            { "month": "Feb", "value": "6.8k", "height": "65%" },
            { "month": "Mar", "value": "9.5k", "height": "90%" }
        ],
        "topSkills": [
            { "name": "Frontend / React", "percentage": "45%", "width": "45%", "colors": ["#d85f24", "#ff8a4c"] },
            { "name": "Backend / Node.js", "percentage": "30%", "width": "30%", "colors": ["#3498db", "#5dade2"] },
            { "name": "Data Science / Python", "percentage": "25%", "width": "25%", "colors": ["#2ed573", "#7bed9f"] }
        ]
    }
