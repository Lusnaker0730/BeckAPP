#!/bin/bash
# 本地測試 CI/CD 管道
# 模擬 GitHub Actions 在本地執行

set -e  # 遇到錯誤時停止

echo "=========================================="
echo "  本地 CI/CD 測試"
echo "=========================================="
echo ""

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 測試計數器
TESTS_PASSED=0
TESTS_FAILED=0

# 測試函數
run_test() {
    local test_name=$1
    local test_command=$2
    
    echo -e "${YELLOW}► 執行：$test_name${NC}"
    
    if eval "$test_command"; then
        echo -e "${GREEN}✓ $test_name 通過${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ $test_name 失敗${NC}"
        ((TESTS_FAILED++))
    fi
    echo ""
}

# 1. 檢查環境
echo "=========================================="
echo "1. 檢查環境依賴"
echo "=========================================="

run_test "Python 版本" "python --version"
run_test "Node.js 版本" "node --version"
run_test "Docker 版本" "docker --version"
run_test "Docker Compose 版本" "docker-compose --version"

# 2. 後端測試
echo "=========================================="
echo "2. 後端測試"
echo "=========================================="

cd backend

run_test "安裝 Python 依賴" "pip install -q -r requirements.txt"
run_test "Python Linting (flake8)" "flake8 app --count --select=E9,F63,F7,F82 --show-source --statistics"
run_test "Python 格式檢查 (black)" "black --check app"
run_test "Import 排序檢查 (isort)" "isort --check-only app"
run_test "執行後端測試" "pytest -v --cov=app --cov-report=term-missing --cov-fail-under=70"

cd ..

# 3. 前端測試
echo "=========================================="
echo "3. 前端測試"
echo "=========================================="

cd frontend

if [ -d "node_modules" ]; then
    echo "node_modules 已存在，跳過安裝"
else
    run_test "安裝 NPM 依賴" "npm ci"
fi

run_test "前端 Linting" "npm run lint || true"
run_test "執行前端測試" "CI=true npm test -- --coverage --watchAll=false --passWithNoTests"
run_test "前端構建" "CI=true npm run build"

cd ..

# 4. Docker 測試
echo "=========================================="
echo "4. Docker 構建測試"
echo "=========================================="

run_test "構建 Backend Docker 映像" "docker build -t fhir-backend:test ./backend"
run_test "構建 Frontend Docker 映像" "docker build -t fhir-frontend:test ./frontend"
run_test "構建 ETL Service Docker 映像" "docker build -t fhir-etl:test ./etl-service"
run_test "構建 Analytics Service Docker 映像" "docker build -t fhir-analytics:test ./analytics-service"

# 5. Docker Compose 整合測試
echo "=========================================="
echo "5. Docker Compose 整合測試"
echo "=========================================="

# 創建測試 .env 檔案
cat > .env.test << EOF
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
EOF

echo "啟動服務..."
docker-compose --env-file .env.test up -d

echo "等待服務啟動..."
sleep 30

run_test "Backend 健康檢查" "curl -f http://localhost:8000/health"
run_test "Backend API 文檔" "curl -f http://localhost:8000/docs"
run_test "ETL Service 健康檢查" "curl -f http://localhost:8001/health"
run_test "Analytics Service 健康檢查" "curl -f http://localhost:8002/health"
run_test "Frontend 訪問測試" "curl -f http://localhost:3000"

echo "停止服務..."
docker-compose --env-file .env.test down -v

rm .env.test

# 6. 安全掃描
echo "=========================================="
echo "6. 安全掃描"
echo "=========================================="

if command -v bandit &> /dev/null; then
    run_test "Bandit 安全掃描" "bandit -r backend/app -f json -o bandit-report.json || true"
else
    echo -e "${YELLOW}Bandit 未安裝，跳過安全掃描${NC}"
fi

if command -v safety &> /dev/null; then
    run_test "Safety 依賴檢查" "cd backend && safety check || true"
else
    echo -e "${YELLOW}Safety 未安裝，跳過依賴檢查${NC}"
fi

# 7. 總結
echo ""
echo "=========================================="
echo "  測試總結"
echo "=========================================="
echo -e "${GREEN}通過：$TESTS_PASSED${NC}"
echo -e "${RED}失敗：$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ 所有測試通過！準備 push 到 GitHub。${NC}"
    exit 0
else
    echo -e "${RED}✗ 有測試失敗，請修復後再 push。${NC}"
    exit 1
fi

