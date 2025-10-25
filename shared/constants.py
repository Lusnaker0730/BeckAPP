"""
Shared constants across all services
"""

# FHIR Resource Types
FHIR_RESOURCE_TYPES = [
    "Patient",
    "Condition",
    "Encounter",
    "Observation",
    "Procedure",
    "Medication",
    "MedicationRequest",
    "AllergyIntolerance",
    "DiagnosticReport",
    "Immunization"
]

# User Roles
USER_ROLES = {
    "USER": "user",
    "ADMIN": "admin",
    "ENGINEER": "engineer",
    "CLINICIAN": "clinician"
}

# ETL Job Status
ETL_STATUS = {
    "PENDING": "pending",
    "RUNNING": "running",
    "COMPLETED": "completed",
    "FAILED": "failed",
    "CANCELLED": "cancelled"
}

# Export Formats
EXPORT_FORMATS = ["csv", "json", "excel", "parquet"]

# Diagnosis Codes
DIAGNOSIS_CODES = {
    "influenza": ["J09", "J10", "J11"],
    "myocardial_infarction": ["I21", "I22"],
    "lung_adenocarcinoma": ["C34.1"],
    "diabetes": ["E10", "E11", "E12", "E13", "E14"],
    "hypertension": ["I10", "I11", "I12", "I13", "I15"],
    "copd": ["J44"]
}

# FHIR Scopes
FHIR_SCOPES = {
    "PATIENT_READ": "patient/*.read",
    "PATIENT_WRITE": "patient/*.write",
    "USER_READ": "user/*.read",
    "LAUNCH": "launch/patient",
    "OPENID": "openid",
    "FHIR_USER": "fhirUser"
}

# Database Table Names
TABLE_NAMES = {
    "USERS": "users",
    "PATIENTS": "patients",
    "CONDITIONS": "conditions",
    "ENCOUNTERS": "encounters",
    "OBSERVATIONS": "observations",
    "ETL_JOBS": "etl_jobs",
    "VALUESETS": "valuesets"
}

# Chart Types
CHART_TYPES = ["bar", "line", "scatter", "pie", "doughnut", "radar"]

# Time Periods
TIME_PERIODS = {
    "DAILY": "daily",
    "WEEKLY": "weekly",
    "MONTHLY": "monthly",
    "QUARTERLY": "quarterly",
    "YEARLY": "yearly"
}

# Age Groups
AGE_GROUPS = ["0-18", "19-35", "36-50", "51-65", "65+"]

