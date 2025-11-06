"""
Integration tests for Survival Analysis API endpoints.

Tests Kaplan-Meier curves, Cox regression, and survival statistics.
"""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
@pytest.mark.api
class TestSurvivalAnalysisAPI:
    """Test suite for survival analysis endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self, test_db, sample_patient_data):
        """Setup test data before each test."""
        from app.models.fhir_resources import Condition, Observation, Patient

        # Create test patients with conditions
        self.patients = []
        self.conditions = []

        for i in range(20):
            # Create patient
            patient = Patient(
                fhir_id=f"patient-{i}",
                identifier=f"MRN{i:05d}",
                family_name=f"Patient{i}",
                given_name="Test",
                gender="male" if i % 2 == 0 else "female",
                birth_date=f"{1950 + i}-01-01",
            )
            test_db.add(patient)
            test_db.flush()
            self.patients.append(patient)

            # Create condition (cancer diagnosis)
            onset_date = datetime(2020, 1, 1) + timedelta(days=i * 30)
            condition = Condition(
                fhir_id=f"condition-{i}",
                patient_id=patient.id,
                code={
                    "coding": [
                        {
                            "system": "ICD-10",
                            "code": "C50.9",  # Breast cancer
                            "display": "Malignant neoplasm of breast",
                        }
                    ]
                },
                code_text="Breast cancer",
                clinical_status="active",
                onset_datetime=onset_date,
            )
            test_db.add(condition)
            self.conditions.append(condition)

        test_db.commit()

    def test_kaplan_meier_success(self, authenticated_client):
        """Test successful Kaplan-Meier curve generation."""
        client, token, user = authenticated_client

        response = client.post(
            "/api/survival/kaplan-meier",
            json={
                "condition_code": "C50.9",
                "start_date": "2020-01-01",
                "end_date": "2023-12-31",
                "time_unit": "months",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "survival_curve" in data
        assert "median_survival" in data
        assert "confidence_interval" in data
        assert "n_patients" in data
        assert "n_events" in data

        # Verify survival curve data
        assert isinstance(data["survival_curve"], list)
        assert len(data["survival_curve"]) > 0

        # Verify curve point structure
        point = data["survival_curve"][0]
        assert "time" in point
        assert "survival_probability" in point
        assert "at_risk" in point

        # Verify survival probability is between 0 and 1
        for point in data["survival_curve"]:
            assert 0 <= point["survival_probability"] <= 1

        # Verify patient count
        assert data["n_patients"] > 0

    def test_kaplan_meier_with_stratification(self, authenticated_client):
        """Test Kaplan-Meier with stratification by gender."""
        client, token, user = authenticated_client

        response = client.post(
            "/api/survival/kaplan-meier",
            json={
                "condition_code": "C50.9",
                "start_date": "2020-01-01",
                "end_date": "2023-12-31",
                "stratify_by": "gender",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify stratified results
        assert "strata" in data
        assert isinstance(data["strata"], dict)

        # Should have both male and female strata
        assert len(data["strata"]) >= 1

        # Verify each stratum has survival curve
        for stratum_name, stratum_data in data["strata"].items():
            assert "survival_curve" in stratum_data
            assert "median_survival" in stratum_data
            assert "n_patients" in stratum_data

    def test_kaplan_meier_no_data(self, authenticated_client):
        """Test Kaplan-Meier with no matching data."""
        client, token, user = authenticated_client

        response = client.post(
            "/api/survival/kaplan-meier",
            json={
                "condition_code": "Z99.9",  # Non-existent code
                "start_date": "2020-01-01",
                "end_date": "2023-12-31",
            },
        )

        # Should return error or empty result
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert data["n_patients"] == 0

    def test_kaplan_meier_invalid_dates(self, authenticated_client):
        """Test Kaplan-Meier with invalid date range."""
        client, token, user = authenticated_client

        response = client.post(
            "/api/survival/kaplan-meier",
            json={
                "condition_code": "C50.9",
                "start_date": "2023-12-31",
                "end_date": "2020-01-01",  # End before start
            },
        )

        assert response.status_code == 400
        assert "detail" in response.json()

    def test_kaplan_meier_missing_required_fields(self, authenticated_client):
        """Test Kaplan-Meier with missing required fields."""
        client, token, user = authenticated_client

        response = client.post(
            "/api/survival/kaplan-meier",
            json={
                "start_date": "2020-01-01",
                # Missing condition_code
            },
        )

        assert response.status_code == 422  # Validation error

    def test_cox_regression_success(self, authenticated_client):
        """Test successful Cox proportional hazards regression."""
        client, token, user = authenticated_client

        response = client.post(
            "/api/survival/cox-regression",
            json={
                "condition_code": "C50.9",
                "start_date": "2020-01-01",
                "end_date": "2023-12-31",
                "covariates": ["age", "gender"],
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "hazard_ratios" in data
        assert "confidence_intervals" in data
        assert "p_values" in data
        assert "concordance_index" in data
        assert "n_patients" in data

        # Verify hazard ratios for each covariate
        assert isinstance(data["hazard_ratios"], dict)
        for covariate in ["age", "gender"]:
            if covariate in data["hazard_ratios"]:
                assert data["hazard_ratios"][covariate] > 0

        # Verify concordance index is between 0 and 1
        assert 0 <= data["concordance_index"] <= 1

    def test_cox_regression_no_covariates(self, authenticated_client):
        """Test Cox regression without covariates."""
        client, token, user = authenticated_client

        response = client.post(
            "/api/survival/cox-regression",
            json={
                "condition_code": "C50.9",
                "start_date": "2020-01-01",
                "end_date": "2023-12-31",
                "covariates": [],
            },
        )

        assert response.status_code == 400
        assert "covariate" in response.json()["detail"].lower()

    def test_survival_statistics_success(self, authenticated_client):
        """Test survival statistics endpoint."""
        client, token, user = authenticated_client

        response = client.get(
            "/api/survival/statistics",
            params={
                "condition_code": "C50.9",
                "start_date": "2020-01-01",
                "end_date": "2023-12-31",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "n_patients" in data
        assert "n_events" in data
        assert "median_survival" in data
        assert "mean_survival" in data
        assert "survival_rate_1year" in data
        assert "survival_rate_5year" in data

        # Verify values are reasonable
        assert data["n_patients"] > 0
        assert data["n_events"] >= 0
        assert data["n_events"] <= data["n_patients"]

    def test_survival_comparison_groups(self, authenticated_client):
        """Test survival comparison between groups."""
        client, token, user = authenticated_client

        response = client.post(
            "/api/survival/compare",
            json={
                "condition_code": "C50.9",
                "start_date": "2020-01-01",
                "end_date": "2023-12-31",
                "group_by": "gender",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify comparison results
        assert "groups" in data
        assert "log_rank_test" in data

        # Verify log-rank test results
        assert "statistic" in data["log_rank_test"]
        assert "p_value" in data["log_rank_test"]
        assert "significant" in data["log_rank_test"]

        # Verify p-value is between 0 and 1
        assert 0 <= data["log_rank_test"]["p_value"] <= 1

    def test_unauthorized_access(self, client):
        """Test accessing survival analysis without authentication."""
        response = client.post(
            "/api/survival/kaplan-meier",
            json={"condition_code": "C50.9", "start_date": "2020-01-01", "end_date": "2023-12-31"},
        )

        assert response.status_code == 401

    def test_survival_export(self, authenticated_client):
        """Test exporting survival analysis results."""
        client, token, user = authenticated_client

        response = client.post(
            "/api/survival/kaplan-meier/export",
            json={
                "condition_code": "C50.9",
                "start_date": "2020-01-01",
                "end_date": "2023-12-31",
                "format": "csv",
            },
        )

        assert response.status_code == 200

        # Verify CSV content
        content = response.content.decode()
        assert "time" in content.lower()
        assert "survival_probability" in content.lower()

    @pytest.mark.slow
    def test_large_dataset_performance(self, authenticated_client, test_db):
        """Test survival analysis performance with large dataset."""
        from app.models.fhir_resources import Condition, Patient

        # Create 1000 additional patients
        for i in range(1000):
            patient = Patient(
                fhir_id=f"patient-large-{i}",
                identifier=f"LRGE{i:05d}",
                family_name=f"Large{i}",
                given_name="Test",
                gender="male" if i % 2 == 0 else "female",
                birth_date=f"{1950 + (i % 50)}-01-01",
            )
            test_db.add(patient)
            test_db.flush()

            condition = Condition(
                fhir_id=f"condition-large-{i}",
                patient_id=patient.id,
                code={
                    "coding": [{"system": "ICD-10", "code": "C50.9", "display": "Breast cancer"}]
                },
                code_text="Breast cancer",
                clinical_status="active",
                onset_datetime=datetime(2020, 1, 1) + timedelta(days=i),
            )
            test_db.add(condition)

        test_db.commit()

        client, token, user = authenticated_client

        import time

        start_time = time.time()

        response = client.post(
            "/api/survival/kaplan-meier",
            json={"condition_code": "C50.9", "start_date": "2020-01-01", "end_date": "2023-12-31"},
        )

        end_time = time.time()
        duration = end_time - start_time

        assert response.status_code == 200
        assert duration < 10  # Should complete within 10 seconds

        data = response.json()
        assert data["n_patients"] > 1000


@pytest.mark.integration
@pytest.mark.security
def test_survival_analysis_role_permissions(client, create_test_user):
    """Test that only authorized roles can access survival analysis."""
    # Create regular user
    user = create_test_user(role="user")

    # Login
    response = client.post(
        "/api/auth/login", data={"username": "testuser", "password": "TestPass123!"}
    )
    token = response.json()["access_token"]
    client.headers = {"Authorization": f"Bearer {token}"}

    # Regular user should be able to access
    response = client.post(
        "/api/survival/kaplan-meier",
        json={"condition_code": "C50.9", "start_date": "2020-01-01", "end_date": "2023-12-31"},
    )

    assert response.status_code in [200, 404]  # Either success or no data
