#!/bin/bash
# ============================================================================
# FHIR Analytics Platform - 数据库索引优化执行脚本 (Linux/Mac)
# ============================================================================

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  🚀 FHIR Analytics Platform - 数据库索引优化                   ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check Docker Compose
echo -e "${YELLOW}📋 步骤 1/5: 检查 Docker 服务状态...${NC}"
if ! docker-compose ps postgres &> /dev/null; then
    echo -e "${RED}❌ 错误: Docker Compose 未运行${NC}"
    echo -e "${YELLOW}请先运行: docker-compose up -d${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker 服务正常运行${NC}"
echo ""

# Backup
echo -e "${YELLOW}📋 步骤 2/5: 数据库备份${NC}"
read -p "是否备份数据库？(强烈推荐) [Y/n] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_dir="./backups"
    
    mkdir -p "$backup_dir"
    
    echo -e "${CYAN}正在备份数据库...${NC}"
    docker-compose exec -T postgres pg_dump -U fhir_user fhir_analytics > "$backup_dir/fhir_analytics_backup_$timestamp.sql"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 备份成功: $backup_dir/fhir_analytics_backup_$timestamp.sql${NC}"
    else
        echo -e "${RED}❌ 备份失败${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  跳过备份 (不推荐)${NC}"
fi
echo ""

# Preview
echo -e "${YELLOW}📋 步骤 3/5: 优化内容预览${NC}"
echo "将执行以下优化:"
echo "  • JSON → JSONB 数据类型转换"
echo "  • 添加 20+ 个性能优化索引"
echo "  • 创建 GIN 索引支持 JSONB 搜索"
echo "  • 添加文本搜索索引（pg_trgm）"
echo "  • 创建监控视图"
echo ""
echo -e "${CYAN}预计执行时间: 5-30 分钟（视数据量而定）${NC}"
echo -e "${CYAN}执行期间应用可正常运行（使用 CONCURRENTLY）${NC}"
echo ""

# Confirm
read -p "是否继续执行优化？[Y/n] " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo -e "${YELLOW}❌ 用户取消操作${NC}"
    exit 0
fi

# Execute optimization
echo ""
echo -e "${YELLOW}📋 步骤 4/5: 执行优化脚本${NC}"
echo -e "${CYAN}正在优化数据库，请稍候...${NC}"
echo ""

cat ./docker/optimize-indexes.sql | docker-compose exec -T postgres psql -U fhir_user -d fhir_analytics

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ 优化脚本执行成功！${NC}"
else
    echo ""
    echo -e "${RED}❌ 优化失败，请检查错误日志${NC}"
    echo -e "${YELLOW}可以使用回滚脚本恢复: ./docker/rollback-indexes.sql${NC}"
    exit 1
fi

# Verify
echo ""
echo -e "${YELLOW}📋 步骤 5/5: 验证优化结果${NC}"
echo -e "${CYAN}正在运行性能检查...${NC}"
echo ""

cat ./docker/check-index-performance.sql | docker-compose exec -T postgres psql -U fhir_user -d fhir_analytics

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ 数据库索引优化完成！                                       ║${NC}"
echo -e "${GREEN}╠════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  📊 后续操作:                                                  ║${NC}"
echo -e "${GREEN}║                                                                ║${NC}"
echo "║  1. 测试应用功能是否正常                                       ║"
echo "║  2. 运行性能测试: ./docker/performance-test.sql                ║"
echo "║  3. 监控索引使用情况                                           ║"
echo "║  4. 如有问题，使用回滚脚本: ./docker/rollback-indexes.sql      ║"
echo -e "${GREEN}║                                                                ║${NC}"
echo -e "${CYAN}║  📖 详细文档: DATABASE_INDEX_OPTIMIZATION.md                   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Run performance test
read -p "是否运行性能测试？[Y/n] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo ""
    echo -e "${CYAN}🚀 运行性能测试...${NC}"
    cat ./docker/performance-test.sql | docker-compose exec -T postgres psql -U fhir_user -d fhir_analytics
fi

echo ""
echo -e "${GREEN}🎉 全部完成！${NC}"

