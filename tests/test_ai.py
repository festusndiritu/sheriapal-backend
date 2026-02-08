def test_ai_query_with_documents(client):
    """Test AI query with document context and citations."""
    # Register, login, upload document
    client.post("/auth/register", json={"email": "ai_user@example.com", "password": "pass"})
    r = client.post("/auth/login", json={"email": "ai_user@example.com", "password": "pass"})
    token = r.json()["access_token"]

    # Upload and approve a document
    import io
    file_content = b"This employment contract outlines the terms of employment including salary, benefits, and termination clauses."
    files = {"file": ("employment.txt", io.BytesIO(file_content), "text/plain")}
    r = client.post("/docs/", files=files, headers={"Authorization": f"Bearer {token}"})
    doc_id = r.json()["id"]

    # Query AI
    r = client.post(
        "/ai/query",
        json={"query": "What are typical employment contract terms?", "use_documents": True},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert "metadata" in data
    assert data["metadata"]["user_id"] == 1


def test_ai_query_without_documents(client):
    """Test AI query without using documents (fallback to Gemini)."""
    # Register and login
    client.post("/auth/register", json={"email": "ai_user2@example.com", "password": "pass"})
    r = client.post("/auth/login", json={"email": "ai_user2@example.com", "password": "pass"})
    token = r.json()["access_token"]

    # Query without documents
    r = client.post(
        "/ai/query",
        json={"query": "What is an affidavit?", "use_documents": False},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert data["metadata"]["use_documents"] is False


def test_get_document_templates(client):
    """Test getting available document templates."""
    client.post("/auth/register", json={"email": "template_user@example.com", "password": "pass"})
    r = client.post("/auth/login", json={"email": "template_user@example.com", "password": "pass"})
    token = r.json()["access_token"]

    r = client.get("/ai/templates", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert "templates" in data
    templates = data["templates"]
    assert len(templates) > 0
    assert any(t["type"] == "employment_contract" for t in templates)


def test_draft_employment_contract(client):
    """Test drafting an employment contract."""
    client.post("/auth/register", json={"email": "draft_user@example.com", "password": "pass"})
    r = client.post("/auth/login", json={"email": "draft_user@example.com", "password": "pass"})
    token = r.json()["access_token"]

    r = client.post(
        "/ai/draft",
        json={
            "document_type": "employment_contract",
            "parties": ["Acme Corp", "John Doe"],
            "effective_date": "2026-03-01",
            "details": {
                "position": "Senior Developer",
                "salary": "$150,000 annually",
                "duration": "2 years",
                "benefits": "Health insurance, 401k"
            }
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200
    data = r.json()
    assert data["document_type"] == "employment_contract"
    assert data["title"] == "Employment Contract"
    assert "content" in data
    assert "Acme Corp" in str(data["parties"])
    assert "note" in data


def test_draft_invalid_document_type(client):
    """Test drafting with invalid document type."""
    client.post("/auth/register", json={"email": "invalid_user@example.com", "password": "pass"})
    r = client.post("/auth/login", json={"email": "invalid_user@example.com", "password": "pass"})
    token = r.json()["access_token"]

    r = client.post(
        "/ai/draft",
        json={
            "document_type": "invalid_type",
            "parties": ["Party A", "Party B"],
            "effective_date": "2026-03-01",
            "details": {}
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 400
    data = r.json()
    assert "error" in data or r.status_code == 400


def test_draft_affidavit(client):
    """Test drafting an affidavit."""
    client.post("/auth/register", json={"email": "affidavit_user@example.com", "password": "pass"})
    r = client.post("/auth/login", json={"email": "affidavit_user@example.com", "password": "pass"})
    token = r.json()["access_token"]

    r = client.post(
        "/ai/draft",
        json={
            "document_type": "affidavit",
            "parties": ["Jane Smith"],
            "effective_date": "2026-02-08",
            "details": {
                "statement": "I declare under penalty of perjury that the facts stated above are true and correct.",
                "jurisdiction": "California"
            }
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200
    data = r.json()
    assert data["document_type"] == "affidavit"
    assert "content" in data

