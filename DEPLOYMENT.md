# FHIR Analytics Platform - Deployment Guide

Complete deployment guide for production and development environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Development Setup](#development-setup)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Configuration](#configuration)
- [Security](#security)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- **Docker** >= 20.10
- **Docker Compose** >= 2.0
- **Node.js** >= 18.x (for frontend development)
- **Python** >= 3.11 (for backend development)
- **PostgreSQL** >= 15

### System Requirements

**Minimum:**
- CPU: 4 cores
- RAM: 8 GB
- Storage: 50 GB

**Recommended:**
- CPU: 8 cores
- RAM: 16 GB
- Storage: 200 GB SSD

## Development Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd BeckAPP
```

### 2. Setup Environment Variables

Create `.env` files in each service directory:

```bash
# Copy example env files
cp frontend/.env.example frontend/.env
cp backend/.env.example backend/.env
cp etl-service/.env.example etl-service/.env
cp analytics-service/.env.example analytics-service/.env
```

### 3. Start PostgreSQL

```bash
docker-compose up -d postgres
```

### 4. Run Services Individually

**Frontend:**
```bash
cd frontend
npm install
npm start
```

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

**ETL Service:**
```bash
cd etl-service
pip install -r requirements.txt
uvicorn main:app --port 8001 --reload
```

**Analytics Service:**
```bash
cd analytics-service
pip install -r requirements.txt
uvicorn main:app --port 8002 --reload
```

## Docker Deployment

### Quick Start

```bash
docker-compose up -d
```

This will start all services:
- PostgreSQL (port 5432)
- Backend API (port 8000)
- ETL Service (port 8001)
- Analytics Service (port 8002)
- Frontend (port 3000)

### Check Service Status

```bash
docker-compose ps
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
```

### Stop Services

```bash
docker-compose down
```

### Rebuild Services

```bash
docker-compose up -d --build
```

## Production Deployment

### 1. Prepare Environment

Update production environment variables:

```bash
# backend/.env
DATABASE_URL=postgresql://prod_user:secure_password@db-host:5432/fhir_analytics
JWT_SECRET=<generate-secure-random-key>
FHIR_SERVER_URL=https://your-fhir-server.com/fhir
ALLOWED_ORIGINS=https://your-domain.com

# frontend/.env
REACT_APP_API_URL=https://api.your-domain.com
REACT_APP_FHIR_CLIENT_ID=your-production-client-id
```

### 2. Build Production Images

```bash
# Build all services
docker-compose -f docker-compose.prod.yml build

# Tag images
docker tag beckapp_backend:latest your-registry/fhir-backend:1.0.0
docker tag beckapp_frontend:latest your-registry/fhir-frontend:1.0.0
docker tag beckapp_etl:latest your-registry/fhir-etl:1.0.0
docker tag beckapp_analytics:latest your-registry/fhir-analytics:1.0.0

# Push to registry
docker push your-registry/fhir-backend:1.0.0
docker push your-registry/fhir-frontend:1.0.0
docker push your-registry/fhir-etl:1.0.0
docker push your-registry/fhir-analytics:1.0.0
```

### 3. Database Setup

```bash
# Run migrations
docker exec -it fhir-backend alembic upgrade head

# Or use init script
psql -h db-host -U fhir_user -d fhir_analytics -f docker/init-db.sql
```

### 4. SSL/TLS Configuration

Use reverse proxy (Nginx) for SSL termination:

```nginx
server {
    listen 443 ssl http2;
    server_name api.your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 5. Deploy with Docker Swarm or Kubernetes

**Docker Swarm:**
```bash
docker stack deploy -c docker-compose.prod.yml fhir-stack
```

**Kubernetes:**
```bash
kubectl apply -f k8s/
```

## Configuration

### Backend Configuration

Key settings in `backend/.env`:

```env
# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# JWT Security
JWT_SECRET=<secret-key>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# FHIR Server
FHIR_SERVER_URL=https://fhir-server.com/fhir

# CORS
ALLOWED_ORIGINS=https://frontend.com,https://app.com
```

### Frontend Configuration

Key settings in `frontend/.env`:

```env
REACT_APP_API_URL=https://api.your-domain.com
REACT_APP_ANALYTICS_URL=https://analytics.your-domain.com
REACT_APP_FHIR_CLIENT_ID=your-client-id
REACT_APP_FHIR_REDIRECT_URI=https://your-domain.com/callback
REACT_APP_FHIR_SCOPE=patient/*.read launch/patient openid fhirUser
```

## Security

### Security Checklist

- [ ] Change default passwords
- [ ] Generate secure JWT secret
- [ ] Enable HTTPS/TLS
- [ ] Configure CORS properly
- [ ] Enable database encryption at rest
- [ ] Setup backup strategy
- [ ] Enable audit logging
- [ ] Implement rate limiting
- [ ] Regular security updates
- [ ] Setup firewall rules

### Generate Secure Keys

```bash
# JWT Secret
openssl rand -hex 32

# PostgreSQL Password
openssl rand -base64 32
```

### Database Encryption

Enable PostgreSQL encryption:

```sql
-- Enable pgcrypto extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypt sensitive fields
ALTER TABLE patients 
ALTER COLUMN raw_data TYPE bytea 
USING pgp_sym_encrypt(raw_data::text, 'encryption-key');
```

## Monitoring

### Health Checks

All services expose `/health` endpoints:

```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
```

### Logging

Centralized logging with ELK stack:

```yaml
# docker-compose.monitoring.yml
services:
  elasticsearch:
    image: elasticsearch:8.10.0
    ...
  
  logstash:
    image: logstash:8.10.0
    ...
  
  kibana:
    image: kibana:8.10.0
    ...
```

### Metrics

Prometheus + Grafana for metrics:

```yaml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
```

## Troubleshooting

### Common Issues

**Database Connection Error:**
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Test connection
psql -h localhost -U fhir_user -d fhir_analytics
```

**Port Already in Use:**
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>
```

**Frontend Build Errors:**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules
rm -rf node_modules package-lock.json

# Reinstall
npm install
```

**Backend Import Errors:**
```bash
# Recreate virtual environment
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Debug Mode

Enable debug logging:

```python
# backend/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Tuning

**PostgreSQL:**
```sql
-- Increase connection pool
ALTER SYSTEM SET max_connections = 200;

-- Increase shared buffers
ALTER SYSTEM SET shared_buffers = '2GB';

-- Reload configuration
SELECT pg_reload_conf();
```

**Backend:**
```bash
# Increase workers
uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000
```

## Backup & Recovery

### Database Backup

```bash
# Backup
pg_dump -h localhost -U fhir_user fhir_analytics > backup.sql

# Restore
psql -h localhost -U fhir_user -d fhir_analytics < backup.sql
```

### Automated Backups

```bash
# Add to crontab
0 2 * * * pg_dump -h localhost -U fhir_user fhir_analytics > /backups/backup_$(date +\%Y\%m\%d).sql
```

## Support

For issues and questions:
- GitHub Issues: <repository-url>/issues
- Documentation: <docs-url>
- Email: support@fhir-analytics.com

## License

MIT License

