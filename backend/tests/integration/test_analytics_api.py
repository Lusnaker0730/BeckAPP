"""
Integration tests for analytics API endpoints.

Tests statistics, trends, and diagnosis analysis endpoints.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
@pytest.mark.api
class TestAnalyticsEndpoints:
    """Test analytics API endpoints."""
    
    def test_get_stats_empty_database(self, authenticated_client):
        """Test getting stats from empty database."""
        client, token, user = authenticated_client
        
        response = client.get("/api/analytics/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "totalPatients" in data
        assert "totalConditions" in data
        assert "totalEncounters" in data
        assert "totalObservations" in data
        
        # Should be 0 for empty database
        assert data["totalPatients"] == 0
        assert data["totalConditions"] == 0
    
    def test_get_stats_with_job_filter(self, authenticated_client):
        """Test getting stats filtered by job ID."""
        client, token, user = authenticated_client
        
        response = client.get("/api/analytics/stats?job_id=test-job-123")
        assert response.status_code == 200
    
    def test_get_trends(self, authenticated_client):
        """Test getting trend data."""
        client, token, user = authenticated_client
        
        response = client.get("/api/analytics/trends")
        assert response.status_code == 200
        
        data = response.json()
        assert "labels" in data
        assert "values" in data
        assert isinstance(data["labels"], list)
        assert isinstance(data["values"], list)
    
    def test_get_trends_with_year_range(self, authenticated_client):
        """Test getting trends with year range."""
        client, token, user = authenticated_client
        
        response = client.get("/api/analytics/trends?start_year=2020&end_year=2023")
        assert response.status_code == 200
    
    def test_get_top_conditions(self, authenticated_client):
        """Test getting top conditions."""
        client, token, user = authenticated_client
        
        response = client.get("/api/analytics/top-conditions?limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "labels" in data
        assert "values" in data
    
    def test_get_top_conditions_invalid_limit(self, authenticated_client):
        """Test getting top conditions with invalid limit."""
        client, token, user = authenticated_client
        
        # Limit > 20 should be rejected
        response = client.get("/api/analytics/top-conditions?limit=50")
        assert response.status_code == 422  # Validation error
    
    def test_get_diagnosis_analysis(self, authenticated_client):
        """Test getting diagnosis analysis."""
        client, token, user = authenticated_client
        
        response = client.get(
            "/api/analytics/diagnosis",
            params={"diagnosis": "influenza", "timeRange": "yearly"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "diagnosis" in data
        assert "labels" in data
        assert "counts" in data
        assert "totalCount" in data
        assert "averageCount" in data
    
    def test_get_diagnosis_analysis_missing_params(self, authenticated_client):
        """Test diagnosis analysis with missing parameters."""
        client, token, user = authenticated_client
        
        response = client.get("/api/analytics/diagnosis")
        assert response.status_code == 422  # Missing required param
    
    def test_get_diagnosis_by_code(self, authenticated_client):
        """Test getting diagnosis by specific code."""
        client, token, user = authenticated_client
        
        response = client.get(
            "/api/analytics/diagnosis-by-code",
            params={"code": "38341003"}  # Hypertension
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "code" in data
        assert data["code"] == "38341003"
    
    def test_get_patient_demographics(self, authenticated_client):
        """Test getting patient demographics."""
        client, token, user = authenticated_client
        
        response = client.get("/api/analytics/patient-demographics")
        assert response.status_code == 200
        
        data = response.json()
        assert "gender" in data
        assert "ageGroups" in data
    
    def test_get_recent_activities(self, authenticated_client):
        """Test getting recent activities."""
        client, token, user = authenticated_client
        
        response = client.get("/api/analytics/recent-activities?limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_available_diagnoses(self, authenticated_client):
        """Test getting available diagnoses list."""
        client, token, user = authenticated_client
        
        response = client.get("/api/analytics/available-diagnoses")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.integration
@pytest.mark.api
class TestAnalyticsAuthorization:
    """Test analytics endpoint authorization."""
    
    def test_analytics_requires_authentication(self, client: TestClient):
        """Test that analytics endpoints require authentication."""
        endpoints = [
            "/api/analytics/stats",
            "/api/analytics/trends",
            "/api/analytics/top-conditions",
            "/api/analytics/patient-demographics"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401, f"Endpoint {endpoint} should require auth"
    
    def test_diagnosis_analysis_requires_authentication(self, client: TestClient):
        """Test that diagnosis analysis requires authentication."""
        response = client.get(
            "/api/analytics/diagnosis",
            params={"diagnosis": "influenza"}
        )
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.slow
class TestAnalyticsPerformance:
    """Test analytics endpoint performance and caching."""
    
    def test_cache_headers(self, authenticated_client):
        """Test that cacheable endpoints have appropriate behavior."""
        client, token, user = authenticated_client
        
        # Make same request twice
        response1 = client.get("/api/analytics/top-conditions")
        response2 = client.get("/api/analytics/top-conditions")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
    
    def test_multiple_concurrent_requests(self, authenticated_client):
        """Test handling multiple concurrent requests."""
        import concurrent.futures
        
        client, token, user = authenticated_client
        
        def make_request():
            return client.get("/api/analytics/stats")
        
        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All should succeed
        assert all(r.status_code == 200 for r in results)

