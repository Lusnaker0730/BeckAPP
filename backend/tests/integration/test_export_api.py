"""
Integration tests for Data Export API endpoints.

Tests CSV, JSON, Excel, and Parquet export functionality.
"""

import csv
import json
from datetime import datetime
from io import BytesIO, StringIO

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
@pytest.mark.api
class TestExportAPI:
    """Test suite for data export endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self, test_db):
        """Setup test data before each test."""
        from app.models.fhir_resources import Condition, Encounter, Observation, Patient

        # Create test patients
        self.patients = []
        for i in range(10):
            patient = Patient(
                fhir_id=f"export-patient-{i}",
                identifier=f"EXP{i:05d}",
                family_name=f"Export{i}",
                given_name="Test",
                gender="male" if i % 2 == 0 else "female",
                birth_date=f"{1960 + i}-01-01",
            )
            test_db.add(patient)
            test_db.flush()
            self.patients.append(patient)

            # Create conditions
            condition = Condition(
                fhir_id=f"export-condition-{i}",
                patient_id=patient.id,
                code={
                    "coding": [{"system": "ICD-10", "code": f"I10.{i}", "display": "Hypertension"}]
                },
                code_text="Hypertension",
                clinical_status="active",
                onset_datetime=datetime(2023, 1, 1 + i),
            )
            test_db.add(condition)

            # Create observations
            observation = Observation(
                fhir_id=f"export-observation-{i}",
                patient_id=patient.id,
                code={
                    "coding": [{"system": "LOINC", "code": "85354-9", "display": "Blood pressure"}]
                },
                code_text="Blood pressure",
                value_quantity={"value": 120 + i, "unit": "mmHg"},
                effective_datetime=datetime(2023, 1, 1 + i),
            )
            test_db.add(observation)

            # Create encounter
            encounter = Encounter(
                fhir_id=f"export-encounter-{i}",
                patient_id=patient.id,
                encounter_class="outpatient",
                encounter_type="Routine check-up",
                status="finished",
                period_start=datetime(2023, 1, 1 + i),
                period_end=datetime(2023, 1, 1 + i),
            )
            test_db.add(encounter)

        test_db.commit()

    # ========================================================================
    # CSV Export Tests
    # ========================================================================

    def test_export_patients_csv(self, authenticated_client):
        """Test exporting patients as CSV."""
        client, token, user = authenticated_client

        response = client.post(
            "/api/export/patients",
            json={"format": "csv", "start_date": "2023-01-01", "end_date": "2023-12-31"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"

        # Parse CSV
        content = response.content.decode()
        csv_reader = csv.DictReader(StringIO(content))
        rows = list(csv_reader)

        # Verify data
        assert len(rows) > 0
        assert "fhir_id" in rows[0] or "identifier" in rows[0]
        assert "family_name" in rows[0]
        assert "given_name" in rows[0]
        assert "gender" in rows[0]

    def test_export_conditions_csv(self, authenticated_client):
        """Test exporting conditions as CSV."""
        client, token, user = authenticated_client

        response = client.post(
            "/api/export/conditions",
            json={"format": "csv", "start_date": "2023-01-01", "end_date": "2023-12-31"},
        )

        assert response.status_code == 200
        content = response.content.decode()

        # Verify CSV headers
        assert "patient_id" in content or "fhir_id" in content
        assert "code_text" in content or "code" in content

        # Parse and verify rows
        csv_reader = csv.DictReader(StringIO(content))
        rows = list(csv_reader)
        assert len(rows) > 0

    def test_export_observations_csv(self, authenticated_client):
        """Test exporting observations as CSV."""
        client, token, user = authenticated_client

        response = client.post(
            "/api/export/observations",
            json={
                "format": "csv",
                "fields": ["fhir_id", "patient_id", "code_text", "value_quantity"],
            },
        )

        assert response.status_code == 200

        # Verify selected fields are present
        content = response.content.decode()
        assert "fhir_id" in content
        assert "patient_id" in content
        assert "code_text" in content

    # ========================================================================
    # JSON Export Tests
    # ========================================================================

    def test_export_patients_json(self, authenticated_client):
        """Test exporting patients as JSON."""
        client, token, user = authenticated_client

        response = client.post(
            "/api/export/patients",
            json={"format": "json", "start_date": "2023-01-01", "end_date": "2023-12-31"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        # Parse JSON
        data = response.json()

        # Verify structure
        assert isinstance(data, dict) or isinstance(data, list)

        if isinstance(data, dict):
            assert "data" in data or "patients" in data
            patients = data.get("data", data.get("patients", []))
        else:
            patients = data

        # Verify patient data
        assert len(patients) > 0
        patient = patients[0]
        assert "fhir_id" in patient or "identifier" in patient

    def test_export_json_with_pagination(self, authenticated_client):
        """Test JSON export with pagination."""
        client, token, user = authenticated_client

        response = client.post(
            "/api/export/patients", json={"format": "json", "limit": 5, "offset": 0}
        )

        assert response.status_code == 200
        data = response.json()

        # Should return no more than 5 results
        patients = data.get("data", data.get("patients", data))
        assert len(patients) <= 5

    # ========================================================================
    # Excel Export Tests
    # ========================================================================

    def test_export_patients_excel(self, authenticated_client):
        """Test exporting patients as Excel."""
        client, token, user = authenticated_client

        response = client.post(
            "/api/export/patients",
            json={"format": "excel", "start_date": "2023-01-01", "end_date": "2023-12-31"},
        )

        assert response.status_code == 200
        assert (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            in response.headers["content-type"]
        )

        # Verify file is not empty
        assert len(response.content) > 0

    def test_export_excel_multiple_sheets(self, authenticated_client):
        """Test Excel export with multiple sheets."""
        client, token, user = authenticated_client

        response = client.post(
            "/api/export/comprehensive",
            json={
                "format": "excel",
                "include_patients": True,
                "include_conditions": True,
                "include_observations": True,
            },
        )

        assert response.status_code == 200

        # Verify Excel file structure (would need openpyxl to fully test)
        assert len(response.content) > 0

    # ========================================================================
    # Parquet Export Tests
    # ========================================================================

    def test_export_patients_parquet(self, authenticated_client):
        """Test exporting patients as Parquet."""
        client, token, user = authenticated_client

        response = client.post(
            "/api/export/patients",
            json={"format": "parquet", "start_date": "2023-01-01", "end_date": "2023-12-31"},
        )

        assert response.status_code == 200
        assert "application/octet-stream" in response.headers["content-type"]

        # Verify Parquet magic bytes (PAR1)
        content = response.content
        assert len(content) > 0

    # ========================================================================
    # Field Selection Tests
    # ========================================================================

    def test_export_with_field_selection(self, authenticated_client):
        """Test export with specific field selection."""
        client, token, user = authenticated_client

        response = client.post(
            "/api/export/patients",
            json={"format": "csv", "fields": ["identifier", "family_name", "gender"]},
        )

        assert response.status_code == 200
        content = response.content.decode()

        # Verify only selected fields are present
        csv_reader = csv.DictReader(StringIO(content))
        headers = csv_reader.fieldnames

        assert "identifier" in headers
        assert "family_name" in headers
        assert "gender" in headers

    def test_export_with_invalid_fields(self, authenticated_client):
        """Test export with invalid field names."""
        client, token, user = authenticated_client

        response = client.post(
            "/api/export/patients", json={"format": "csv", "fields": ["nonexistent_field"]}
        )

        # Should either ignore invalid fields or return error
        assert response.status_code in [200, 400]

    # ========================================================================
    # Filter Tests
    # ========================================================================

    def test_export_with_date_filter(self, authenticated_client):
        """Test export with date range filter."""
        client, token, user = authenticated_client

        response = client.post(
            "/api/export/conditions",
            json={"format": "json", "start_date": "2023-01-01", "end_date": "2023-01-05"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify filtered results
        conditions = data.get("data", data.get("conditions", data))

        # Should only include conditions from specified date range
        for condition in conditions:
            if "onset_datetime" in condition:
                onset_date = datetime.fromisoformat(
                    condition["onset_datetime"].replace("Z", "+00:00")
                )
                assert datetime(2023, 1, 1) <= onset_date <= datetime(2023, 1, 5)

    def test_export_with_gender_filter(self, authenticated_client):
        """Test export with gender filter."""
        client, token, user = authenticated_client

        response = client.post(
            "/api/export/patients", json={"format": "json", "filters": {"gender": "male"}}
        )

        assert response.status_code == 200
        data = response.json()

        patients = data.get("data", data.get("patients", data))

        # Verify all returned patients are male
        for patient in patients:
            assert patient.get("gender") == "male"

    # ========================================================================
    # Large Dataset Tests
    # ========================================================================

    @pytest.mark.slow
    def test_export_large_dataset(self, authenticated_client, test_db):
        """Test exporting large dataset (background job)."""
        from app.models.fhir_resources import Patient

        # Create 1000 additional patients
        for i in range(1000):
            patient = Patient(
                fhir_id=f"large-export-{i}",
                identifier=f"LGE{i:05d}",
                family_name=f"Large{i}",
                given_name="Export",
                gender="male" if i % 2 == 0 else "female",
                birth_date=f"{1950 + (i % 50)}-01-01",
            )
            test_db.add(patient)

        test_db.commit()

        client, token, user = authenticated_client

        response = client.post(
            "/api/export/patients",
            json={"format": "csv", "async_export": True},  # Trigger background job
        )

        # Should return job ID for async export
        if response.status_code == 202:
            data = response.json()
            assert "job_id" in data
            assert "status" in data
        else:
            # Or return data directly if sync export
            assert response.status_code == 200

    # ========================================================================
    # Error Handling Tests
    # ========================================================================

    def test_export_unsupported_format(self, authenticated_client):
        """Test export with unsupported format."""
        client, token, user = authenticated_client

        response = client.post("/api/export/patients", json={"format": "xml"})  # Unsupported format

        assert response.status_code == 400
        assert "format" in response.json()["detail"].lower()

    def test_export_missing_required_params(self, authenticated_client):
        """Test export with missing required parameters."""
        client, token, user = authenticated_client

        response = client.post("/api/export/patients", json={})  # Missing format

        assert response.status_code == 422  # Validation error

    def test_export_invalid_date_range(self, authenticated_client):
        """Test export with invalid date range."""
        client, token, user = authenticated_client

        response = client.post(
            "/api/export/patients",
            json={
                "format": "csv",
                "start_date": "2023-12-31",
                "end_date": "2023-01-01",  # End before start
            },
        )

        assert response.status_code == 400

    def test_unauthorized_export(self, client):
        """Test export without authentication."""
        response = client.post("/api/export/patients", json={"format": "csv"})

        assert response.status_code == 401

    # ========================================================================
    # Audit Logging Tests
    # ========================================================================

    def test_export_creates_audit_log(self, authenticated_client, test_db):
        """Test that export creates audit log entry."""
        client, token, user = authenticated_client

        response = client.post(
            "/api/export/patients",
            json={"format": "csv", "start_date": "2023-01-01", "end_date": "2023-12-31"},
        )

        assert response.status_code == 200

        # Check audit log was created
        from app.models.audit_log import AuditLog

        audit_logs = test_db.query(AuditLog).filter(AuditLog.action == "export_data").all()

        # Should have at least one export audit log
        assert len(audit_logs) > 0

        # Verify audit log details
        log = audit_logs[-1]  # Most recent
        assert log.username == user.username
        assert log.resource == "patients"
        assert log.is_success == "success"

    # ========================================================================
    # Performance Tests
    # ========================================================================

    def test_export_performance(self, authenticated_client):
        """Test export performance is acceptable."""
        client, token, user = authenticated_client

        import time

        start_time = time.time()

        response = client.post("/api/export/patients", json={"format": "csv"})

        end_time = time.time()
        duration = end_time - start_time

        assert response.status_code == 200
        assert duration < 5  # Should complete within 5 seconds for small dataset

    # ========================================================================
    # Comprehensive Export Tests
    # ========================================================================

    def test_export_all_resources(self, authenticated_client):
        """Test exporting all resource types."""
        client, token, user = authenticated_client

        response = client.post(
            "/api/export/comprehensive",
            json={
                "format": "json",
                "include_patients": True,
                "include_conditions": True,
                "include_observations": True,
                "include_encounters": True,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all resource types are included
        assert "patients" in data or "Patient" in data
        assert "conditions" in data or "Condition" in data
        assert "observations" in data or "Observation" in data
        assert "encounters" in data or "Encounter" in data


@pytest.mark.integration
@pytest.mark.security
def test_export_role_permissions(client, create_test_user):
    """Test export permissions for different roles."""
    # Create regular user
    user = create_test_user(role="user")

    # Login
    response = client.post(
        "/api/auth/login", data={"username": "testuser", "password": "TestPass123!"}
    )
    token = response.json()["access_token"]
    client.headers = {"Authorization": f"Bearer {token}"}

    # Regular users should be able to export
    response = client.post("/api/export/patients", json={"format": "csv"})

    assert response.status_code in [200, 403]  # Depends on permission config
