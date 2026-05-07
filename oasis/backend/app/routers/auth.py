from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.deps import get_current_user
from app.models import User, UserProfile
from app.schemas import Token, UserCreate, UserLogin, UserRead


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status_code=409, detail="此 email 已註冊。")

    user = User(
        name=payload.name,
        email=str(payload.email),
        password_hash=get_password_hash(payload.password),
    )
    db.add(user)
    db.flush()
    db.add(UserProfile(user_id=user.id, preferred_locale="zh-TW"))
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> Token:
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email 或密碼錯誤。")
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
