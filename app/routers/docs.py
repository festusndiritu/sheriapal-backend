from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from typing import Any
try:
    from sqlmodel import Session, select
except Exception:  # pragma: no cover - typing fallback for static analysis environments
    Session = Any
    def select(*args, **kwargs):
        raise RuntimeError("sqlmodel.select is not available in this environment")

from app.db import get_session
from app.models import Document, DocumentStatus, Role
from app.services.storage import save_upload_file
from app.deps import get_current_user, require_roles
from app.services.vector_store import vector_store
from datetime import datetime, timezone
import os
from fastapi.responses import FileResponse

router = APIRouter(prefix="/docs", tags=["documents"])


@router.post("/", response_model=dict)
def upload(file: UploadFile = File(...), session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    # simple checks
    if file.content_type not in ("application/pdf", "text/plain", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")
    orig_name, filepath, size = save_upload_file(file)
    doc = Document(owner_id=current_user.id, filename=orig_name, filepath=filepath, mimetype=file.content_type, size=size)
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return {"id": doc.id, "filename": doc.filename, "status": doc.status}


@router.post("/{doc_id}/submit")
def submit(doc_id: int, session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    statement = select(Document).where(Document.id == doc_id)
    doc = session.exec(statement).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not owner")
    doc.status = DocumentStatus.PENDING
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return {"id": doc.id, "status": doc.status}


@router.post("/{doc_id}/approve")
def approve(doc_id: int, session: Session = Depends(get_session), current_user=Depends(require_roles(Role.ADMIN, Role.SUPERADMIN))):
    statement = select(Document).where(Document.id == doc_id)
    doc = session.exec(statement).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.status = DocumentStatus.APPROVED
    doc.approved_by = current_user.id
    doc.approved_at = datetime.now(timezone.utc)
    session.add(doc)
    session.commit()
    session.refresh(doc)
    # stub: add to vector store
    try:
        with open(doc.filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except Exception:
        text = ""
    if text:
        vector_store.add_document(doc.id, text)
    return {"id": doc.id, "status": doc.status}


@router.get("/")
def list_docs(session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    if str(current_user.role) in (Role.ADMIN.value, Role.SUPERADMIN.value):
        statement = select(Document)
    else:
        statement = select(Document).where(Document.owner_id == current_user.id)
    docs = session.exec(statement).all()
    return [
        {"id": d.id, "filename": d.filename, "status": d.status, "created_at": d.created_at} for d in docs
    ]


@router.get("/{doc_id}/download")
def download_document(doc_id: int, session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    """Download a document (owner or admin only)."""
    statement = select(Document).where(Document.id == doc_id)
    doc = session.exec(statement).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.owner_id != current_user.id and str(current_user.role) not in (Role.ADMIN.value, Role.SUPERADMIN.value):
        raise HTTPException(status_code=403, detail="Not authorized")
    if not os.path.exists(doc.filepath):
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(path=doc.filepath, filename=doc.filename)


@router.post("/{doc_id}/reject")
def reject_document(doc_id: int, reason: str = "No reason provided", session: Session = Depends(get_session), current_user=Depends(require_roles(Role.ADMIN, Role.SUPERADMIN))):
    """Reject a document (admin only)."""
    statement = select(Document).where(Document.id == doc_id)
    doc = session.exec(statement).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.status = DocumentStatus.REJECTED
    doc.approved_by = current_user.id
    doc.approved_at = datetime.now(timezone.utc)
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return {"id": doc.id, "status": doc.status, "rejection_reason": reason}


@router.delete("/{doc_id}")
def delete_document(doc_id: int, session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    """Delete a document (owner or admin only)."""
    statement = select(Document).where(Document.id == doc_id)
    doc = session.exec(statement).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.owner_id != current_user.id and str(current_user.role) not in (Role.ADMIN.value, Role.SUPERADMIN.value):
        raise HTTPException(status_code=403, detail="Not authorized")

    # Delete file from disk
    if os.path.exists(doc.filepath):
        os.remove(doc.filepath)

    session.delete(doc)
    session.commit()
    return {"id": doc_id, "deleted": True}
