from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token
)
from app.core.config import settings
from app.models.user import User

router = APIRouter()

# Pydantic schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str = None
    role: str = "user"

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user exists
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create access token
    access_token = create_access_token(
        data={"sub": new_user.username, "role": new_user.role},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "name": new_user.full_name,
            "role": new_user.role
        }
    }

@router.post("/login", response_model=Token)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Find user
    logger.info(f"Login attempt for username: {login_data.username}")
    user = db.query(User).filter(User.username == login_data.username).first()
    
    if not user:
        logger.warning(f"User not found: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"User found: {user.username}, checking password...")
    password_valid = verify_password(login_data.password, user.hashed_password)
    logger.info(f"Password verification result: {password_valid}")
    
    if not password_valid:
        logger.warning(f"Invalid password for user: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "name": user.full_name,
            "role": user.role
        }
    }

@router.post("/smart-auth")
async def smart_auth(token_data: dict, db: Session = Depends(get_db)):
    """Authenticate via SMART on FHIR token"""
    # This endpoint would validate FHIR tokens and create/update user records
    # For now, it's a placeholder
    return {
        "message": "SMART authentication endpoint",
        "status": "not_implemented"
    }

