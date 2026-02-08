from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column
from enum import Enum
from sqlalchemy import String


class Role(str, Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    LAWYER = "lawyer"
    USER = "user"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, nullable=False)
    hashed_password: str
    role: Role = Field(sa_column=Column(String, nullable=False, default=Role.USER.value))
    is_active: bool = Field(default=True)


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PENDING = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(index=True, nullable=False)
    filename: str
    filepath: str
    mimetype: Optional[str] = None
    size: Optional[int] = None
    status: DocumentStatus = Field(default=DocumentStatus.UPLOADED)
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
