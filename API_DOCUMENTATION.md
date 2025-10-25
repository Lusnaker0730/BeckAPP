# API Documentation

Complete API reference for the FHIR Analytics Platform.

## Base URLs

- Backend API: `http://localhost:8000`
- ETL Service: `http://localhost:8001`
- Analytics Service: `http://localhost:8002`

## Authentication

All protected endpoints require a Bearer token in the Authorization header:

```bash
Authorization: Bearer <access_token>
```

### Obtain Token

**POST** `/api/auth/login`

```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "name": "Administrator",
    "role": "admin"
  }
}
```

## Backend API Endpoints

### Authentication

#### Register User

**POST** `/api/auth/register`

```json
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "New User",
  "role": "user"
}
```

#### Login

**POST** `/api/auth/login`

```json
{
  "username": "admin",
  "password": "admin123"
}
```

### Analytics

#### Get Statistics

**GET** `/api/analytics/stats`

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "totalPatients": 5000,
  "totalConditions": 12000,
  "totalEncounters": 25000,
  "totalObservations": 50000
}
```

#### Get Trends

**GET** `/api/analytics/trends?months=12`

**Parameters:**
- `months` (int): Number of months to include (1-24)

**Response:**
```json
{
  "labels": ["2023-01", "2023-02", "2023-03"],
  "values": [1200, 1350, 1280]
}
```

#### Get Top Conditions

**GET** `/api/analytics/top-conditions?limit=5`

**Parameters:**
- `limit` (int): Number of top conditions (1-20)

**Response:**
```json
{
  "labels": ["Hypertension", "Diabetes", "Influenza"],
  "values": [1250, 980, 875]
}
```

#### Get Diagnosis Analysis

**GET** `/api/analytics/diagnosis?diagnosis=influenza&timeRange=yearly`

**Parameters:**
- `diagnosis` (string): Diagnosis type (influenza, diabetes, etc.)
- `timeRange` (string): Time range (monthly, quarterly, yearly)

**Response:**
```json
{
  "labels": ["2020", "2021", "2022", "2023"],
  "counts": [1250, 1380, 1520, 1450],
  "totalCount": 5600,
  "averageCount": 1400,
  "peakCount": 1520,
  "growthRate": 15.2,
  "details": [
    {
      "period": "2020",
      "count": 1250,
      "change": 0,
      "percentage": 22.3
    }
  ]
}
```

#### Get Patient Demographics

**GET** `/api/analytics/patient-demographics`

**Response:**
```json
{
  "gender": {
    "labels": ["Male", "Female", "Other"],
    "values": [4200, 4800, 150]
  },
  "ageGroups": {
    "labels": ["0-18", "19-35", "36-50", "51-65", "65+"],
    "values": [1250, 2340, 3120, 2890, 1980]
  }
}
```

### Export

#### Export Data

**POST** `/api/export`

**Body:**
```json
{
  "dataType": "conditions",
  "format": "csv",
  "dateFrom": "2023-01-01",
  "dateTo": "2023-12-31",
  "includeFields": {
    "patient": true,
    "condition": true,
    "encounter": true,
    "observation": false
  }
}
```

**Parameters:**
- `dataType`: patients, conditions, encounters, observations, combined
- `format`: csv, json, excel, parquet

**Response:** File download

### Admin (Engineers Only)

#### Get ETL Jobs

**GET** `/api/admin/etl-jobs?limit=50`

**Headers:** `Authorization: Bearer <token>` (role: admin or engineer)

**Response:**
```json
[
  {
    "id": "job-123",
    "resourceType": "Patient",
    "status": "completed",
    "startTime": "2024-01-15T10:00:00Z",
    "endTime": "2024-01-15T10:15:00Z",
    "recordsProcessed": 5000,
    "recordsFailed": 5
  }
]
```

#### Fetch Bulk Data

**POST** `/api/admin/bulk-data/fetch`

**Body:**
```json
{
  "fhirServerUrl": "https://hapi.fhir.org/baseR4",
  "resourceTypes": ["Patient", "Condition", "Encounter"],
  "since": "2024-01-01T00:00:00Z"
}
```

#### Get Valuesets

**GET** `/api/admin/valuesets`

**Response:**
```json
[
  {
    "id": 1,
    "name": "ICD-10 Diagnoses",
    "url": "http://hl7.org/fhir/sid/icd-10",
    "version": "2024",
    "code_system": "ICD-10",
    "description": "International Classification of Diseases",
    "code_count": 15342,
    "updated_at": "2024-01-15T00:00:00Z"
  }
]
```

#### Create Valueset

**POST** `/api/admin/valuesets`

**Body:**
```json
{
  "name": "Custom Diagnoses",
  "url": "http://example.com/valuesets/custom",
  "version": "1.0",
  "description": "Custom diagnosis codes",
  "code_system": "Custom",
  "codes": [
    {
      "code": "CUSTOM001",
      "display": "Custom Diagnosis 1"
    }
  ]
}
```

## ETL Service Endpoints

### Bulk Data Export

#### Kick-off Export

**POST** `/api/bulk-data/kick-off`

```json
{
  "fhir_server_url": "https://hapi.fhir.org/baseR4",
  "resource_types": ["Patient", "Condition"],
  "since": "2024-01-01T00:00:00Z",
  "bearer_token": "optional-token"
}
```

**Response:**
```json
{
  "job_id": "export-123",
  "status": "accepted",
  "message": "Bulk export initiated",
  "status_url": "https://fhir-server.com/bulkstatus/123"
}
```

#### Get Export Status

**GET** `/api/bulk-data/status/{job_id}`

**Response:**
```json
{
  "status": "completed",
  "status_url": "https://fhir-server.com/bulkstatus/123",
  "fhir_server_url": "https://hapi.fhir.org/baseR4",
  "resource_types": ["Patient", "Condition"],
  "started_at": "2024-01-15T10:00:00Z",
  "completed_at": "2024-01-15T10:15:00Z",
  "files": [
    {
      "resource_type": "Patient",
      "filename": "Patient.ndjson",
      "size": 1048576
    }
  ]
}
```

#### List Jobs

**GET** `/api/bulk-data/jobs`

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "export-123",
      "status": "completed",
      "started_at": "2024-01-15T10:00:00Z",
      "resource_types": ["Patient", "Condition"]
    }
  ]
}
```

