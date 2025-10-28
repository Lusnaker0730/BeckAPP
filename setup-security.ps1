# FHIR Analytics Platform - Security Setup Helper Script (PowerShell)
# This script helps generate secure passwords and create .env files

$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  FHIR Analytics Platform - Security Setup" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env already exists
if (Test-Path ".env") {
    Write-Host "⚠️  .env file already exists!" -ForegroundColor Yellow
    $overwrite = Read-Host "Do you want to overwrite it? (y/N)"
    if ($overwrite -ne "y" -and $overwrite -ne "Y") {
        Write-Host "Setup cancelled." -ForegroundColor Red
        exit 1
    }
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    Rename-Item -Path ".env" -NewName ".env.backup.$timestamp"
    Write-Host "✅ Backed up existing .env file" -ForegroundColor Green
}

Write-Host ""
Write-Host "Generating secure keys and passwords..." -ForegroundColor Cyan
Write-Host ""

# Function to generate random password
function Get-RandomPassword {
    param (
        [int]$length = 24
    )
    $bytes = New-Object byte[] $length
    $rng = [System.Security.Cryptography.RNGCryptoServiceProvider]::Create()
    $rng.GetBytes($bytes)
    return [Convert]::ToBase64String($bytes).Substring(0, $length)
}

# Function to generate hex string
function Get-RandomHex {
    param (
        [int]$bytes = 32
    )
    $byteArray = New-Object byte[] $bytes
    $rng = [System.Security.Cryptography.RNGCryptoServiceProvider]::Create()
    $rng.GetBytes($byteArray)
    return ($byteArray | ForEach-Object { $_.ToString("x2") }) -join ''
}

# Generate secure passwords
$JWT_SECRET = Get-RandomHex -bytes 32
$POSTGRES_PASSWORD = Get-RandomPassword -length 24
$REDIS_PASSWORD = Get-RandomPassword -length 24

Write-Host "✅ Generated JWT Secret (64 chars)" -ForegroundColor Green
Write-Host "✅ Generated PostgreSQL password (24 chars)" -ForegroundColor Green
Write-Host "✅ Generated Redis password (24 chars)" -ForegroundColor Green
Write-Host ""

# Get admin password
Write-Host "Please create an admin password." -ForegroundColor Cyan
Write-Host "Requirements:" -ForegroundColor Yellow
Write-Host "  • At least 12 characters"
Write-Host "  • Include uppercase letters (A-Z)"
Write-Host "  • Include lowercase letters (a-z)"
Write-Host "  • Include digits (0-9)"
Write-Host "  • Include special characters (!@#`$%^&*)"
Write-Host ""

$validPassword = $false
while (-not $validPassword) {
    $ADMIN_PASSWORD = Read-Host "Enter admin password" -AsSecureString
    $ADMIN_PASSWORD_CONFIRM = Read-Host "Confirm admin password" -AsSecureString
    
    $adminPwd = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($ADMIN_PASSWORD))
    $adminPwdConfirm = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($ADMIN_PASSWORD_CONFIRM))
    
    if ($adminPwd -ne $adminPwdConfirm) {
        Write-Host "❌ Passwords do not match. Try again." -ForegroundColor Red
        Write-Host ""
        continue
    }
    
    if ($adminPwd.Length -lt 12) {
        Write-Host "❌ Password must be at least 12 characters. Try again." -ForegroundColor Red
        Write-Host ""
        continue
    }
    
    $hasUpper = $adminPwd -cmatch '[A-Z]'
    $hasLower = $adminPwd -cmatch '[a-z]'
    $hasDigit = $adminPwd -match '\d'
    $hasSpecial = $adminPwd -match '[!@#$%^&*(),.?":{}|<>]'
    
    if (-not ($hasUpper -and $hasLower -and $hasDigit -and $hasSpecial)) {
        Write-Host "❌ Password must contain uppercase, lowercase, digit, and special character. Try again." -ForegroundColor Red
        Write-Host ""
        continue
    }
    
    $validPassword = $true
}

Write-Host "✅ Admin password validated" -ForegroundColor Green
Write-Host ""

# Get engineer password
Write-Host "Please create an engineer password." -ForegroundColor Cyan
Write-Host ""

