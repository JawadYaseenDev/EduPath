from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models as m
from ..db import get_db
from ..schemas import LoginIn, RegisterIn
from ..security import (
    create_access_token,
    current_user,
    hash_password,
    password_problem,
    verify_password,
)
from ..services import profile as profile_service

router = APIRouter(prefix="/v1/auth", tags=["auth"])


def _user_out(user: m.User) -> dict:
    return {"id": user.id, "email": user.email, "role": user.role,
            "email_verified": user.email_verified}


def _token(user: m.User) -> dict:
    return {"access_token": create_access_token(user), "token_type": "bearer",
            "user": _user_out(user)}


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if not body.accept_terms:
        raise HTTPException(422, "Please accept the terms and privacy policy to continue.")
    problem = password_problem(body.password)
    if problem:
        raise HTTPException(422, problem)
    email = body.email.lower()
    if db.scalar(select(m.User).where(func.lower(m.User.email) == email)):
        raise HTTPException(409, "An account with this email already exists. Please log in.")
    user = m.User(email=email, password_hash=hash_password(body.password))
    db.add(user)
    db.flush()
    profile = profile_service.get_or_create_profile(db, user)
    profile.full_name = body.full_name
    db.commit()
    return _token(user)


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(m.User).where(func.lower(m.User.email) == body.email.lower()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Wrong email or password.")
    if not user.is_active:
        raise HTTPException(403, "This account has been disabled. Contact support.")
    return _token(user)


@router.post("/logout-all")
def logout_all(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    """Signs the user out on every device by invalidating all existing tokens."""
    user.token_version += 1
    db.commit()
    return {"ok": True}


@router.get("/me")
def me(user: m.User = Depends(current_user)):
    return _user_out(user)
