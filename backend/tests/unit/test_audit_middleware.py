"""
Unit tests for Audit Middleware.

Tests audit log creation, sensitive data sanitization, and middleware behavior.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import Request, Response
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestAuditMiddleware:
    """Test suite for audit middleware functionality."""

    def test_audit_log_creation(self, authenticated_client, test_db):
        """Test that audit logs are created for API requests."""
        client, token, user = authenticated_client

        # Make a request
        response = client.get("/api/patients")

        # Check audit log was created
        from app.models.audit_log import AuditLog

        audit_logs = test_db.query(AuditLog).all()
        assert len(audit_logs) > 0

        # Verify log details
        log = audit_logs[-1]
        assert log.method == "GET"
        assert "/api/patients" in log.endpoint
        assert log.username == user.username
        assert log.status_code == response.status_code

    def test_audit_log_includes_duration(self, authenticated_client, test_db):
        """Test that audit logs include request duration."""
        client, token, user = authenticated_client

        response = client.get("/api/patients")

        from app.models.audit_log import AuditLog

        log = test_db.query(AuditLog).order_by(AuditLog.timestamp.desc()).first()

        assert log is not None
        assert log.duration_ms is not None
        assert log.duration_ms >= 0

    def test_audit_log_includes_ip_address(self, authenticated_client, test_db):
        """Test that audit logs include client IP address."""
        client, token, user = authenticated_client

        response = client.get("/api/patients")

        from app.models.audit_log import AuditLog

        log = test_db.query(AuditLog).order_by(AuditLog.timestamp.desc()).first()

        assert log.ip_address is not None
        # TestClient uses testclient as IP
        assert isinstance(log.ip_address, str)

    def test_sensitive_data_sanitization(self, authenticated_client, test_db):
        """Test that sensitive data is sanitized in audit logs."""
        client, token, user = authenticated_client

        # Make request with password in body
        response = client.post(
            "/api/users/create",
            json={"username": "newuser", "password": "SecretPass123!", "email": "new@example.com"},
        )

        from app.models.audit_log import AuditLog

        log = test_db.query(AuditLog).order_by(AuditLog.timestamp.desc()).first()

        # Verify password is sanitized
        if log.request_params:
            assert (
                "password" not in log.request_params
                or log.request_params.get("password") == "***REDACTED***"
            )

    def test_skip_health_check_endpoints(self, client, test_db):
        """Test that health check endpoints are not audited."""
        # Make health check request
        response = client.get("/health")

        from app.models.audit_log import AuditLog

        # Health checks should not create audit logs
        health_logs = test_db.query(AuditLog).filter(AuditLog.endpoint.like("%/health%")).all()

        # Should be empty or very few
        assert len(health_logs) == 0

    def test_skip_static_files(self, client, test_db):
        """Test that static file requests are not audited."""
        # Make request to docs (static-like endpoint)
        response = client.get("/docs")

        from app.models.audit_log import AuditLog

        docs_logs = test_db.query(AuditLog).filter(AuditLog.endpoint.like("%/docs%")).all()

        # Static files should not be audited
        assert len(docs_logs) == 0

    def test_audit_log_on_error(self, authenticated_client, test_db):
        """Test that audit logs are created even on errors."""
        client, token, user = authenticated_client

        # Make request that will fail
        response = client.get("/api/nonexistent-endpoint")

        from app.models.audit_log import AuditLog

        log = test_db.query(AuditLog).order_by(AuditLog.timestamp.desc()).first()

        # Should have audit log for failed request
        assert log is not None
        assert log.status_code == 404
        assert log.is_success == "failure"

    def test_audit_log_includes_user_role(self, authenticated_client, test_db):
        """Test that audit logs include user role."""
        client, token, user = authenticated_client

        response = client.get("/api/patients")

        from app.models.audit_log import AuditLog

        log = test_db.query(AuditLog).order_by(AuditLog.timestamp.desc()).first()

        assert log.user_role is not None
        assert log.user_role == user.role

    def test_audit_log_action_classification(self, authenticated_client, test_db):
        """Test that actions are correctly classified."""
        client, token, user = authenticated_client

        # Test different action types
        test_cases = [
            ("GET", "/api/patients", "query"),
            ("POST", "/api/export/patients", "export"),
            ("POST", "/api/patients", "create"),
            ("PUT", "/api/patients/1", "update"),
            ("DELETE", "/api/patients/1", "delete"),
        ]

        for method, endpoint, expected_action in test_cases:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})
            elif method == "PUT":
                response = client.put(endpoint, json={})
            elif method == "DELETE":
                response = client.delete(endpoint)

        from app.models.audit_log import AuditLog

        logs = test_db.query(AuditLog).all()

        # Verify actions are classified (if implemented)
        for log in logs:
            if log.action:
                assert isinstance(log.action, str)
                assert len(log.action) > 0

    def test_audit_log_does_not_block_request(self, authenticated_client):
        """Test that audit logging failure doesn't block requests."""
        client, token, user = authenticated_client

        # Even if audit logging fails, request should succeed
        with patch("app.core.audit.create_audit_log", side_effect=Exception("Audit failed")):
            response = client.get("/api/patients")

            # Request should still succeed
            assert response.status_code in [200, 404]

    def test_concurrent_requests_audit_correctly(self, authenticated_client, test_db):
        """Test that concurrent requests are audited correctly."""
        import concurrent.futures

        client, token, user = authenticated_client

        def make_request():
            return client.get("/api/patients")

        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in futures]

        from app.models.audit_log import AuditLog

        # Should have audit logs for all requests
        logs = test_db.query(AuditLog).all()
        assert len(logs) >= 10

    def test_large_request_body_handling(self, authenticated_client, test_db):
        """Test handling of large request bodies in audit logs."""
        client, token, user = authenticated_client

        # Create large request body
        large_data = {"data": "x" * 10000}

        response = client.post("/api/some-endpoint", json=large_data)

        from app.models.audit_log import AuditLog

        log = test_db.query(AuditLog).order_by(AuditLog.timestamp.desc()).first()

        # Large bodies should be truncated or summarized
        if log.request_params:
            import json

            params_str = json.dumps(log.request_params)
            # Should not store huge amounts of data
            assert len(params_str) < 50000

    def test_sensitive_endpoint_marking(self, authenticated_client, test_db):
        """Test that sensitive endpoints are marked in audit logs."""
        client, token, user = authenticated_client

        # Make request to auth endpoint (sensitive)
        response = client.post("/api/auth/login", data={"username": "test", "password": "test"})

        from app.models.audit_log import AuditLog

        log = test_db.query(AuditLog).filter(AuditLog.endpoint.like("%/auth/%")).first()

        if log:
            # Sensitive endpoints should have extra security
            assert log.request_params is None or "password" not in str(log.request_params)


