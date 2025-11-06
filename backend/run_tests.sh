#!/bin/bash
# 測試執行腳本 - FHIR Analytics Platform
# 
# 使用方式：
#   ./run_tests.sh           # 執行所有測試
#   ./run_tests.sh unit      # 只執行單元測試
#   ./run_tests.sh integration # 只執行整合測試
#   ./run_tests.sh coverage  # 執行測試並生成覆蓋率報告

set -e  # 遇到錯誤時停止

echo "=========================================="
echo "  FHIR Analytics Platform - 測試執行"
echo "=========================================="
echo ""

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 檢查是否在 backend 目錄
if [ ! -f "pytest.ini" ]; then
    echo "錯誤：請在 backend 目錄下執行此腳本"
    exit 1
fi

# 檢查 pytest 是否已安裝
if ! command -v pytest &> /dev/null; then
    echo "錯誤：pytest 未安裝"
    echo "請執行：pip install -r requirements.txt"
    exit 1
fi

# 根據參數執行不同的測試
case "${1:-all}" in
    unit)
        echo -e "${YELLOW}執行單元測試...${NC}"
        pytest tests/unit/ -v
        ;;
    
    integration)
        echo -e "${YELLOW}執行整合測試...${NC}"
        pytest tests/integration/ -v
        ;;
    
    coverage)
        echo -e "${YELLOW}執行測試並生成覆蓋率報告...${NC}"
        pytest --cov=app --cov-report=html --cov-report=term-missing --cov-fail-under=70
        echo ""
        echo -e "${GREEN}✓ 覆蓋率報告已生成：htmlcov/index.html${NC}"
        echo ""
        echo "開啟報告："
        echo "  Windows:  start htmlcov/index.html"
        echo "  Mac:      open htmlcov/index.html"
        echo "  Linux:    xdg-open htmlcov/index.html"
        ;;
    
    fast)
        echo -e "${YELLOW}執行快速測試（排除慢速測試）...${NC}"
        pytest -m "not slow" -v
        ;;
    
    api)
        echo -e "${YELLOW}執行 API 測試...${NC}"
        pytest -m api -v
        ;;
    
    security)
        echo -e "${YELLOW}執行安全相關測試...${NC}"
        pytest -m security -v
        ;;
    
    parallel)
        echo -e "${YELLOW}並行執行測試...${NC}"
        if ! command -v pytest-xdist &> /dev/null; then
            echo "安裝 pytest-xdist..."
            pip install pytest-xdist
        fi
        pytest -n auto -v
        ;;
    
    failed)
        echo -e "${YELLOW}重新執行失敗的測試...${NC}"
        pytest --lf -v
        ;;
    
    new)
        echo -e "${YELLOW}執行新增的測試...${NC}"
        pytest tests/integration/test_survival_api.py \
               tests/integration/test_export_api.py \
               tests/integration/test_cohort_api.py \
               tests/unit/test_audit_middleware.py \
               tests/unit/test_cache.py \
               -v
        ;;
    
    all|*)
        echo -e "${YELLOW}執行所有測試...${NC}"
        pytest -v
        echo ""
        echo -e "${GREEN}✓ 所有測試完成${NC}"
        echo ""
        echo "執行覆蓋率報告："
        echo "  ./run_tests.sh coverage"
        ;;
esac

echo ""
echo "=========================================="
echo "  測試執行完成"
echo "=========================================="

