from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from .session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, default="user")  # 'user' or 'recruiter'
    has_resume = Column(Boolean, default=False)
    registration_date = Column(DateTime, default=datetime.utcnow)
    match_score = Column(Integer, default=0)
    status = Column(String, default="Active")

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    tags = Column(String, nullable=False)  # JSON string or comma-separated
    candidates_count = Column(Integer, default=0)
    posted_ago = Column(String, default="Just now")
    tag_colors = Column(String, nullable=True) # JSON string
