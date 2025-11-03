# ============================================================================
# FHIR Analytics Platform - 存活分析功能安装脚本 (Windows PowerShell)
# ============================================================================

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🔬 FHIR Analytics Platform - 存活分析功能安装                 ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# 步骤 1: 检查 Docker 服务
Write-Host "📋 步骤 1/3: 检查 Docker 服务状态..." -ForegroundColor Yellow
$dockerStatus = docker-compose ps 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 错误: Docker Compose 未运行" -ForegroundColor Red
    Write-Host "请先运行: docker-compose up -d" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ Docker 服务正常运行" -ForegroundColor Green
Write-Host ""

# 步骤 2: 安装 Python 依赖
Write-Host "📋 步骤 2/3: 安装 Python 依赖库..." -ForegroundColor Yellow
Write-Host "正在安装 lifelines, matplotlib, scipy..." -ForegroundColor Cyan

docker-compose exec backend pip install lifelines==0.27.8 matplotlib==3.8.2 scipy==1.11.4

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Python 依赖安装成功" -ForegroundColor Green
} else {
    Write-Host "❌ Python 依赖安装失败" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 步骤 3: 创建数据库表
Write-Host "📋 步骤 3/3: 创建数据库表..." -ForegroundColor Yellow
Write-Host "正在创建 survival_cohorts 和 survival_events 表..." -ForegroundColor Cyan

docker cp ./docker/add-survival-tables.sql fhir-postgres:/tmp/add-survival-tables.sql
docker-compose exec postgres psql -U fhir_admin -d fhir_analytics -f /tmp/add-survival-tables.sql

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 数据库表创建成功" -ForegroundColor Green
} else {
    Write-Host "❌ 数据库表创建失败" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 步骤 4: 重启服务
Write-Host "📋 重启服务以应用更改..." -ForegroundColor Yellow
docker-compose restart backend

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 服务重启成功" -ForegroundColor Green
} else {
    Write-Host "❌ 服务重启失败" -ForegroundColor Red
}
Write-Host ""

# 完成
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ✅ 存活分析功能安装完成！                                     ║" -ForegroundColor Green
Write-Host "╠════════════════════════════════════════════════════════════════╣" -ForegroundColor Green
Write-Host "║  🎯 下一步:                                                    ║" -ForegroundColor White
Write-Host "║                                                                ║" -ForegroundColor Green
Write-Host "║  1. 打开浏览器访问: http://localhost:3000                      ║" -ForegroundColor White
Write-Host "║  2. 登录系统                                                   ║" -ForegroundColor White
Write-Host "║  3. 点击导航栏的 [存活分析 🔬]                                 ║" -ForegroundColor White
Write-Host "║  4. 开始使用 Kaplan-Meier 和 Cox 回归分析！                   ║" -ForegroundColor White
Write-Host "║                                                                ║" -ForegroundColor Green
Write-Host "║  📖 详细文档: SURVIVAL_ANALYSIS_FEATURE.md                     ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Host "🎉 安装成功！" -ForegroundColor Green

