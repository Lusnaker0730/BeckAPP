# 前端測試執行腳本 (PowerShell)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  前端測試執行" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 檢查 node_modules
if (-not (Test-Path "node_modules")) {
    Write-Host "安裝依賴..." -ForegroundColor Yellow
    npm install
}

Write-Host ""
Write-Host "執行測試..." -ForegroundColor Yellow
Write-Host ""

# 設置環境變數
$env:CI = "true"

# 執行測試
npm test -- --coverage --watchAll=false --passWithNoTests

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ 測試通過！" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "✗ 測試失敗" -ForegroundColor Red
    Write-Host ""
    Write-Host "請檢查錯誤訊息並修復" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "覆蓋率報告已生成在: coverage/" -ForegroundColor Cyan

