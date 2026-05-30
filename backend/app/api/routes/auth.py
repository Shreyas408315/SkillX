from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import bcrypt
from pydantic import BaseModel
from typing import Optional

from app.db.session import get_db
from app.db.models import User

router = APIRouter()

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str = "user"

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    
    class Config:
        from_attributes = True

@router.post("/register", response_model=UserResponse)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if email exists
    db_user = db.query(User).filter(User.email == user_in.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = hash_password(user_in.password)
    
    # Create user
    new_user = User(
        email=user_in.email,
        name=user_in.name,
        hashed_password=hashed_password,
        role=user_in.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/login")
def login_user(user_in: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user_in.email).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    if not verify_password(user_in.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    return {
        "id": db_user.id,
        "email": db_user.email,
        "name": db_user.name,
        "role": db_user.role,
        "loggedIn": True
    }
