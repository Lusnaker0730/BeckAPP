# =========================================================
# 審計日誌系統安裝腳本 (PowerShell - Windows)
# =========================================================
# 
# 此腳本將：
# 1. 在 PostgreSQL 數據庫中創建 audit_logs 表
# 2. 重啟後端服務以應用新的審計日誌功能
#
# 使用方法：
#   .\setup-audit-logs.ps1
# =========================================================

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "    審計日誌系統安裝腳本" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# 檢查 Docker Compose 是否可用
Write-Host "[1/3] 檢查 Docker Compose..." -ForegroundColor Yellow
if (!(Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Error: docker-compose not found!" -ForegroundColor Red
    Write-Host "   Please install Docker Compose first." -ForegroundColor Red
    exit 1
}
Write-Host "✅ Docker Compose 已安裝" -ForegroundColor Green
Write-Host ""

# 創建審計日誌表
Write-Host "[2/3] 創建審計日誌表..." -ForegroundColor Yellow

# 檢查 SQL 文件是否存在
if (!(Test-Path "docker\add-audit-logs-table.sql")) {
    Write-Host "❌ Error: SQL file not found at docker\add-audit-logs-table.sql" -ForegroundColor Red
    exit 1
}

# 將 SQL 文件複製到容器內
Write-Host "   - 複製 SQL 文件到容器..." -ForegroundColor Cyan
docker cp docker\add-audit-logs-table.sql fhir-postgres:/tmp/add-audit-logs-table.sql

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 複製文件失敗！" -ForegroundColor Red
    exit 1
}

# 執行 SQL 腳本
Write-Host "   - 執行 SQL 腳本..." -ForegroundColor Cyan
docker-compose exec -T postgres psql -U fhir_admin -d fhir_analytics -f /tmp/add-audit-logs-table.sql

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ SQL 執行失敗！" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 審計日誌表創建成功！" -ForegroundColor Green
Write-Host ""

# 重啟後端服務
Write-Host "[3/3] 重啟後端服務..." -ForegroundColor Yellow
docker-compose restart backend

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 重啟後端服務失敗！" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 後端服務已重啟" -ForegroundColor Green
Write-Host ""

# 等待服務啟動
Write-Host "⏳ 等待服務啟動..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
Write-Host ""

# 完成
Write-Host "================================================" -ForegroundColor Green
Write-Host "    ✅ 審計日誌系統安裝完成！" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "📋 功能說明：" -ForegroundColor Cyan
Write-Host "   - 自動記錄所有 API 請求" -ForegroundColor White
Write-Host "   - 記錄用戶操作（登錄、查詢、導出等）" -ForegroundColor White
Write-Host "   - 安全審計和合規性追蹤" -ForegroundColor White
Write-Host ""
Write-Host "🔐 使用方法：" -ForegroundColor Cyan
Write-Host "   1. 以管理員身份登錄系統" -ForegroundColor White
Write-Host "   2. 導航欄中點擊「審計日誌」" -ForegroundColor White
Write-Host "   3. 查看系統操作記錄" -ForegroundColor White
Write-Host ""
Write-Host "📚 文檔：請查看 AUDIT_LOG_SYSTEM.md" -ForegroundColor Cyan
Write-Host ""
Write-Host "🎉 審計日誌系統已就緒！" -ForegroundColor Green
Write-Host ""

