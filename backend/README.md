# FHIR Analytics Platform - Backend API

FastAPI-based backend service for FHIR data management and analytics.

## Features

- 🔐 **Authentication & Authorization**
  - JWT token-based authentication
  - Role-based access control (user, admin, engineer)
  - SMART on FHIR token support

- 📊 **Analytics APIs**
  - Overall statistics
  - Trend analysis
  - Diagnosis analysis
  - Patient demographics
  - Top conditions

- 💾 **Data Export**
  - Multiple format support (CSV, JSON, Excel, Parquet)
  - Configurable field selection
  - Date range filtering

- ⚙️ **Admin APIs**
  - BULK DATA fetch management
  - ETL job monitoring
  - Valueset management
  - API configuration

## Tech Stack

- **FastAPI** 0.104.1
- **SQLAlchemy** 2.0.23 (ORM)
- **PostgreSQL** (via psycopg2)
- **Pydantic** 2.5.0 (Data validation)
- **python-jose** (JWT handling)
- **Passlib** (Password hashing)
- **Pandas** (Data processing)
- **FHIR Client** 4.1.0

## Installation

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file:

```env
DATABASE_URL=postgresql://fhir_user:fhir_password@localhost:5432/fhir_analytics
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
FHIR_SERVER_URL=https://hapi.fhir.org/baseR4
REDIS_URL=redis://localhost:6379/0
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

## Database Setup

The application will automatically create tables on startup. To manually manage migrations:

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

## Development

```bash
uvicorn main:app --reload
```

Runs on http://localhost:8000

API documentation available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Production

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── auth.py          # Authentication endpoints
│   │       ├── analytics.py     # Analytics endpoints
│   │       ├── export.py        # Data export endpoints
│   │       └── admin.py         # Admin endpoints
│   ├── core/
│   │   ├── config.py           # Configuration
│   │   ├── database.py         # Database setup
│   │   └── security.py         # Security utilities
│   └── models/
│       ├── user.py             # User model
│       ├── fhir_resources.py   # FHIR resource models
│       ├── etl_job.py          # ETL job model
│       └── valueset.py         # Valueset model
├── main.py                     # Application entry point
├── requirements.txt
└── Dockerfile
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/auth/smart-auth` - SMART on FHIR authentication

### Analytics
- `GET /api/analytics/stats` - Overall statistics
- `GET /api/analytics/trends` - Trend data
- `GET /api/analytics/top-conditions` - Top conditions
- `GET /api/analytics/diagnosis` - Diagnosis analysis
- `GET /api/analytics/patient-demographics` - Patient demographics

### Export
- `POST /api/export` - Export data in various formats

### Admin (Engineers only)
- `GET /api/admin/etl-jobs` - Get ETL job history
- `POST /api/admin/bulk-data/fetch` - Fetch BULK DATA
- `GET /api/admin/etl-jobs/{job_id}/status` - Get job status
- `GET /api/admin/valuesets` - Get valuesets
- `POST /api/admin/valuesets` - Create valueset
- `PUT /api/admin/valuesets/{id}` - Update valueset
- `DELETE /api/admin/valuesets/{id}` - Delete valueset

## Database Models

### User
- User authentication and profile information
- Role-based access control

### FHIR Resources
- **Patient**: Patient demographics and identifiers
- **Condition**: Diagnosis and clinical conditions
- **Encounter**: Healthcare encounters
- **Observation**: Clinical observations and measurements

### ETL Job
- Track BULK DATA import jobs
- Monitor processing status and errors

### Valueset
- Code system definitions
- Value set expansions

## Security

- Password hashing with bcrypt
- JWT token authentication
- Role-based access control
- CORS configuration
- SQL injection protection via SQLAlchemy ORM
- Input validation with Pydantic

## HIPAA Compliance Considerations

- Database encryption at rest
- TLS/SSL for data in transit
- Audit logging
- Access control and authentication
- Data anonymization options
- Secure token management

## Testing

```bash
pytest
```

## License

MIT

