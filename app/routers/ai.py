from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.services.vector_store import vector_store
from app.services import GeminiStub
from app.deps import get_current_user

router = APIRouter(prefix="/ai", tags=["ai"])

class AIQuery(BaseModel):
    query: str
    top_k: int = 5
    use_documents: bool = True


class DocumentDraft(BaseModel):
    document_type: str  # e.g., "employment_contract", "affidavit", "power_of_attorney"
    parties: list[str]  # Names of parties involved
    effective_date: str  # Date in YYYY-MM-DD format
    details: dict  # Custom details like "salary", "duration", etc.


class AIResponse(BaseModel):
    answer: str
    sources: list[dict] = []
    citations: list[dict] = []
    metadata: dict = {}


@router.post("/query", response_model=AIResponse)
def query_ai(payload: AIQuery, current_user=Depends(get_current_user)):
    """Query AI with optional document context and citations."""
    from datetime import datetime

    sources = []
    citations = []

    # Retrieve relevant documents
    if payload.use_documents:
        sources = vector_store.query(payload.query, top_k=payload.top_k)

        # Build citations from sources
        for i, source in enumerate(sources, 1):
            citations.append({
                "id": i,
                "doc_id": source.get("doc_id"),
                "score": source.get("score"),
                "excerpt": source.get("snippet", "")[:200]
            })

    gemini = GeminiStub()

    # Build prompt with citations
    if sources:
        context_parts = []
        for i, source in enumerate(sources, 1):
            context_parts.append(f"[{i}] {source.get('snippet', '')}")
        context = "\n\n".join(context_parts)
        prompt = f"Based on these documents:\n{context}\n\nAnswer this question: {payload.query}\nInclude references like [1], [2] etc to cite sources."
        answer = gemini.complete(prompt)
    else:
        prompt = f"Question: {payload.query}\n\nProvide helpful legal information."
        answer = gemini.complete(prompt)

    metadata = {
        "query_timestamp": datetime.now().isoformat(),
        "user_id": current_user.id,
        "use_documents": payload.use_documents,
        "documents_searched": len(sources),
        "model": "gemini-stub"
    }

    return AIResponse(
        answer=answer,
        sources=sources,
        citations=citations,
        metadata=metadata
    )


# Document templates for drafting
DOCUMENT_TEMPLATES = {
    "employment_contract": {
        "title": "Employment Contract",
        "required_fields": ["employer_name", "employee_name", "position", "salary", "start_date", "duration"],
        "description": "Standard employment agreement between employer and employee"
    },
    "affidavit": {
        "title": "Affidavit",
        "required_fields": ["declarant_name", "statement", "date"],
        "description": "Sworn statement under oath"
    },
    "power_of_attorney": {
        "title": "Power of Attorney",
        "required_fields": ["principal_name", "agent_name", "powers", "effective_date"],
        "description": "Legal authorization for one person to act on behalf of another"
    },
    "tenancy_agreement": {
        "title": "Tenancy Agreement",
        "required_fields": ["landlord_name", "tenant_name", "property_address", "rent_amount", "lease_start", "lease_end"],
        "description": "Agreement between landlord and tenant for property rental"
    },
    "sales_agreement": {
        "title": "Sales Agreement",
        "required_fields": ["seller_name", "buyer_name", "item_description", "price", "delivery_date"],
        "description": "Agreement for the sale of goods or services"
    },
    "demand_letter": {
        "title": "Demand Letter",
        "required_fields": ["sender_name", "recipient_name", "claim_details", "amount_demanded", "deadline"],
        "description": "Formal letter demanding payment or action"
    }
}


@router.post("/draft")
def draft_document(payload: DocumentDraft, current_user=Depends(get_current_user)):
    """Draft a custom legal document using AI."""
    from datetime import datetime
    from fastapi import HTTPException

    doc_type = payload.document_type.lower()

    if doc_type not in DOCUMENT_TEMPLATES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown document type: {doc_type}. Available types: {list(DOCUMENT_TEMPLATES.keys())}"
        )

    template = DOCUMENT_TEMPLATES[doc_type]

    # Build prompt for document generation
    details_str = "\n".join([f"- {k}: {v}" for k, v in payload.details.items()])

    prompt = f"""Generate a professional {template['title']} with the following details:
Parties: {', '.join(payload.parties)}
Effective Date: {payload.effective_date}
Additional Details:
{details_str}

Create a complete, ready-to-use document with all necessary legal clauses and sections."""

    gemini = GeminiStub()
    draft_content = gemini.complete(prompt)

    return {
        "document_type": doc_type,
        "title": template["title"],
        "description": template["description"],
        "parties": payload.parties,
        "effective_date": payload.effective_date,
        "content": draft_content,
        "generated_at": datetime.now().isoformat(),
        "user_id": current_user.id,
        "note": "This is an AI-generated draft. Please review with a legal professional before use."
    }


@router.get("/templates")
def get_document_templates():
    """Get available document templates and their requirements."""
    return {
        "templates": [
            {
                "type": type_key,
                "title": template["title"],
                "description": template["description"],
                "required_fields": template["required_fields"]
            }
            for type_key, template in DOCUMENT_TEMPLATES.items()
        ]
    }