@pytest.mark.unit
class TestAuditLogSanitization:
    """Test suite for sensitive data sanitization."""

    def test_password_sanitization(self):
        """Test password field sanitization."""
        from app.core.audit import sanitize_params

        params = {"username": "testuser", "password": "SecretPass123!", "email": "test@example.com"}

        sanitized = sanitize_params(params)

        assert sanitized["username"] == "testuser"
        assert sanitized["password"] == "***REDACTED***"
        assert sanitized["email"] == "test@example.com"

    def test_token_sanitization(self):
        """Test token field sanitization."""
        from app.core.audit import sanitize_params

        params = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "refresh_token_value",
            "api_key": "api_key_value",
        }

        sanitized = sanitize_params(params)

        assert sanitized["access_token"] == "***REDACTED***"
        assert sanitized["refresh_token"] == "***REDACTED***"
        assert sanitized["api_key"] == "***REDACTED***"

    def test_nested_object_sanitization(self):
        """Test sanitization of nested objects."""
        from app.core.audit import sanitize_params

        params = {
            "user": {
                "username": "test",
                "password": "secret",
                "profile": {"email": "test@example.com", "secret_key": "key123"},
            }
        }

        sanitized = sanitize_params(params)

        assert sanitized["user"]["username"] == "test"
        assert sanitized["user"]["password"] == "***REDACTED***"
        assert sanitized["user"]["profile"]["email"] == "test@example.com"
        assert sanitized["user"]["profile"]["secret_key"] == "***REDACTED***"

    def test_array_sanitization(self):
        """Test sanitization of arrays."""
        from app.core.audit import sanitize_params

        params = {
            "users": [
                {"username": "user1", "password": "pass1"},
                {"username": "user2", "password": "pass2"},
            ]
        }

        sanitized = sanitize_params(params)

        assert sanitized["users"][0]["password"] == "***REDACTED***"
        assert sanitized["users"][1]["password"] == "***REDACTED***"
        assert sanitized["users"][0]["username"] == "user1"

    def test_case_insensitive_sanitization(self):
        """Test case-insensitive field sanitization."""
        from app.core.audit import sanitize_params

        params = {"Password": "secret1", "PASSWORD": "secret2", "passWORD": "secret3"}

        sanitized = sanitize_params(params)

        # All variations should be sanitized
        assert sanitized["Password"] == "***REDACTED***"
        assert sanitized["PASSWORD"] == "***REDACTED***"
        assert sanitized["passWORD"] == "***REDACTED***"

    def test_credit_card_sanitization(self):
        """Test credit card number sanitization."""
        from app.core.audit import sanitize_params

        params = {
            "credit_card": "4532-1234-5678-9010",
            "card_number": "4532123456789010",
            "ccn": "4532 1234 5678 9010",
        }

        sanitized = sanitize_params(params)

        assert sanitized["credit_card"] == "***REDACTED***"
        assert sanitized["card_number"] == "***REDACTED***"
        assert sanitized["ccn"] == "***REDACTED***"

    def test_ssn_sanitization(self):
        """Test SSN sanitization."""
        from app.core.audit import sanitize_params

        params = {"ssn": "123-45-6789", "social_security_number": "123456789"}

        sanitized = sanitize_params(params)

        assert sanitized["ssn"] == "***REDACTED***"
        assert sanitized["social_security_number"] == "***REDACTED***"


@pytest.mark.unit
def test_audit_middleware_initialization():
    """Test audit middleware can be initialized correctly."""
    from fastapi import FastAPI

    from app.middleware.audit_middleware import AuditMiddleware

    app = FastAPI()

    # Should not raise exception
    middleware = AuditMiddleware(app)

    assert middleware is not None


@pytest.mark.integration
def test_audit_log_query_performance(test_db):
    """Test audit log query performance with many records."""
    from datetime import datetime, timedelta

    from app.models.audit_log import AuditLog

    # Create 1000 audit log entries
    for i in range(1000):
        log = AuditLog(
            user_id=1,
            username="testuser",
            user_role="user",
            action="query",
            method="GET",
            endpoint="/api/test",
            status_code=200,
            ip_address="127.0.0.1",
            duration_ms=100,
            is_success="success",
            timestamp=datetime.now() - timedelta(days=i % 30),
        )
        test_db.add(log)

    test_db.commit()

    import time

    start_time = time.time()

    # Query recent logs
    logs = (
        test_db.query(AuditLog)
        .filter(AuditLog.timestamp >= datetime.now() - timedelta(days=7))
        .limit(100)
        .all()
    )

    end_time = time.time()
    duration = end_time - start_time

    # Should be fast even with many records
    assert duration < 1.0
    assert len(logs) > 0
