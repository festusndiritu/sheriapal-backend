from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any
from datetime import datetime, timezone
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

    # Determine role and approval status
    role = getattr(payload, 'role', Role.USER.value)
    is_approved = role != Role.LAWYER.value  # Lawyers need approval, users are auto-approved

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=role,
        is_approved=is_approved,
        approval_requested_at=datetime.now(timezone.utc) if role == Role.LAWYER.value else None
    )
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


@router.get("/lawyers/pending")
def get_pending_lawyers(session: Session = Depends(get_session), current_user=Depends(require_roles(Role.ADMIN, Role.SUPERADMIN))):
    """Get list of lawyers pending approval (admin/superadmin only)."""
    statement = select(User).where(
        (User.role == Role.LAWYER.value) & (User.is_approved == False)
    ).order_by(User.approval_requested_at)
    lawyers = session.exec(statement).all()
    return [
        {
            "id": l.id,
            "email": l.email,
            "role": l.role,
            "requested_at": l.approval_requested_at
        }
        for l in lawyers
    ]


@router.post("/lawyers/{lawyer_id}/approve")
def approve_lawyer(lawyer_id: int, session: Session = Depends(get_session), current_user=Depends(require_roles(Role.ADMIN, Role.SUPERADMIN))):
    """Approve a lawyer (admin/superadmin only)."""
    statement = select(User).where(User.id == lawyer_id)
    lawyer = session.exec(statement).first()

    if not lawyer:
        raise HTTPException(status_code=404, detail="Lawyer not found")
    if lawyer.role != Role.LAWYER.value:
        raise HTTPException(status_code=400, detail="User is not a lawyer")
    if lawyer.is_approved:
        raise HTTPException(status_code=400, detail="Lawyer already approved")

    lawyer.is_approved = True
    lawyer.approved_by = current_user.id
    lawyer.approved_at = datetime.now(timezone.utc)
    session.add(lawyer)
    session.commit()
    session.refresh(lawyer)

    return {
        "id": lawyer.id,
        "email": lawyer.email,
        "status": "approved",
        "approved_at": lawyer.approved_at
    }


@router.post("/lawyers/{lawyer_id}/decline")
def decline_lawyer(lawyer_id: int, reason: str = "Application declined", session: Session = Depends(get_session), current_user=Depends(require_roles(Role.ADMIN, Role.SUPERADMIN))):
    """Decline a lawyer application (admin/superadmin only)."""
    statement = select(User).where(User.id == lawyer_id)
    lawyer = session.exec(statement).first()

    if not lawyer:
        raise HTTPException(status_code=404, detail="Lawyer not found")
    if lawyer.role != Role.LAWYER.value:
        raise HTTPException(status_code=400, detail="User is not a lawyer")

    # Delete the user since application was declined
    session.delete(lawyer)
    session.commit()

    return {
        "id": lawyer_id,
        "status": "declined",
        "reason": reason
    }
