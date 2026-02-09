from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from app.models import Role, DocumentStatus


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "user"  # "user" or "lawyer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    role: Role


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


class DocumentCreate(BaseModel):
    pass  # uploads handled via UploadFile


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    filename: str
    status: DocumentStatus
    created_at: datetime

