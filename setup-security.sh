#!/bin/bash

# FHIR Analytics Platform - Security Setup Helper Script
# This script helps generate secure passwords and create .env files

set -e

echo "=================================================="
echo "  FHIR Analytics Platform - Security Setup"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env already exists
if [ -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file already exists!${NC}"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 1
    fi
    mv .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo -e "${GREEN}✅ Backed up existing .env file${NC}"
fi

echo ""
echo "Generating secure keys and passwords..."
echo ""

# Generate secure passwords
JWT_SECRET=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-24)
REDIS_PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-24)

echo -e "${GREEN}✅ Generated JWT Secret (64 chars)${NC}"
echo -e "${GREEN}✅ Generated PostgreSQL password (24 chars)${NC}"
echo -e "${GREEN}✅ Generated Redis password (24 chars)${NC}"
echo ""

# Get admin password
echo "Please create an admin password."
echo -e "${YELLOW}Requirements:${NC}"
echo "  • At least 12 characters"
echo "  • Include uppercase letters (A-Z)"
echo "  • Include lowercase letters (a-z)"
echo "  • Include digits (0-9)"
echo "  • Include special characters (!@#\$%^&*)"
echo ""

while true; do
    read -sp "Enter admin password: " ADMIN_PASSWORD
    echo
    read -sp "Confirm admin password: " ADMIN_PASSWORD_CONFIRM
    echo
    
    if [ "$ADMIN_PASSWORD" != "$ADMIN_PASSWORD_CONFIRM" ]; then
        echo -e "${RED}❌ Passwords do not match. Try again.${NC}"
        echo ""
        continue
    fi
    
    # Basic password validation
    if [ ${#ADMIN_PASSWORD} -lt 12 ]; then
        echo -e "${RED}❌ Password must be at least 12 characters. Try again.${NC}"
        echo ""
        continue
    fi
    
    # Check for complexity (basic check)
    if ! echo "$ADMIN_PASSWORD" | grep -q "[A-Z]" || \
       ! echo "$ADMIN_PASSWORD" | grep -q "[a-z]" || \
       ! echo "$ADMIN_PASSWORD" | grep -q "[0-9]" || \
       ! echo "$ADMIN_PASSWORD" | grep -q "[!@#\$%^&*(),.?\":{}|<>]"; then
        echo -e "${RED}❌ Password must contain uppercase, lowercase, digit, and special character. Try again.${NC}"
        echo ""
        continue
    fi
    
    break
done

echo -e "${GREEN}✅ Admin password validated${NC}"
echo ""

# Get engineer password
echo "Please create an engineer password."
echo ""

while true; do
    read -sp "Enter engineer password: " ENGINEER_PASSWORD
    echo
    read -sp "Confirm engineer password: " ENGINEER_PASSWORD_CONFIRM
    echo
    
    if [ "$ENGINEER_PASSWORD" != "$ENGINEER_PASSWORD_CONFIRM" ]; then
        echo -e "${RED}❌ Passwords do not match. Try again.${NC}"
        echo ""
        continue
    fi
    
    if [ ${#ENGINEER_PASSWORD} -lt 12 ]; then
        echo -e "${RED}❌ Password must be at least 12 characters. Try again.${NC}"
        echo ""
        continue
    fi
    
    if ! echo "$ENGINEER_PASSWORD" | grep -q "[A-Z]" || \
       ! echo "$ENGINEER_PASSWORD" | grep -q "[a-z]" || \
       ! echo "$ENGINEER_PASSWORD" | grep -q "[0-9]" || \
       ! echo "$ENGINEER_PASSWORD" | grep -q "[!@#\$%^&*(),.?\":{}|<>]"; then
        echo -e "${RED}❌ Password must contain uppercase, lowercase, digit, and special character. Try again.${NC}"
        echo ""
        continue
    fi
    
    break
done

echo -e "${GREEN}✅ Engineer password validated${NC}"
echo ""

# Get domain for CORS
echo "Enter your domain for CORS (or press Enter for localhost):"
read -p "Domain (default: localhost): " DOMAIN
if [ -z "$DOMAIN" ]; then
    ALLOWED_ORIGINS="http://localhost:3000,http://localhost:8000"
else
    ALLOWED_ORIGINS="https://${DOMAIN},https://app.${DOMAIN}"
fi

echo ""
echo "Creating .env file..."
echo ""

# Create .env file
cat > .env << EOF
# FHIR Analytics Platform - Environment Configuration
# Generated on: $(date)
# DO NOT commit this file to version control!

# ============================================
# Database Configuration
# ============================================
POSTGRES_DB=fhir_analytics
POSTGRES_USER=fhir_user
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
DATABASE_URL=postgresql://fhir_user:${POSTGRES_PASSWORD}@postgres:5432/fhir_analytics

# ============================================
# Redis Configuration
# ============================================
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0

# ============================================
# JWT Security
# ============================================
JWT_SECRET=${JWT_SECRET}
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# ============================================
# Admin Credentials
# ============================================
ADMIN_USERNAME=admin
ADMIN_PASSWORD=${ADMIN_PASSWORD}
ADMIN_EMAIL=admin@fhir-analytics.local

# ============================================
# Engineer Credentials
# ============================================
ENGINEER_USERNAME=engineer
ENGINEER_PASSWORD=${ENGINEER_PASSWORD}
ENGINEER_EMAIL=engineer@fhir-analytics.local

# ============================================
# CORS Configuration
# ============================================
ALLOWED_ORIGINS=${ALLOWED_ORIGINS}

# ============================================
# FHIR Server
# ============================================
FHIR_SERVER_URL=https://hapi.fhir.org/baseR4

# ============================================
# Frontend Configuration
# ============================================
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ANALYTICS_URL=http://localhost:8002
REACT_APP_FHIR_CLIENT_ID=your-smart-client-id

# ============================================
# Environment
# ============================================
ENVIRONMENT=development
LOG_LEVEL=INFO

# ============================================
# Rate Limiting
# ============================================
API_RATE_LIMIT=100/minute
RETRY_MAX_ATTEMPTS=5
RETRY_BASE_DELAY=1.0
RETRY_MAX_DELAY=60.0
EOF

# Set proper permissions
chmod 600 .env

echo -e "${GREEN}✅ Created .env file with secure permissions (600)${NC}"
echo ""

# Save secrets to separate files for backup (optional)
echo "Saving secrets to secure files..."
echo "$JWT_SECRET" > .jwt_secret
echo "$POSTGRES_PASSWORD" > .postgres_password
echo "$REDIS_PASSWORD" > .redis_password
chmod 600 .jwt_secret .postgres_password .redis_password

echo -e "${GREEN}✅ Saved secrets to secure files${NC}"
echo ""

# Display summary
echo "=================================================="
echo "  Setup Complete!"
echo "=================================================="
echo ""
echo "Generated files:"
echo "  • .env (main configuration)"
echo "  • .jwt_secret (JWT secret backup)"
echo "  • .postgres_password (database password backup)"
echo "  • .redis_password (Redis password backup)"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT SECURITY REMINDERS:${NC}"
echo "  1. These files are NOT committed to git (.gitignore)"
echo "  2. Store passwords in a secure password manager"
echo "  3. Change admin/engineer passwords after first login"
echo "  4. For production, update ALLOWED_ORIGINS in .env"
echo "  5. Never share these credentials"
echo ""
echo "Next steps:"
echo "  1. Review .env file: cat .env"
echo "  2. Start services: docker-compose up -d"
echo "  3. Check logs: docker-compose logs -f"
echo "  4. Access frontend: http://localhost:3000"
echo ""
echo "Documentation:"
echo "  • Complete guide: SECURITY_SETUP_COMPLETE_GUIDE.md"
echo "  • Environment setup: ENV_SETUP_GUIDE.md"
echo ""
echo -e "${GREEN}✨ Ready to launch!${NC}"

