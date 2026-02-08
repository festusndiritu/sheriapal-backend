import io


def test_document_upload(client):
    """Test uploading a document."""
    # Register and login
    client.post("/auth/register", json={"email": "doc_user@example.com", "password": "pass"})
    r = client.post("/auth/login", json={"email": "doc_user@example.com", "password": "pass"})
    token = r.json()["access_token"]

    # Upload document
    file_content = b"This is a test document for legal purposes."
    files = {"file": ("test_doc.txt", io.BytesIO(file_content), "text/plain")}
    r = client.post(
        "/docs/",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200
    data = r.json()
    assert data["filename"] == "test_doc.txt"
    assert data["status"] == "uploaded"
    assert "id" in data


def test_document_submit(client):
    """Test submitting a document for review."""
    # Register, login, and upload
    client.post("/auth/register", json={"email": "submit_user@example.com", "password": "pass"})
    r = client.post("/auth/login", json={"email": "submit_user@example.com", "password": "pass"})
    token = r.json()["access_token"]

    file_content = b"Employment contract content"
    files = {"file": ("contract.txt", io.BytesIO(file_content), "text/plain")}
    r = client.post("/docs/", files=files, headers={"Authorization": f"Bearer {token}"})
    doc_id = r.json()["id"]

    # Submit for review
    r = client.post(f"/docs/{doc_id}/submit", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["status"] == "pending_review"


def test_document_list(client):
    """Test listing documents."""
    # Register, login, and upload
    client.post("/auth/register", json={"email": "list_user@example.com", "password": "pass"})
    r = client.post("/auth/login", json={"email": "list_user@example.com", "password": "pass"})
    token = r.json()["access_token"]

    file_content = b"Test doc"
    files = {"file": ("doc.txt", io.BytesIO(file_content), "text/plain")}
    client.post("/docs/", files=files, headers={"Authorization": f"Bearer {token}"})

    # List documents
    r = client.get("/docs/", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    docs = r.json()
    assert len(docs) >= 1
    assert docs[0]["filename"] == "doc.txt"


def test_unsupported_file_type(client):
    """Test that unsupported file types are rejected."""
    # Register and login
    client.post("/auth/register", json={"email": "file_user@example.com", "password": "pass"})
    r = client.post("/auth/login", json={"email": "file_user@example.com", "password": "pass"})
    token = r.json()["access_token"]

    # Try to upload unsupported file
    files = {"file": ("test.exe", io.BytesIO(b"binary"), "application/octet-stream")}
    r = client.post(
        "/docs/",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 400
    assert "Unsupported file type" in r.json()["detail"]

