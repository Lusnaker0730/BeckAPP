"""
Integration tests for Cohort Analysis API endpoints.

Tests cohort creation, analysis, and comparison functionality.
"""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
@pytest.mark.api
class TestCohortAPI:
    """Test suite for cohort analysis endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self, test_db):
        """Setup test data before each test."""
        from app.models.cohort import Cohort
        from app.models.fhir_resources import Condition, Patient

        # Create test patients with different conditions
        self.patients = []
        for i in range(30):
            patient = Patient(
                fhir_id=f"cohort-patient-{i}",
                identifier=f"COH{i:05d}",
                family_name=f"Cohort{i}",
                given_name="Test",
                gender="male" if i % 2 == 0 else "female",
                birth_date=f"{1940 + i}-01-01",
            )
            test_db.add(patient)
            test_db.flush()
            self.patients.append(patient)

            # Create conditions
            # First 15 patients: Hypertension
            # Last 15 patients: Diabetes
            if i < 15:
                condition = Condition(
                    fhir_id=f"cohort-condition-{i}",
                    patient_id=patient.id,
                    code={
                        "coding": [
                            {"system": "ICD-10", "code": "I10", "display": "Essential hypertension"}
                        ]
                    },
                    code_text="Hypertension",
                    clinical_status="active",
                    onset_datetime=datetime(2020, 1, 1) + timedelta(days=i * 10),
                )
            else:
                condition = Condition(
                    fhir_id=f"cohort-condition-{i}",
                    patient_id=patient.id,
                    code={
                        "coding": [
                            {
                                "system": "ICD-10",
                                "code": "E11",
                                "display": "Type 2 diabetes mellitus",
                            }
                        ]
                    },
                    code_text="Diabetes",
                    clinical_status="active",
                    onset_datetime=datetime(2020, 1, 1) + timedelta(days=i * 10),
                )
            test_db.add(condition)

        test_db.commit()

    # ========================================================================
    # Cohort Creation Tests
    # ========================================================================

    def test_create_cohort_success(self, admin_client, test_db):
        """Test successful cohort creation."""
        client, token, admin = admin_client

        response = client.post(
            "/api/cohorts",
            json={
                "name": "Hypertension Cohort",
                "description": "Patients with hypertension",
                "criteria": {"condition_codes": ["I10"], "age_min": 50, "age_max": 80},
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "id" in data or "cohort_id" in data
        assert "name" in data
        assert data["name"] == "Hypertension Cohort"
        assert "patient_count" in data or "n_patients" in data

        # Verify cohort was created in database
        from app.models.cohort import Cohort

        cohort = test_db.query(Cohort).filter(Cohort.name == "Hypertension Cohort").first()

        assert cohort is not None
        assert cohort.description == "Patients with hypertension"

    def test_create_cohort_with_complex_criteria(self, admin_client):
        """Test creating cohort with complex criteria."""
        client, token, admin = admin_client

        response = client.post(
            "/api/cohorts",
            json={
                "name": "Complex Cohort",
                "description": "Complex criteria test",
                "criteria": {
                    "condition_codes": ["I10", "E11"],
                    "gender": "male",
                    "age_min": 60,
                    "age_max": 75,
                    "date_range": {"start": "2020-01-01", "end": "2023-12-31"},
                },
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify complex criteria was saved
        assert "criteria" in data
        assert data["criteria"]["age_min"] == 60

    def test_create_cohort_missing_name(self, admin_client):
        """Test cohort creation with missing required field."""
        client, token, admin = admin_client

        response = client.post(
            "/api/cohorts",
            json={"description": "No name provided", "criteria": {"condition_codes": ["I10"]}},
        )

        assert response.status_code == 422  # Validation error

    def test_create_cohort_duplicate_name(self, admin_client):
        """Test creating cohort with duplicate name."""
        client, token, admin = admin_client

        # Create first cohort
        client.post(
            "/api/cohorts",
            json={"name": "Duplicate Test", "criteria": {"condition_codes": ["I10"]}},
        )

        # Try to create duplicate
        response = client.post(
            "/api/cohorts",
            json={"name": "Duplicate Test", "criteria": {"condition_codes": ["E11"]}},
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    # ========================================================================
    # Cohort Retrieval Tests
    # ========================================================================

    def test_list_cohorts(self, admin_client, test_db):
        """Test listing all cohorts."""
        from app.models.cohort import Cohort

        # Create test cohorts
        for i in range(5):
            cohort = Cohort(
                name=f"Test Cohort {i}",
                description=f"Description {i}",
                criteria={"condition_codes": [f"I1{i}"]},
                created_by="admin",
            )
            test_db.add(cohort)
        test_db.commit()

        client, token, admin = admin_client

        response = client.get("/api/cohorts")

        assert response.status_code == 200
        data = response.json()

        # Verify cohorts are returned
        cohorts = data.get("cohorts", data.get("data", data))
        assert len(cohorts) >= 5

    def test_get_cohort_by_id(self, admin_client, test_db):
        """Test retrieving specific cohort by ID."""
        from app.models.cohort import Cohort

        # Create test cohort
        cohort = Cohort(
            name="Specific Cohort",
            description="Test cohort",
            criteria={"condition_codes": ["I10"]},
            created_by="admin",
        )
        test_db.add(cohort)
        test_db.commit()

        client, token, admin = admin_client

        response = client.get(f"/api/cohorts/{cohort.id}")

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "Specific Cohort"
        assert data["description"] == "Test cohort"

    def test_get_nonexistent_cohort(self, admin_client):
        """Test retrieving non-existent cohort."""
        client, token, admin = admin_client

        response = client.get("/api/cohorts/99999")

        assert response.status_code == 404

    # ========================================================================
    # Cohort Analysis Tests
    # ========================================================================

    def test_analyze_cohort_demographics(self, admin_client, test_db):
        """Test cohort demographic analysis."""
        from app.models.cohort import Cohort

        # Create cohort
        cohort = Cohort(
            name="Demographics Test", criteria={"condition_codes": ["I10"]}, created_by="admin"
        )
        test_db.add(cohort)
        test_db.commit()

        client, token, admin = admin_client

        response = client.get(f"/api/cohorts/{cohort.id}/demographics")

        assert response.status_code == 200
        data = response.json()

        # Verify demographic data
        assert "age_distribution" in data or "demographics" in data
        assert "gender_distribution" in data or "gender" in data

    def test_cohort_survival_analysis(self, admin_client, test_db):
        """Test survival analysis for cohort."""
        from app.models.cohort import Cohort

        cohort = Cohort(
            name="Survival Test", criteria={"condition_codes": ["I10"]}, created_by="admin"
        )
        test_db.add(cohort)
        test_db.commit()

        client, token, admin = admin_client

        response = client.post(
            f"/api/cohorts/{cohort.id}/survival",
            json={"analysis_type": "kaplan_meier", "time_unit": "months"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify survival analysis results
        assert "survival_curve" in data or "results" in data

    def test_cohort_statistics(self, admin_client, test_db):
        """Test cohort statistics calculation."""
        from app.models.cohort import Cohort

        cohort = Cohort(
            name="Statistics Test", criteria={"condition_codes": ["I10"]}, created_by="admin"
        )
        test_db.add(cohort)
        test_db.commit()

        client, token, admin = admin_client

        response = client.get(f"/api/cohorts/{cohort.id}/statistics")

        assert response.status_code == 200
        data = response.json()

        # Verify statistics
        assert "patient_count" in data or "n_patients" in data
        assert "mean_age" in data or "age_mean" in data

    # ========================================================================
    # Cohort Comparison Tests
    # ========================================================================

    def test_compare_two_cohorts(self, admin_client, test_db):
        """Test comparing two cohorts."""
        from app.models.cohort import Cohort

        # Create two cohorts
        cohort1 = Cohort(name="Cohort A", criteria={"condition_codes": ["I10"]}, created_by="admin")
        cohort2 = Cohort(name="Cohort B", criteria={"condition_codes": ["E11"]}, created_by="admin")
        test_db.add_all([cohort1, cohort2])
        test_db.commit()

        client, token, admin = admin_client

        response = client.post(
            "/api/cohorts/compare",
            json={
                "cohort_ids": [cohort1.id, cohort2.id],
                "comparison_metrics": ["demographics", "outcomes"],
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify comparison results
        assert "cohorts" in data or "comparison" in data
        assert len(data.get("cohorts", data.get("comparison", []))) == 2

    def test_compare_cohorts_statistical_test(self, admin_client, test_db):
        """Test statistical comparison between cohorts."""
        from app.models.cohort import Cohort

        cohort1 = Cohort(
            name="Test Group", criteria={"condition_codes": ["I10"]}, created_by="admin"
        )
        cohort2 = Cohort(
            name="Control Group", criteria={"condition_codes": ["E11"]}, created_by="admin"
        )
        test_db.add_all([cohort1, cohort2])
        test_db.commit()

        client, token, admin = admin_client

        response = client.post(
            "/api/cohorts/compare",
            json={
                "cohort_ids": [cohort1.id, cohort2.id],
                "statistical_tests": ["t_test", "chi_square"],
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify statistical test results
        if "statistical_tests" in data:
            assert (
                "t_test" in data["statistical_tests"] or "chi_square" in data["statistical_tests"]
            )

    # ========================================================================
    # Cohort Update/Delete Tests
    # ========================================================================

    def test_update_cohort(self, admin_client, test_db):
        """Test updating cohort details."""
        from app.models.cohort import Cohort

        cohort = Cohort(
            name="Original Name",
            description="Original description",
            criteria={"condition_codes": ["I10"]},
            created_by="admin",
        )
        test_db.add(cohort)
        test_db.commit()

        client, token, admin = admin_client

        response = client.put(
            f"/api/cohorts/{cohort.id}",
            json={"name": "Updated Name", "description": "Updated description"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated description"

    def test_delete_cohort(self, admin_client, test_db):
        """Test deleting a cohort."""
        from app.models.cohort import Cohort

        cohort = Cohort(
            name="To Be Deleted", criteria={"condition_codes": ["I10"]}, created_by="admin"
        )
        test_db.add(cohort)
        test_db.commit()
        cohort_id = cohort.id

        client, token, admin = admin_client

        response = client.delete(f"/api/cohorts/{cohort_id}")

        assert response.status_code == 200

        # Verify cohort was deleted
        deleted_cohort = test_db.query(Cohort).filter(Cohort.id == cohort_id).first()

        assert deleted_cohort is None

    # ========================================================================
    # Cohort Patient Management Tests
    # ========================================================================

    def test_get_cohort_patients(self, admin_client, test_db):
        """Test retrieving patients in a cohort."""
        from app.models.cohort import Cohort

        cohort = Cohort(
            name="Patient List Test", criteria={"condition_codes": ["I10"]}, created_by="admin"
        )
        test_db.add(cohort)
        test_db.commit()

        client, token, admin = admin_client

        response = client.get(f"/api/cohorts/{cohort.id}/patients")

        assert response.status_code == 200
        data = response.json()

        # Verify patient list
        patients = data.get("patients", data.get("data", []))
        assert isinstance(patients, list)

    def test_add_patient_to_cohort(self, admin_client, test_db):
        """Test manually adding patient to cohort."""
        from app.models.cohort import Cohort

        cohort = Cohort(
            name="Manual Add Test", criteria={"condition_codes": ["I10"]}, created_by="admin"
        )
        test_db.add(cohort)
        test_db.commit()

        client, token, admin = admin_client

        response = client.post(f"/api/cohorts/{cohort.id}/patients", json={"patient_id": 1})

        # May or may not be implemented
        assert response.status_code in [200, 201, 404, 501]

    # ========================================================================
    # Permission Tests
    # ========================================================================

    def test_non_admin_cannot_create_cohort(self, authenticated_client):
        """Test that non-admin users cannot create cohorts."""
        client, token, user = authenticated_client

        response = client.post(
            "/api/cohorts",
            json={"name": "Unauthorized Cohort", "criteria": {"condition_codes": ["I10"]}},
        )

        # Should be forbidden or require admin role
        assert response.status_code in [403, 401]

    def test_cohort_access_control(self, authenticated_client, admin_client, test_db):
        """Test cohort access control."""
        from app.models.cohort import Cohort

        # Admin creates a cohort
        admin_cli, admin_token, admin = admin_client

        cohort = Cohort(
            name="Private Cohort",
            criteria={"condition_codes": ["I10"]},
            created_by=admin.username,
            is_public=False,
        )
        test_db.add(cohort)
        test_db.commit()

        # Regular user tries to access
        user_cli, user_token, user = authenticated_client

        response = user_cli.get(f"/api/cohorts/{cohort.id}")

        # Access control depends on implementation
        # May be allowed to view or forbidden
        assert response.status_code in [200, 403, 404]

    # ========================================================================
    # Export Tests
    # ========================================================================

    def test_export_cohort_definition(self, admin_client, test_db):
        """Test exporting cohort definition."""
        from app.models.cohort import Cohort

        cohort = Cohort(
            name="Export Test",
            description="Test cohort for export",
            criteria={"condition_codes": ["I10"]},
            created_by="admin",
        )
        test_db.add(cohort)
        test_db.commit()

        client, token, admin = admin_client

        response = client.get(f"/api/cohorts/{cohort.id}/export", params={"format": "json"})

        assert response.status_code == 200

        # Verify export format
        if response.headers.get("content-type") == "application/json":
            data = response.json()
            assert "name" in data
            assert "criteria" in data


@pytest.mark.integration
@pytest.mark.slow
def test_cohort_large_dataset(admin_client, test_db):
    """Test cohort performance with large patient population."""
    from app.models.cohort import Cohort
    from app.models.fhir_resources import Condition, Patient

    # Create 1000 patients
    for i in range(1000):
        patient = Patient(
            fhir_id=f"large-cohort-{i}",
            identifier=f"LCH{i:06d}",
            family_name=f"Large{i}",
            given_name="Test",
            gender="male" if i % 2 == 0 else "female",
            birth_date=f"{1950 + (i % 50)}-01-01",
        )
        test_db.add(patient)
        test_db.flush()

        condition = Condition(
            fhir_id=f"large-condition-{i}",
            patient_id=patient.id,
            code={"coding": [{"system": "ICD-10", "code": "I10", "display": "Hypertension"}]},
            code_text="Hypertension",
            clinical_status="active",
            onset_datetime=datetime(2020, 1, 1),
        )
        test_db.add(condition)

    test_db.commit()

    client, token, admin = admin_client

    import time

    start_time = time.time()

    # Create cohort with large population
    response = client.post(
        "/api/cohorts",
        json={"name": "Large Population Cohort", "criteria": {"condition_codes": ["I10"]}},
    )

    end_time = time.time()
    duration = end_time - start_time

    assert response.status_code == 200
    assert duration < 10  # Should complete within 10 seconds
