# 測試執行腳本 - FHIR Analytics Platform (PowerShell)
#
# 使用方式：
#   .\run_tests.ps1           # 執行所有測試
#   .\run_tests.ps1 unit      # 只執行單元測試
#   .\run_tests.ps1 integration # 只執行整合測試
#   .\run_tests.ps1 coverage  # 執行測試並生成覆蓋率報告

param(
    [string]$TestType = "all"
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  FHIR Analytics Platform - 測試執行" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 檢查是否在 backend 目錄
if (-not (Test-Path "pytest.ini")) {
    Write-Host "錯誤：請在 backend 目錄下執行此腳本" -ForegroundColor Red
    exit 1
}

# 檢查 pytest 是否已安裝
try {
    $null = Get-Command pytest -ErrorAction Stop
} catch {
    Write-Host "錯誤：pytest 未安裝" -ForegroundColor Red
    Write-Host "請執行：pip install -r requirements.txt"
    exit 1
}

# 根據參數執行不同的測試
switch ($TestType) {
    "unit" {
        Write-Host "執行單元測試..." -ForegroundColor Yellow
        pytest tests/unit/ -v
    }
    
    "integration" {
        Write-Host "執行整合測試..." -ForegroundColor Yellow
        pytest tests/integration/ -v
    }
    
    "coverage" {
        Write-Host "執行測試並生成覆蓋率報告..." -ForegroundColor Yellow
        pytest --cov=app --cov-report=html --cov-report=term-missing --cov-fail-under=70
        Write-Host ""
        Write-Host "✓ 覆蓋率報告已生成：htmlcov\index.html" -ForegroundColor Green
        Write-Host ""
        Write-Host "開啟報告："
        Write-Host "  start htmlcov\index.html"
    }
    
    "fast" {
        Write-Host "執行快速測試（排除慢速測試）..." -ForegroundColor Yellow
        pytest -m "not slow" -v
    }
    
    "api" {
        Write-Host "執行 API 測試..." -ForegroundColor Yellow
        pytest -m api -v
    }
    
    "security" {
        Write-Host "執行安全相關測試..." -ForegroundColor Yellow
        pytest -m security -v
    }
    
    "parallel" {
        Write-Host "並行執行測試..." -ForegroundColor Yellow
        try {
            $null = Get-Command pytest-xdist -ErrorAction Stop
        } catch {
            Write-Host "安裝 pytest-xdist..."
            pip install pytest-xdist
        }
        pytest -n auto -v
    }
    
    "failed" {
        Write-Host "重新執行失敗的測試..." -ForegroundColor Yellow
        pytest --lf -v
    }
    
    "new" {
        Write-Host "執行新增的測試..." -ForegroundColor Yellow
        pytest tests/integration/test_survival_api.py `
               tests/integration/test_export_api.py `
               tests/integration/test_cohort_api.py `
               tests/unit/test_audit_middleware.py `
               tests/unit/test_cache.py `
               -v
    }
    
    default {
        Write-Host "執行所有測試..." -ForegroundColor Yellow
        pytest -v
        Write-Host ""
        Write-Host "✓ 所有測試完成" -ForegroundColor Green
        Write-Host ""
        Write-Host "執行覆蓋率報告："
        Write-Host "  .\run_tests.ps1 coverage"
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  測試執行完成" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

