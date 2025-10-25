# FHIR ETL Service

ETL (Extract, Transform, Load) service for FHIR BULK DATA processing.

## Features

- 📥 **FHIR BULK DATA API Integration**
  - Kick-off bulk export requests
  - Poll export status
  - Download NDJSON files
  
- 🔄 **Transform**
  - Parse NDJSON FHIR resources
  - Extract and normalize data
  - Transform to database-ready format
  
- 💾 **Load**
  - Load transformed data into PostgreSQL
  - Handle conflicts and updates
  - Batch processing

## Supported Resources

- Patient
- Condition
- Encounter
- Observation
- (Extensible to other FHIR resources)

## Installation

```bash
pip install -r requirements.txt
```

## Environment Variables

```env
DATABASE_URL=postgresql://fhir_user:fhir_password@localhost:5432/fhir_analytics
FHIR_SERVER_URL=https://hapi.fhir.org/baseR4
BULK_DATA_DIR=/data/bulk
REDIS_URL=redis://localhost:6379/0
```

## Usage

```bash
uvicorn main:app --port 8001 --reload
```

## API Endpoints

### Bulk Data Export

**Kick-off Export**
```bash
POST /api/bulk-data/kick-off
{
  "fhir_server_url": "https://hapi.fhir.org/baseR4",
  "resource_types": ["Patient", "Condition", "Encounter"],
  "since": "2024-01-01T00:00:00Z",
  "bearer_token": "optional-token"
}
```

**Get Export Status**
```bash
GET /api/bulk-data/status/{job_id}
```

**List All Jobs**
```bash
GET /api/bulk-data/jobs
```

### Transform

**Process NDJSON Files**
```bash
POST /api/transform/process
{
  "job_id": "abc123",
  "resource_types": ["Patient", "Condition"]
}
```

**Load to Database**
```bash
POST /api/transform/load-to-database
{
  "job_id": "abc123",
  "resource_types": ["Patient", "Condition"]
}
```

## FHIR Bulk Data Workflow

1. **Kick-off Export**: Initiate bulk export on FHIR server
2. **Poll Status**: Wait for export to complete
3. **Download Files**: Download NDJSON files
4. **Transform**: Parse and transform FHIR resources
5. **Load**: Insert data into PostgreSQL

## FHIR Resource Transformation

### Patient
- Extract demographics (name, gender, birthDate)
- Parse identifiers and contact info
- Store raw FHIR resource

### Condition
- Extract diagnosis codes and text
- Parse clinical status
- Link to patient and encounter

### Encounter
- Extract encounter details
- Parse period and location
- Link to patient

### Observation
- Extract observation values
- Parse codes and units
- Link to patient and encounter

## Data Storage

Data is stored in two formats:
1. **Normalized fields**: For efficient querying
2. **Raw FHIR JSON**: For complete data preservation

## Error Handling

- Failed records are logged
- Transactions are rolled back on error
- Detailed error messages in logs

## Performance

- Batch processing for large datasets
- Asynchronous file downloads
- Database connection pooling
- Configurable batch sizes

## License

MIT

