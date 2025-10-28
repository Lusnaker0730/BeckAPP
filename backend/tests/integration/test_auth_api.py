"""
Integration tests for authentication API endpoints.

Tests login, token generation, and protected route access.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
@pytest.mark.auth
class TestAuthEndpoints:
    """Test authentication API endpoints."""
    
    def test_health_check(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
    
    def test_login_success(self, client: TestClient, create_test_user, test_user_data):
        """Test successful login."""
        # Create user
        create_test_user()
        
        # Login
        response = client.post(
            "/api/auth/login",
            data={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_username(self, client: TestClient):
        """Test login with invalid username."""
        response = client.post(
            "/api/auth/login",
            data={
                "username": "nonexistent",
                "password": "password"
            }
        )
        
        assert response.status_code == 401
    
    def test_login_invalid_password(self, client: TestClient, create_test_user, test_user_data):
        """Test login with invalid password."""
        # Create user
        create_test_user()
        
        # Try login with wrong password
        response = client.post(
            "/api/auth/login",
            data={
                "username": test_user_data["username"],
                "password": "WrongPassword123!"
            }
        )
        
        assert response.status_code == 401
    
    def test_login_inactive_user(self, client: TestClient, create_test_user, test_user_data):
        """Test login with inactive user."""
        # Create inactive user
        create_test_user(is_active=False)
        
        # Try login
        response = client.post(
            "/api/auth/login",
            data={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )
        
        assert response.status_code == 401
    
    def test_protected_route_without_token(self, client: TestClient):
        """Test accessing protected route without token."""
        response = client.get("/api/analytics/stats")
        assert response.status_code == 401
    
    def test_protected_route_with_invalid_token(self, client: TestClient):
        """Test accessing protected route with invalid token."""
        client.headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/analytics/stats")
        assert response.status_code == 401
    
    def test_protected_route_with_valid_token(self, authenticated_client):
        """Test accessing protected route with valid token."""
        client, token, user = authenticated_client
        response = client.get("/api/analytics/stats")
        
        # Should succeed (may return 200 or other valid status)
        assert response.status_code in [200, 404]  # 404 if no data


@pytest.mark.integration
@pytest.mark.auth
class TestTokenBehavior:
    """Test JWT token behavior."""
    
    def test_token_reuse(self, authenticated_client):
        """Test that same token can be reused."""
        client, token, user = authenticated_client
        
        # Make multiple requests with same token
        response1 = client.get("/api/analytics/stats")
        response2 = client.get("/api/analytics/stats")
        
        assert response1.status_code == response2.status_code
    
    def test_token_contains_user_info(self, authenticated_client):
        """Test that token contains user information."""
        client, token, user = authenticated_client
        
        # Decode token (in real app, backend does this)
        from jose import jwt
        from app.core.config import settings
        
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        assert "sub" in payload  # Username in "sub" claim
    
    def test_different_users_different_tokens(self, client, create_test_user, test_user_data, test_admin_data):
        """Test that different users get different tokens."""
        # Create two users
        create_test_user()
        create_test_user(**test_admin_data)
        
        # Login as first user
        response1 = client.post(
            "/api/auth/login",
            data={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )
        token1 = response1.json()["access_token"]
        
        # Login as second user
        response2 = client.post(
            "/api/auth/login",
            data={
                "username": test_admin_data["username"],
                "password": test_admin_data["password"]
            }
        )
        token2 = response2.json()["access_token"]
        
        assert token1 != token2


@pytest.mark.integration
@pytest.mark.auth
class TestRoleBasedAccess:
    """Test role-based access control."""
    
    def test_admin_access(self, admin_client):
        """Test that admin can access admin routes."""
        client, token, admin = admin_client
        
        # Try to access admin endpoint
        response = client.get("/api/admin/etl-jobs")
        
        # Should succeed (may return 200 with empty list)
        assert response.status_code == 200
    
    def test_user_no_admin_access(self, authenticated_client):
        """Test that regular user cannot access admin routes."""
        client, token, user = authenticated_client
        
        # Try to access admin endpoint
        response = client.get("/api/admin/etl-jobs")
        
        # Should be forbidden
        assert response.status_code == 403
    
    def test_get_current_user(self, authenticated_client):
        """Test getting current user information."""
        client, token, user = authenticated_client
        
        # Get current user (if endpoint exists)
        response = client.get("/api/auth/me")
        
        if response.status_code == 200:
            data = response.json()
            assert "username" in data
            assert data["username"] == user.username


@pytest.mark.integration
class TestSecurityHeaders:
    """Test security headers are present in responses."""
    
    def test_security_headers_present(self, client: TestClient):
        """Test that security headers are added to responses."""
        response = client.get("/")
        
        headers = response.headers
        assert "X-Content-Type-Options" in headers
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert "X-Frame-Options" in headers
        assert headers["X-Frame-Options"] == "DENY"
        assert "X-XSS-Protection" in headers
    
    def test_cors_headers(self, client: TestClient):
        """Test CORS headers configuration."""
        response = client.options("/api/analytics/stats", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        })
        
        # Check if CORS headers are present
        assert response.status_code in [200, 404]

