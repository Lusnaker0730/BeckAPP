# 🚀 Redis 缓存使用指南

本指南说明如何使用和管理 FHIR Analytics Platform 中的 Redis 缓存功能。

---

## 📋 目录

- [什么是 Redis 缓存](#什么是-redis-缓存)
- [快速开始](#快速开始)
- [缓存策略](#缓存策略)
- [管理缓存](#管理缓存)
- [监控和统计](#监控和统计)
- [故障排除](#故障排除)
- [最佳实践](#最佳实践)

---

## 🎯 什么是 Redis 缓存

Redis 是一个高速内存数据库，用于缓存频繁访问的数据，可以将 API 响应速度提升 **10-100 倍**。

### 性能对比

| 场景 | 无缓存 | 有缓存 | 提升 |
|------|-------|-------|------|
| 诊断分析查询 | 3.2秒 | 0.05秒 | **64倍** |
| 热门诊断列表 | 2.5秒 | 0.03秒 | **83倍** |
| 患者统计 | 1.8秒 | 0.02秒 | **90倍** |

---

## 🚀 快速开始

### 1. 启动 Redis 服务

使用 Docker Compose：

```bash
# 启动所有服务（包括 Redis）
docker-compose up -d

# 或只启动 Redis
docker-compose up -d redis
```

验证 Redis 正在运行：

```bash
# 检查 Redis 容器状态
docker ps | grep fhir-redis

# 测试 Redis 连接
docker exec -it fhir-redis redis-cli ping
# 应该返回: PONG
```

### 2. 检查缓存健康状态

访问健康检查端点：

```bash
curl http://localhost:8000/api/cache/health
```

**成功响应：**
```json
{
  "status": "healthy",
  "message": "Redis cache is operational",
  "total_keys": 42
}
```

### 3. 查看缓存统计

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/cache/stats
```

**响应示例：**
```json
{
  "status": "success",
  "data": {
    "status": "connected",
    "total_keys": 156,
    "memory_used_mb": 12.45,
    "memory_peak_mb": 15.23,
    "hits": 8943,
    "misses": 1230,
    "hit_rate": 87.91,
    "total_commands": 10500
  }
}
```

---

## 📊 缓存策略

### 已缓存的 API 端点

| API 端点 | 缓存时间 | 说明 |
|----------|---------|------|
| `/api/analytics/diagnosis` | 30分钟 | 诊断分析数据 |
| `/api/analytics/top-conditions` | 10分钟 | 热门诊断列表 |
| `/api/analytics/available-diagnoses` | 10分钟 | 可用诊断列表 |
| `/api/analytics/patient-demographics` | 15分钟 | 患者统计信息 |

### 缓存时间说明

- **10分钟**：经常变动但可以容忍短暂延迟的数据
- **15-30分钟**：统计数据，变化较慢
- **1小时+**：配置信息，极少变化

### 缓存键命名规则

缓存键格式：`{prefix}:{function_name}:{parameters}`

示例：
```
diagnosis_analysis:get_diagnosis_analysis:diabetes:yearly:2020:2024
top_conditions:get_top_conditions:10
available_diagnoses:get_available_diagnoses:100
```

---

## 🛠️ 管理缓存

### 1. 查看缓存统计

**API 请求：**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/cache/stats
```

**关键指标：**
- `hit_rate`: 缓存命中率 (越高越好，目标 >80%)
- `total_keys`: 当前缓存的键数量
- `memory_used_mb`: Redis 内存使用量

### 2. 清除特定模式的缓存

**清除诊断相关缓存：**
```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/cache/invalidate/diagnosis
```

**清除分析相关缓存：**
```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/cache/invalidate/analytics
```

**自定义模式清除：**
```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  "http://localhost:8000/api/cache/invalidate?pattern=diagnosis:*"
```

### 3. ETL 任务完成后清除缓存

当新数据导入后，应该清除相关缓存：

```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/cache/invalidate/after-etl
```

**自动化（推荐）：**

在 ETL 完成时自动调用：

```python
# etl-service/app/api/bulk_data.py
async def on_etl_complete(job_id: str):
    # ETL 完成逻辑...
    
    # 清除缓存
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://backend:8000/api/cache/invalidate/after-etl",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
```

### 4. 清除所有缓存（慎用！）

**仅管理员可用：**
```bash
curl -X POST \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/api/cache/clear-all
```

⚠️ **警告**：这会清除所有缓存，导致后续请求变慢，直到缓存重新建立。

---

## 📈 监控和统计

### 缓存性能监控

#### 1. 实时监控 Redis

```bash
# 进入 Redis 容器
docker exec -it fhir-redis redis-cli

# 实时监控命令
> MONITOR

# 查看信息
> INFO stats
> INFO memory

# 查看所有键
> KEYS *

# 查看特定键的值
> GET "diagnosis_analysis:get_diagnosis_analysis:diabetes"

# 查看键的过期时间（秒）
> TTL "diagnosis_analysis:get_diagnosis_analysis:diabetes"
```

#### 2. 通过 API 监控

创建监控脚本：

```bash
#!/bin/bash
# cache_monitor.sh

while true; do
  clear
  echo "=== Redis Cache Statistics ==="
  echo ""
  
  curl -s -H "Authorization: Bearer $TOKEN" \
    http://localhost:8000/api/cache/stats | jq '.'
  
  echo ""
  echo "Refreshing in 10 seconds..."
  sleep 10
done
```

运行：
```bash
chmod +x cache_monitor.sh
export TOKEN="your_jwt_token"
./cache_monitor.sh
```

#### 3. 日志监控

查看缓存命中/未命中日志：

```bash
# 查看后端日志
docker logs -f fhir-backend | grep -i "cache"

# 输出示例：
# ✅ Cache HIT: diagnosis_analysis:get_diagnosis_analysis:diabetes
# ❌ Cache MISS: top_conditions:get_top_conditions:10
# 💾 Cached result for diagnosis_analysis... (expires in 1800s)
```

---

## 🔍 故障排除

### 问题 1：Redis 连接失败

**症状：**
```
⚠️  Redis not available: connection refused
```

**解决方案：**

1. 检查 Redis 是否运行：
```bash
docker ps | grep redis
```

2. 检查端口是否开放：
```bash
telnet localhost 6379
```

3. 重启 Redis：
```bash
docker-compose restart redis
```

4. 检查日志：
```bash
docker logs fhir-redis
```

### 问题 2：缓存未生效

**症状：**
- API 响应时间没有改善
- 日志中只看到 "Cache MISS"

**检查清单：**

1. Redis 是否正常运行？
```bash
curl http://localhost:8000/api/cache/health
```

2. API 是否添加了 `@cache_result` 装饰器？
```python
@cache_result(expire_seconds=600, key_prefix="my_api")
async def my_api_function():
    ...
```

3. 是否有参数导致缓存键不同？
```python
# 这两个会生成不同的缓存键
/api/analytics/diagnosis?diagnosis=diabetes
/api/analytics/diagnosis?diagnosis=Diabetes  # 注意大小写
```

### 问题 3：内存不足

**症状：**
```
OOM command not allowed when used memory > 'maxmemory'
```

**解决方案：**

1. 检查内存使用：
```bash
curl http://localhost:8000/api/cache/stats
```

2. 增加 Redis 内存限制（`docker-compose.yml`）：
```yaml
redis:
  command: redis-server --maxmemory 512mb  # 增加到 512MB
```

3. 或清除旧缓存：
```bash
curl -X POST http://localhost:8000/api/cache/clear-all
```

### 问题 4：缓存数据过期

**症状：**
- 用户看到旧数据

**解决方案：**

1. ETL 后清除缓存：
```bash
curl -X POST http://localhost:8000/api/cache/invalidate/after-etl
```

2. 调整缓存过期时间：
```python
# 从 30 分钟改为 5 分钟
@cache_result(expire_seconds=300, key_prefix="diagnosis")
```

---

## 💡 最佳实践

### 1. 缓存时间设置

```python
# ✅ 好的实践
@cache_result(expire_seconds=600)  # 10 分钟 - 热门数据
@cache_result(expire_seconds=1800) # 30 分钟 - 统计数据
@cache_result(expire_seconds=3600) # 1 小时 - 配置数据

# ❌ 不好的实践
@cache_result(expire_seconds=86400)  # 1 天 - 太长，数据会过期
@cache_result(expire_seconds=10)     # 10 秒 - 太短，缓存效果差
```

### 2. 缓存失效策略

**主动失效（推荐）：**
```python
# 数据更新时，主动清除相关缓存
@router.post("/etl/complete")
async def on_etl_complete():
    # 处理 ETL 完成逻辑
    
    # 清除相关缓存
    invalidate_diagnosis_cache()
    invalidate_analytics_cache()
```

**被动失效：**
```python
# 依赖 Redis 的过期时间自动清除
@cache_result(expire_seconds=300)
```

### 3. 缓存键设计

```python
# ✅ 好的键设计 - 包含所有相关参数
@cache_result(key_prefix="diagnosis_analysis")
async def get_diagnosis(diagnosis: str, year: int, type: str):
    # 键: diagnosis_analysis:get_diagnosis:diabetes:2024:yearly
    ...

# ❌ 不好的键设计 - 缺少参数
@cache_result(key_prefix="diagnosis")  # 太模糊
async def get_diagnosis(diagnosis: str, year: int):
    ...
```

### 4. 错误处理

系统已内置优雅降级：

```python
# Redis 不可用时，自动降级到无缓存模式
if not REDIS_AVAILABLE:
    return await func(*args, **kwargs)  # 直接执行函数
```

无需担心 Redis 故障导致 API 不可用！

### 5. 监控告警

设置告警阈值：

| 指标 | 警告阈值 | 严重阈值 |
|------|---------|---------|
| 缓存命中率 | < 70% | < 50% |
| 内存使用 | > 200MB | > 240MB |
| 键数量 | > 10000 | > 50000 |

### 6. 定期维护

**每天：**
- 检查缓存命中率
- 查看内存使用情况

**每周：**
- 分析缓存效果
- 优化缓存策略

**每月：**
- 清理无用的缓存模式
- 更新缓存时间配置

---

## 🎓 高级用法

### 手动设置缓存

```python
from app.core.cache import set_cache, get_cache

# 手动设置缓存
set_cache("my_custom_key", {"data": "value"}, expire_seconds=300)

# 手动获取缓存
cached_data = get_cache("my_custom_key")
```

### 条件缓存

```python
@router.get("/api/data")
async def get_data(use_cache: bool = True):
    if not use_cache:
        # 跳过缓存，直接查询
        return await query_database()
    
    # 使用缓存
    @cache_result(expire_seconds=600)
    async def cached_query():
        return await query_database()
    
    return await cached_query()
```

### 缓存预热

```python
# 在启动时预热常用缓存
@app.on_event("startup")
async def warmup_cache():
    logger.info("Warming up cache...")
    
    # 预加载热门诊断
    common_diagnoses = ["diabetes", "hypertension", "influenza"]
    for diagnosis in common_diagnoses:
        await get_diagnosis_analysis(diagnosis, "yearly")
    
    logger.info("Cache warmup complete!")
```

---

## 📞 获得帮助

如果遇到问题：

1. 查看日志：`docker logs fhir-backend | grep -i cache`
2. 检查健康状态：`curl http://localhost:8000/api/cache/health`
3. 查看 Redis 日志：`docker logs fhir-redis`

---

## 📚 相关文档

- [Redis 官方文档](https://redis.io/docs/)
- [FastAPI 缓存最佳实践](https://fastapi.tiangolo.com/)
- [安全设置指南](./SECURITY_SETUP_GUIDE.md)

---

**最后更新**: 2025-01-15

**记住**：缓存是性能优化的利器，但需要合理使用和管理！🚀

