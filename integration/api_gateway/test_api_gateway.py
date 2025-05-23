import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root_endpoint():
    """Test the root endpoint returns the expected response."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Welcome to the Manus AI Assistant API Gateway"
    assert "documentation" in response.json()
    assert "status" in response.json()

def test_health_check():
    """Test the health check endpoint returns healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_auth_token_endpoint():
    """Test the authentication token endpoint."""
    response = client.post(
        "/api/auth/token",
        data={"username": "testuser", "password": "secret"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_auth_token_invalid_credentials():
    """Test the authentication token endpoint with invalid credentials."""
    response = client.post(
        "/api/auth/token",
        data={"username": "testuser", "password": "wrong_password"}
    )
    assert response.status_code == 401

def test_protected_endpoint_without_token():
    """Test accessing a protected endpoint without a token."""
    response = client.get("/api/llm/generate?prompt=test")
    assert response.status_code == 401

def test_protected_endpoint_with_token():
    """Test accessing a protected endpoint with a valid token."""
    # First get a token
    auth_response = client.post(
        "/api/auth/token",
        data={"username": "testuser", "password": "secret"}
    )
    token = auth_response.json()["access_token"]
    
    # Then use the token to access a protected endpoint
    response = client.get(
        "/api/llm/generate?prompt=test",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "text" in response.json()
    assert "usage" in response.json()
