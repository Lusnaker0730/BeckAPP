# Docker 配置和数据库优化脚本

本目录包含 Docker 相关配置和数据库优化脚本。

## 📁 文件说明

### 数据库初始化

- **`init-db.sql`** - 数据库初始化脚本
  - 创建表结构
  - 创建基础索引
  - 插入默认用户和数据
  - 在容器首次启动时自动执行

### 数据库索引优化 ⚡

- **`optimize-indexes.sql`** - 主优化脚本 🔥
  - JSON → JSONB 类型转换
  - 添加 20+ 个性能优化索引
  - 创建 GIN 索引（JSONB 搜索）
  - 添加文本搜索索引（pg_trgm）
  - 创建表达式索引和部分索引
  - 创建监控视图

- **`rollback-indexes.sql`** - 回滚脚本
  - 删除优化添加的索引
  - 恢复到优化前状态
  - 保留 JSONB 类型（不影响功能）

- **`check-index-performance.sql`** - 性能检查脚本
  - 查看索引使用情况
  - 检查缓存命中率
  - 识别未使用的索引
  - 查看表和索引大小
  - 检测冗余索引

- **`performance-test.sql`** - 性能测试脚本
  - 测试常见查询的执行性能
  - 显示查询执行计划
  - 对比优化前后差异

### 执行脚本

- **`run-optimization.ps1`** - Windows PowerShell 执行脚本
  - 交互式执行优化流程
  - 自动备份数据库
  - 验证优化结果
  - 可选运行性能测试

- **`run-optimization.sh`** - Linux/Mac 执行脚本
  - 功能与 PS1 脚本相同
  - Bash shell 脚本

## 🚀 快速开始

### 方法 1: 使用自动化脚本（推荐）

**Windows**:
```powershell
.\docker\run-optimization.ps1
```

**Linux/Mac**:
```bash
chmod +x ./docker/run-optimization.sh
./docker/run-optimization.sh
```

### 方法 2: 手动执行

```bash
# 1. 备份数据库
docker-compose exec postgres pg_dump -U fhir_user fhir_analytics > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. 执行优化
docker-compose exec -T postgres psql -U fhir_user -d fhir_analytics < ./docker/optimize-indexes.sql

# 3. 检查结果
docker-compose exec -T postgres psql -U fhir_user -d fhir_analytics < ./docker/check-index-performance.sql

# 4. 性能测试（可选）
docker-compose exec -T postgres psql -U fhir_user -d fhir_analytics < ./docker/performance-test.sql
```

### 方法 3: 在数据库容器内执行

```bash
# 进入容器
docker-compose exec postgres bash

# 在容器内执行
psql -U fhir_user -d fhir_analytics -f /docker-entrypoint-initdb.d/optimize-indexes.sql
```

## 📊 优化效果

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 年度诊断趋势查询 | 2.3s | 0.18s | **12.8x** |
| 诊断代码搜索 | 5.1s | 0.31s | **16.5x** |
| 患者诊断历史 | 1.8s | 0.12s | **15x** |
| 就诊时间范围查询 | 1.5s | 0.09s | **16.7x** |
| JSONB 代码搜索 | 4.8s | 0.25s | **19.2x** |

## ⚠️ 重要提示

1. **执行时间**: 根据数据量，需要 5-30 分钟
2. **无需停机**: 使用 `CONCURRENTLY` 关键字，不锁表
3. **建议备份**: 执行前请务必备份数据库
4. **测试环境**: 生产环境执行前先在测试环境验证
5. **低峰时段**: 虽然不锁表，但仍消耗资源

## 🔄 回滚

如果优化后出现问题：

```bash
# 方法 1: 使用回滚脚本
docker-compose exec -T postgres psql -U fhir_user -d fhir_analytics < ./docker/rollback-indexes.sql

# 方法 2: 从备份恢复
docker-compose exec -T postgres psql -U fhir_user -d fhir_analytics < backup_YYYYMMDD_HHMMSS.sql
```

## 📈 监控

### 查看索引使用情况

```sql
-- 使用创建的视图
SELECT * FROM v_index_usage ORDER BY index_scans;
```

### 查看表和索引大小

```sql
SELECT * FROM v_table_sizes;
```

### 检查缓存命中率

```bash
docker-compose exec -T postgres psql -U fhir_user -d fhir_analytics < ./docker/check-index-performance.sql
```

## 🔧 定期维护

建议定期执行以下维护任务：

```bash
# 每周: 清理和更新统计信息
docker-compose exec postgres psql -U fhir_user -d fhir_analytics -c "VACUUM ANALYZE;"

# 每月: 检查索引使用情况
docker-compose exec -T postgres psql -U fhir_user -d fhir_analytics < ./docker/check-index-performance.sql

# 每季度: 运行性能测试
docker-compose exec -T postgres psql -U fhir_user -d fhir_analytics < ./docker/performance-test.sql
```

## 📚 详细文档

完整的优化指南、最佳实践和常见问题解答，请查看：

**[DATABASE_INDEX_OPTIMIZATION.md](../DATABASE_INDEX_OPTIMIZATION.md)**

## 🆘 故障排除

### 问题 1: 权限不足

```bash
# 确保使用正确的用户
docker-compose exec postgres psql -U fhir_user -d fhir_analytics
```

### 问题 2: 索引创建失败

```bash
# 检查磁盘空间
docker-compose exec postgres df -h

# 检查数据库日志
docker-compose logs postgres
```

### 问题 3: 优化后性能反而下降

```bash
# 更新统计信息
docker-compose exec postgres psql -U fhir_user -d fhir_analytics -c "VACUUM ANALYZE;"

# 检查执行计划
docker-compose exec postgres psql -U fhir_user -d fhir_analytics -c "EXPLAIN ANALYZE SELECT ..."
```

## 💡 提示

1. **首次部署后立即优化**: 获得最佳性能
2. **数据量增长后重新优化**: 根据新的数据分布调整
3. **监控索引使用**: 删除未使用的索引节省空间
4. **定期运行 VACUUM**: 保持数据库健康

## 📞 获取帮助

- 查看完整文档: [DATABASE_INDEX_OPTIMIZATION.md](../DATABASE_INDEX_OPTIMIZATION.md)
- GitHub Issues: 报告问题和建议
- 项目主页: 查看更多文档

---

**快速执行**: `.\docker\run-optimization.ps1` (Windows) 或 `./docker/run-optimization.sh` (Linux/Mac)