### Transform

#### Process NDJSON

**POST** `/api/transform/process`

```json
{
  "job_id": "export-123",
  "resource_types": ["Patient", "Condition"]
}
```

**Response:**
```json
{
  "job_id": "export-123",
  "status": "completed",
  "records_processed": 5000,
  "records_failed": 5,
  "details": [
    {
      "resource_type": "Patient",
      "records_processed": 5000,
      "records_failed": 5,
      "output_file": "/data/bulk/export-123/transformed/Patient.json"
    }
  ]
}
```

#### Load to Database

**POST** `/api/transform/load-to-database`

```json
{
  "job_id": "export-123",
  "resource_types": ["Patient", "Condition"]
}
```

**Response:**
```json
{
  "job_id": "export-123",
  "status": "completed",
  "records_loaded": 4995,
  "records_failed": 5,
  "details": [
    {
      "resource_type": "Patient",
      "records_loaded": 4995,
      "records_failed": 5
    }
  ]
}
```

## Analytics Service Endpoints

### Visualization

#### Get Visualization Data

**GET** `/api/visualization?xAxis=age_group&yAxis=count&filter=all`

**Parameters:**
- `xAxis`: age_group, gender, condition_code, encounter_type, date
- `yAxis`: count, average, total
- `filter`: all, condition, timerange, location

**Response:**
```json
{
  "labels": ["0-18", "19-35", "36-50", "51-65", "65+"],
  "datasets": [
    {
      "label": "count",
      "data": [1250, 2340, 3120, 2890, 1980],
      "backgroundColor": ["rgba(37, 99, 235, 0.8)"],
      "borderColor": ["rgb(37, 99, 235)"],
      "borderWidth": 2
    }
  ]
}
```

### Statistics

#### Descriptive Statistics

**GET** `/api/statistics/descriptive?resource_type=conditions`

**Response:**
```json
{
  "total_count": 12000,
  "unique_patients": 5000,
  "unique_conditions": 150,
  "earliest_date": "2020-01-01T00:00:00Z",
  "latest_date": "2024-01-15T00:00:00Z"
}
```

#### Correlation Analysis

**GET** `/api/statistics/correlation?variable1=age&variable2=condition_count`

**Response:**
```json
{
  "correlation": 0.65,
  "p_value": 0.001,
  "sample_size": 5000,
  "interpretation": "Statistically significant moderate positive correlation (p < 0.05)"
}
```

#### Trend Analysis

**GET** `/api/statistics/trend-analysis?metric=condition_count&time_period=monthly`

**Response:**
```json
{
  "trend": "increasing",
  "slope": 12.5,
  "r_squared": 0.82,
  "p_value": 0.001,
  "data_points": 24,
  "interpretation": "The trend is increasing with R² = 0.820"
}
```

### Cohort Analysis

#### Define Cohort

**POST** `/api/cohort/define`

```json
{
  "name": "Diabetes Patients",
  "inclusion_criteria": {
    "condition": "diabetes",
    "age_min": 18,
    "age_max": 65,
    "gender": "male"
  },
  "exclusion_criteria": {}
}
```

**Response:**
```json
{
  "cohort_name": "Diabetes Patients",
  "cohort_size": 1250,
  "average_age": 52.3,
  "gender_distribution": {
    "male": 1250,
    "female": 0
  },
  "status": "created"
}
```

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized

```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden

```json
{
  "detail": "Insufficient permissions"
}
```

### 404 Not Found

```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Internal server error"
}
```

## Rate Limiting

Default rate limits:
- Authentication endpoints: 5 requests/minute
- Analytics endpoints: 60 requests/minute
- Export endpoints: 10 requests/hour

## Interactive API Documentation

Visit these URLs for interactive Swagger documentation:

- Backend: http://localhost:8000/docs
- ETL Service: http://localhost:8001/docs
- Analytics Service: http://localhost:8002/docs

## Postman Collection

A Postman collection is available at `docs/postman-collection.json` for easy API testing.

## Support

For API questions and issues:
- GitHub Issues: <repository-url>/issues
- Email: api-support@fhir-analytics.com

