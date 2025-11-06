# 本地測試 CI/CD 管道 (PowerShell)
# 模擬 GitHub Actions 在本地執行

$ErrorActionPreference = "Continue"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  本地 CI/CD 測試" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 測試計數器
$TestsPassed = 0
$TestsFailed = 0

# 測試函數
function Run-Test {
    param(
        [string]$TestName,
        [scriptblock]$TestCommand
    )
    
    Write-Host "► 執行：$TestName" -ForegroundColor Yellow
    
    try {
        & $TestCommand
        if ($LASTEXITCODE -eq 0 -or $? -eq $true) {
            Write-Host "✓ $TestName 通過" -ForegroundColor Green
            $script:TestsPassed++
        } else {
            Write-Host "✗ $TestName 失敗" -ForegroundColor Red
            $script:TestsFailed++
        }
    } catch {
        Write-Host "✗ $TestName 失敗: $_" -ForegroundColor Red
        $script:TestsFailed++
    }
    
    Write-Host ""
}

# 1. 檢查環境
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "1. 檢查環境依賴" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

Run-Test "Python 版本" { python --version }
Run-Test "Node.js 版本" { node --version }
Run-Test "Docker 版本" { docker --version }
Run-Test "Docker Compose 版本" { docker-compose --version }

# 2. 後端測試
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "2. 後端測試" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

Push-Location backend

Run-Test "安裝 Python 依賴" { pip install -q -r requirements.txt }
Run-Test "Python Linting (flake8)" { flake8 app --count --select=E9,F63,F7,F82 --show-source --statistics }
Run-Test "Python 格式檢查 (black)" { black --check app }
Run-Test "Import 排序檢查 (isort)" { isort --check-only app }
Run-Test "執行後端測試" { pytest -v --cov=app --cov-report=term-missing --cov-fail-under=70 }

Pop-Location

# 3. 前端測試
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "3. 前端測試" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

Push-Location frontend

if (Test-Path "node_modules") {
    Write-Host "node_modules 已存在，跳過安裝"
} else {
    Run-Test "安裝 NPM 依賴" { npm ci }
}

Run-Test "前端 Linting" { npm run lint }
Run-Test "執行前端測試" { 
    $env:CI = "true"
    npm test -- --coverage --watchAll=false --passWithNoTests 
}
Run-Test "前端構建" { 
    $env:CI = "true"
    npm run build 
}

Pop-Location

# 4. Docker 測試
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "4. Docker 構建測試" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

Run-Test "構建 Backend Docker 映像" { docker build -t fhir-backend:test ./backend }
Run-Test "構建 Frontend Docker 映像" { docker build -t fhir-frontend:test ./frontend }
Run-Test "構建 ETL Service Docker 映像" { docker build -t fhir-etl:test ./etl-service }
Run-Test "構建 Analytics Service Docker 映像" { docker build -t fhir-analytics:test ./analytics-service }

# 5. Docker Compose 整合測試
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "5. Docker Compose 整合測試" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 創建測試 .env 檔案
@"
POSTGRES_DB=fhir_analytics
POSTGRES_USER=test_user
POSTGRES_PASSWORD=test_password
DATABASE_URL=postgresql://test_user:test_password@postgres:5432/fhir_analytics
JWT_SECRET=test-jwt-secret-key-for-testing-32chars
JWT_ALGORITHM=HS256
REDIS_PASSWORD=test_redis_password
REDIS_URL=redis://:test_redis_password@redis:6379/0
ADMIN_PASSWORD=admin123
ENGINEER_PASSWORD=engineer123
ALLOWED_ORIGINS=http://localhost:3000
ENVIRONMENT=testing
"@ | Out-File -FilePath .env.test -Encoding UTF8

Write-Host "啟動服務..."
docker-compose --env-file .env.test up -d

Write-Host "等待服務啟動..."
Start-Sleep -Seconds 30

Run-Test "Backend 健康檢查" { 
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
    if ($response.StatusCode -ne 200) { throw "Health check failed" }
}

Run-Test "Backend API 文檔" { 
    $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing
    if ($response.StatusCode -ne 200) { throw "API docs check failed" }
}

Run-Test "ETL Service 健康檢查" { 
    $response = Invoke-WebRequest -Uri "http://localhost:8001/health" -UseBasicParsing
    if ($response.StatusCode -ne 200) { throw "ETL health check failed" }
}

Run-Test "Analytics Service 健康檢查" { 
    $response = Invoke-WebRequest -Uri "http://localhost:8002/health" -UseBasicParsing
    if ($response.StatusCode -ne 200) { throw "Analytics health check failed" }
}

Run-Test "Frontend 訪問測試" { 
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing
    if ($response.StatusCode -ne 200) { throw "Frontend check failed" }
}

Write-Host "停止服務..."
docker-compose --env-file .env.test down -v

Remove-Item .env.test -ErrorAction SilentlyContinue

# 6. 安全掃描
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "6. 安全掃描" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

if (Get-Command bandit -ErrorAction SilentlyContinue) {
    Run-Test "Bandit 安全掃描" { bandit -r backend/app -f json -o bandit-report.json }
} else {
    Write-Host "Bandit 未安裝，跳過安全掃描" -ForegroundColor Yellow
}

if (Get-Command safety -ErrorAction SilentlyContinue) {
    Run-Test "Safety 依賴檢查" { 
        Push-Location backend
        safety check
        Pop-Location
    }
} else {
    Write-Host "Safety 未安裝，跳過依賴檢查" -ForegroundColor Yellow
}

# 7. 總結
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  測試總結" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "通過：$TestsPassed" -ForegroundColor Green
Write-Host "失敗：$TestsFailed" -ForegroundColor Red
Write-Host ""

if ($TestsFailed -eq 0) {
    Write-Host "✓ 所有測試通過！準備 push 到 GitHub。" -ForegroundColor Green
    exit 0
} else {
    Write-Host "✗ 有測試失敗，請修復後再 push。" -ForegroundColor Red
    exit 1
}

