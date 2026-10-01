import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app

client = TestClient(app)

def test_unauthorized_access():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert "detail" in response.json()

@patch("app.api.v1.dependencies.get_current_user")
def test_admin_rbac_bypass(mock_user):
    mock_user.return_value = MagicMock(id="1", email="admin@autoworth.ai", is_superuser=True, is_active=True, is_verified=True)
    response = client.get("/api/v1/health")
    assert response.status_code == 200

from fastapi import HTTPException

@patch("app.services.auth_service.AuthService.login")
def test_login_validation(mock_login):
    mock_login.side_effect = HTTPException(status_code=401, detail="Invalid credentials")
    response = client.post("/api/v1/auth/login", json={"email": "wrong@example.com", "password": "wrong"})
    assert response.status_code == 401
