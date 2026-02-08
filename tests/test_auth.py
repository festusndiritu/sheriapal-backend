def test_register_and_login(client):
    # register
    r = client.post("/auth/register", json={"email": "test@example.com", "password": "password"})
    if r.status_code != 200:
        print(f"Register error (status {r.status_code}): {r.json()}")
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "test@example.com"

    # login
    r = client.post("/auth/login", json={"email": "test@example.com", "password": "password"})
    assert r.status_code == 200
    tok = r.json()
    assert "access_token" in tok


def test_register_duplicate_email(client):
    """Test that registering with a duplicate email fails."""
    # Register first user
    r = client.post("/auth/register", json={"email": "dup@example.com", "password": "password"})
    assert r.status_code == 200

    # Try to register with same email
    r = client.post("/auth/register", json={"email": "dup@example.com", "password": "different"})
    assert r.status_code == 400
    assert "already registered" in r.json()["detail"]


def test_login_invalid_credentials(client):
    """Test that login fails with invalid credentials."""
    # Register a user
    client.post("/auth/register", json={"email": "user@example.com", "password": "correct"})

    # Try wrong password
    r = client.post("/auth/login", json={"email": "user@example.com", "password": "wrong"})
    assert r.status_code == 401
    assert "Invalid credentials" in r.json()["detail"]

    # Try non-existent user
    r = client.post("/auth/login", json={"email": "nouser@example.com", "password": "password"})
    assert r.status_code == 401


def test_get_current_user(client):
    """Test getting current user info."""
    # Register and login
    client.post("/auth/register", json={"email": "me@example.com", "password": "pass"})
    r = client.post("/auth/login", json={"email": "me@example.com", "password": "pass"})
    token = r.json()["access_token"]

    # Get user info
    r = client.get("/auth/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "me@example.com"
    assert data["role"] == "user"


def test_admin_only_endpoints(client):
    """Test that non-admin cannot access admin endpoints."""
    # Register as regular user
    client.post("/auth/register", json={"email": "regularuser99@example.com", "password": "pass"})
    r = client.post("/auth/login", json={"email": "regularuser99@example.com", "password": "pass"})
    token = r.json()["access_token"]

    # Try to create admin user (should fail - not superadmin)
    r = client.post(
        "/auth/admin/users",
        json={"email": "admin99@example.com", "password": "pass"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 403
    assert "Not enough permissions" in r.json()["detail"]