$validPassword = $false
while (-not $validPassword) {
    $ENGINEER_PASSWORD = Read-Host "Enter engineer password" -AsSecureString
    $ENGINEER_PASSWORD_CONFIRM = Read-Host "Confirm engineer password" -AsSecureString
    
    $engPwd = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($ENGINEER_PASSWORD))
    $engPwdConfirm = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($ENGINEER_PASSWORD_CONFIRM))
    
    if ($engPwd -ne $engPwdConfirm) {
        Write-Host "❌ Passwords do not match. Try again." -ForegroundColor Red
        Write-Host ""
        continue
    }
    
    if ($engPwd.Length -lt 12) {
        Write-Host "❌ Password must be at least 12 characters. Try again." -ForegroundColor Red
        Write-Host ""
        continue
    }
    
    $hasUpper = $engPwd -cmatch '[A-Z]'
    $hasLower = $engPwd -cmatch '[a-z]'
    $hasDigit = $engPwd -match '\d'
    $hasSpecial = $engPwd -match '[!@#$%^&*(),.?":{}|<>]'
    
    if (-not ($hasUpper -and $hasLower -and $hasDigit -and $hasSpecial)) {
        Write-Host "❌ Password must contain uppercase, lowercase, digit, and special character. Try again." -ForegroundColor Red
        Write-Host ""
        continue
    }
    
    $validPassword = $true
}

Write-Host "✅ Engineer password validated" -ForegroundColor Green
Write-Host ""

# Get domain for CORS
Write-Host "Enter your domain for CORS (or press Enter for localhost):" -ForegroundColor Cyan
$DOMAIN = Read-Host "Domain (default: localhost)"
if ([string]::IsNullOrWhiteSpace($DOMAIN)) {
    $ALLOWED_ORIGINS = "http://localhost:3000,http://localhost:8000"
} else {
    $ALLOWED_ORIGINS = "https://$DOMAIN,https://app.$DOMAIN"
}

Write-Host ""
Write-Host "Creating .env file..." -ForegroundColor Cyan
Write-Host ""

# Create .env content
$envContent = @"
# FHIR Analytics Platform - Environment Configuration
# Generated on: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
# DO NOT commit this file to version control!

# ============================================
# Database Configuration
# ============================================
POSTGRES_DB=fhir_analytics
POSTGRES_USER=fhir_user
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
DATABASE_URL=postgresql://fhir_user:$POSTGRES_PASSWORD@postgres:5432/fhir_analytics

# ============================================
# Redis Configuration
# ============================================
REDIS_PASSWORD=$REDIS_PASSWORD
REDIS_URL=redis://:$REDIS_PASSWORD@redis:6379/0

# ============================================
# JWT Security
# ============================================
JWT_SECRET=$JWT_SECRET
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# ============================================
# Admin Credentials
# ============================================
ADMIN_USERNAME=admin
ADMIN_PASSWORD=$adminPwd
ADMIN_EMAIL=admin@fhir-analytics.local

# ============================================
# Engineer Credentials
# ============================================
ENGINEER_USERNAME=engineer
ENGINEER_PASSWORD=$engPwd
ENGINEER_EMAIL=engineer@fhir-analytics.local

# ============================================
# CORS Configuration
# ============================================
ALLOWED_ORIGINS=$ALLOWED_ORIGINS

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
"@

# Write to .env file
$envContent | Out-File -FilePath ".env" -Encoding UTF8 -NoNewline

Write-Host "✅ Created .env file" -ForegroundColor Green
Write-Host ""

# Save secrets to separate files
Write-Host "Saving secrets to secure files..." -ForegroundColor Cyan
$JWT_SECRET | Out-File -FilePath ".jwt_secret" -Encoding UTF8 -NoNewline
$POSTGRES_PASSWORD | Out-File -FilePath ".postgres_password" -Encoding UTF8 -NoNewline
$REDIS_PASSWORD | Out-File -FilePath ".redis_password" -Encoding UTF8 -NoNewline

Write-Host "✅ Saved secrets to secure files" -ForegroundColor Green
Write-Host ""

# Display summary
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Generated files:"
Write-Host "  • .env (main configuration)"
Write-Host "  • .jwt_secret (JWT secret backup)"
Write-Host "  • .postgres_password (database password backup)"
Write-Host "  • .redis_password (Redis password backup)"
Write-Host ""
Write-Host "⚠️  IMPORTANT SECURITY REMINDERS:" -ForegroundColor Yellow
Write-Host "  1. These files are NOT committed to git (.gitignore)"
Write-Host "  2. Store passwords in a secure password manager"
Write-Host "  3. Change admin/engineer passwords after first login"
Write-Host "  4. For production, update ALLOWED_ORIGINS in .env"
Write-Host "  5. Never share these credentials"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Review .env file: Get-Content .env"
Write-Host "  2. Start services: docker-compose up -d"
Write-Host "  3. Check logs: docker-compose logs -f"
Write-Host "  4. Access frontend: http://localhost:3000"
Write-Host ""
Write-Host "Documentation:"
Write-Host "  • Complete guide: SECURITY_SETUP_COMPLETE_GUIDE.md"
Write-Host "  • Environment setup: ENV_SETUP_GUIDE.md"
Write-Host ""
Write-Host "✨ Ready to launch!" -ForegroundColor Green

