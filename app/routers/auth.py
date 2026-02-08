from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any
try:
    from sqlmodel import Session, select
except Exception:  # pragma: no cover - typing fallback for static analysis environments
    Session = Any
    def select(*args, **kwargs):
        raise RuntimeError("sqlmodel.select is not available in this environment")

from app.schemas import UserCreate, Token, UserOut, TokenRefresh
from app.models import User, Role
from app.db import get_session
from app.deps import get_current_user, require_roles
from utils.crypto import hash_password, verify_password
from utils.jwt import create_access_token, verify_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
def register(payload: UserCreate, session: Session = Depends(get_session)):
    statement = select(User).where(User.email == payload.email)
    existing = session.exec(statement).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=payload.email, hashed_password=hash_password(payload.password), role=Role.USER.value)
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserOut.model_validate(user)


@router.post("/login", response_model=Token)
def login(form_data: UserCreate, session: Session = Depends(get_session)):
    statement = select(User).where(User.email == form_data.email)
    user = session.exec(statement).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/admin/users")
def create_admin_user(payload: UserCreate, session: Session = Depends(get_session), current_user=Depends(require_roles(Role.SUPERADMIN))):
    """Superadmin only: Create a new admin user."""
    statement = select(User).where(User.email == payload.email)
    existing = session.exec(statement).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=payload.email, hashed_password=hash_password(payload.password), role=Role.ADMIN.value)
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserOut.model_validate(user)


@router.post("/users/{user_id}/role")
def assign_role(user_id: int, role_name: str, session: Session = Depends(get_session), current_user=Depends(require_roles(Role.SUPERADMIN))):
    """Superadmin only: Assign role to user."""
    if role_name not in [r.value for r in Role]:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {[r.value for r in Role]}")
    statement = select(User).where(User.id == user_id)
    user = session.exec(statement).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = role_name
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserOut.model_validate(user)


@router.get("/users/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user info."""
    return UserOut.model_validate(current_user)


@router.post("/refresh", response_model=Token)
def refresh_token(payload: TokenRefresh, session: Session = Depends(get_session)):
    """Refresh access token using refresh token."""
    from datetime import timedelta
    payload_dict = verify_access_token(payload.refresh_token)
    if not payload_dict or payload_dict.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    email = payload_dict.get("sub")
    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    new_token = create_access_token({"sub": user.email})
    return {"access_token": new_token, "token_type": "bearer"}
