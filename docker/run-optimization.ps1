# ============================================================================
# FHIR Analytics Platform - 数据库索引优化执行脚本 (Windows PowerShell)
# ============================================================================

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🚀 FHIR Analytics Platform - 数据库索引优化                   ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# 检查 Docker Compose 是否运行
Write-Host "📋 步骤 1/5: 检查 Docker 服务状态..." -ForegroundColor Yellow
$dockerStatus = docker-compose ps postgres 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 错误: Docker Compose 未运行" -ForegroundColor Red
    Write-Host "请先运行: docker-compose up -d" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ Docker 服务正常运行" -ForegroundColor Green
Write-Host ""

# 询问是否备份
Write-Host "📋 步骤 2/5: 数据库备份" -ForegroundColor Yellow
$backup = Read-Host "是否备份数据库？(强烈推荐) [Y/n]"
if ($backup -ne "n" -and $backup -ne "N") {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupDir = "./backups"
    
    if (!(Test-Path $backupDir)) {
        New-Item -ItemType Directory -Path $backupDir | Out-Null
    }
    
    Write-Host "正在备份数据库..." -ForegroundColor Cyan
    docker-compose exec -T postgres pg_dump -U fhir_admin fhir_analytics > "$backupDir/fhir_analytics_backup_$timestamp.sql"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 备份成功: $backupDir/fhir_analytics_backup_$timestamp.sql" -ForegroundColor Green
    } else {
        Write-Host "❌ 备份失败" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "⚠️  跳过备份 (不推荐)" -ForegroundColor Yellow
}
Write-Host ""

# 显示优化内容
Write-Host "📋 步骤 3/5: 优化内容预览" -ForegroundColor Yellow
Write-Host "将执行以下优化:" -ForegroundColor White
Write-Host "  • JSON → JSONB 数据类型转换" -ForegroundColor Gray
Write-Host "  • 添加 20+ 个性能优化索引" -ForegroundColor Gray
Write-Host "  • 创建 GIN 索引支持 JSONB 搜索" -ForegroundColor Gray
Write-Host "  • 添加文本搜索索引（pg_trgm）" -ForegroundColor Gray
Write-Host "  • 创建监控视图" -ForegroundColor Gray
Write-Host ""
Write-Host "预计执行时间: 5-30 分钟（视数据量而定）" -ForegroundColor Cyan
Write-Host "执行期间应用可正常运行（使用 CONCURRENTLY）" -ForegroundColor Cyan
Write-Host ""

# 确认执行
$confirm = Read-Host "是否继续执行优化？[Y/n]"
if ($confirm -eq "n" -or $confirm -eq "N") {
    Write-Host "❌ 用户取消操作" -ForegroundColor Yellow
    exit 0
}

# 执行优化
Write-Host ""
Write-Host "📋 步骤 4/5: 执行优化脚本" -ForegroundColor Yellow
Write-Host "正在优化数据库，请稍候..." -ForegroundColor Cyan
Write-Host ""

Get-Content ./docker/optimize-indexes.sql | docker-compose exec -T postgres psql -U fhir_admin -d fhir_analytics

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ 优化脚本执行成功！" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ 优化失败，请检查错误日志" -ForegroundColor Red
    Write-Host "可以使用回滚脚本恢复: ./docker/rollback-indexes.sql" -ForegroundColor Yellow
    exit 1
}

# 验证结果
Write-Host ""
Write-Host "📋 步骤 5/5: 验证优化结果" -ForegroundColor Yellow
Write-Host "正在运行性能检查..." -ForegroundColor Cyan
Write-Host ""

Get-Content ./docker/check-index-performance.sql | docker-compose exec -T postgres psql -U fhir_admin -d fhir_analytics

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ✅ 数据库索引优化完成！                                       ║" -ForegroundColor Green
Write-Host "╠════════════════════════════════════════════════════════════════╣" -ForegroundColor Green
Write-Host "║  📊 后续操作:                                                  ║" -ForegroundColor Green
Write-Host "║                                                                ║" -ForegroundColor Green
Write-Host "║  1. 测试应用功能是否正常                                       ║" -ForegroundColor White
Write-Host "║  2. 运行性能测试: ./docker/performance-test.sql                ║" -ForegroundColor White
Write-Host "║  3. 监控索引使用情况                                           ║" -ForegroundColor White
Write-Host "║  4. 如有问题，使用回滚脚本: ./docker/rollback-indexes.sql      ║" -ForegroundColor White
Write-Host "║                                                                ║" -ForegroundColor Green
Write-Host "║  📖 详细文档: DATABASE_INDEX_OPTIMIZATION.md                   ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

# 询问是否运行性能测试
$runTest = Read-Host "是否运行性能测试？[Y/n]"
if ($runTest -ne "n" -and $runTest -ne "N") {
    Write-Host ""
    Write-Host "🚀 运行性能测试..." -ForegroundColor Cyan
    Get-Content ./docker/performance-test.sql | docker-compose exec -T postgres psql -U fhir_admin -d fhir_analytics
}

Write-Host ""
Write-Host "🎉 全部完成！" -ForegroundColor Green

