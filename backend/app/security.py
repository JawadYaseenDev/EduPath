"""Password hashing, access tokens, and the current-user dependency.

Local auth for development. The plan (docs/SYSTEM_ARCHITECTURE.md) is to switch to
Supabase Auth in staging/production; only this module needs to change.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_db
from .models import User

_hasher = PasswordHasher()
_bearer = HTTPBearer(auto_error=False)

COMMON_PASSWORDS = {"password", "12345678", "123456789", "qwerty123", "password1",
                    "pakistan", "pakistan123", "iloveyou", "11111111", "abc12345"}


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def password_problem(password: str) -> str | None:
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if password.lower() in COMMON_PASSWORDS:
        return "This password is too common. Choose another."
    return None


def create_access_token(user: User) -> str:
    s = get_settings()
    payload = {
        "sub": user.id,
        "role": user.role,
        "ver": user.token_version,
        "exp": datetime.now(UTC) + timedelta(minutes=s.access_token_minutes),
    }
    return jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_algorithm)


def _unauthorised(detail: str = "Please log in again.") -> HTTPException:
    return HTTPException(status.HTTP_401_UNAUTHORIZED, detail,
                         headers={"WWW-Authenticate": "Bearer"})


def current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None:
        raise _unauthorised("Not logged in.")
    s = get_settings()
    try:
        payload = jwt.decode(creds.credentials, s.jwt_secret, algorithms=[s.jwt_algorithm])
    except jwt.PyJWTError:
        raise _unauthorised() from None
    user = db.get(User, payload.get("sub"))
    if user is None or not user.is_active or payload.get("ver") != user.token_version:
        raise _unauthorised()
    return user


def require_role(*roles: str):
    def checker(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have permission.")
        return user

    return checker
