from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Any
try:
    from sqlmodel import Session, select
except Exception:  # pragma: no cover - typing fallback for static analysis environments
    Session = Any
    def select(*args, **kwargs):
        raise RuntimeError("sqlmodel.select is not available in this environment")

from app.db import get_session
from app.models import User, Role
from utils.jwt import verify_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> User:
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    statement = select(User).where(User.email == sub)
    user = session.exec(statement).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_roles(*allowed_roles: Role):
    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in [r.value if isinstance(r, Role) else r for r in allowed_roles]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        return current_user
    return _checker
