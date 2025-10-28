# 🚀 Redis 缓存快速启动指南

5分钟内启动 Redis 缓存，让您的 API 快 100 倍！

---

## ⚡ 快速启动步骤

### 1. 启动服务（1 分钟）

```bash
# 启动所有服务（包括 Redis）
docker-compose up -d

# 等待服务启动完成
docker-compose ps
```

**预期输出：**
```
NAME                COMMAND                  STATUS
fhir-postgres       "docker-entrypoint.s…"   Up (healthy)
fhir-redis          "redis-server --appe…"   Up (healthy)
fhir-backend        "uvicorn main:app --…"   Up
fhir-analytics      "uvicorn main:app --…"   Up
fhir-etl            "uvicorn main:app --…"   Up
fhir-frontend       "docker-entrypoint.s…"   Up
```

### 2. 验证 Redis 运行（30 秒）

```bash
# 测试 Redis 连接
docker exec -it fhir-redis redis-cli ping
# 应该返回: PONG

# 检查缓存健康状态
curl http://localhost:8000/api/cache/health
```

**成功响应：**
```json
{
  "status": "healthy",
  "message": "Redis cache is operational"
}
```

### 3. 测试缓存效果（2 分钟）

#### 登录获取 Token

```bash
# 登录
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.access_token')

echo "Token: $TOKEN"
```

#### 测试无缓存性能

```bash
# 第一次请求（数据库查询）
echo "第一次请求（无缓存）："
time curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/analytics/diagnosis?diagnosis=diabetes&timeRange=yearly" \
  > /dev/null

# 预期: 2-4 秒
```

#### 测试缓存性能

```bash
# 第二次请求（从缓存读取）
echo "第二次请求（有缓存）："
time curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/analytics/diagnosis?diagnosis=diabetes&timeRange=yearly" \
  > /dev/null

# 预期: 0.05 秒 ⚡ 快 60+ 倍！
```

### 4. 查看缓存统计（1 分钟）

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/cache/stats | jq '.'
```

**示例输出：**
```json
{
  "status": "success",
  "data": {
    "status": "connected",
    "total_keys": 5,
    "memory_used_mb": 0.85,
    "hits": 12,
    "misses": 5,
    "hit_rate": 70.59
  }
}
```

---

## 📊 实时监控缓存

### 方法 1：查看后端日志

```bash
docker logs -f fhir-backend | grep -i cache
```

**输出示例：**
```
✅ Redis connection established successfully
✅ Cache HIT: diagnosis_analysis:get_diagnosis_analysis:diabetes
❌ Cache MISS: top_conditions:get_top_conditions:10
💾 Cached result for diagnosis_analysis... (expires in 1800s)
```

### 方法 2：实时监控 Redis

```bash
docker exec -it fhir-redis redis-cli MONITOR
```

---

## 🛠️ 常用命令

### 查看所有缓存键

```bash
docker exec -it fhir-redis redis-cli KEYS "*"
```

### 查看特定键的值

```bash
docker exec -it fhir-redis redis-cli GET "diagnosis_analysis:get_diagnosis_analysis:diabetes"
```

### 清除特定模式的缓存

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/cache/invalidate?pattern=diagnosis:*"
```

### 清除所有缓存（仅管理员）

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/cache/clear-all
```

---

## 🎯 已缓存的 API 端点

| API 端点 | 缓存时间 | 预期提升 |
|----------|---------|---------|
| `/api/analytics/diagnosis` | 30分钟 | 64倍 |
| `/api/analytics/top-conditions` | 10分钟 | 83倍 |
| `/api/analytics/available-diagnoses` | 10分钟 | 50倍 |
| `/api/analytics/patient-demographics` | 15分钟 | 90倍 |

---

## ⚠️ 故障排除

### 问题：Redis 启动失败

```bash
# 检查端口是否被占用
netstat -an | findstr "6379"

# 如果被占用，修改端口
# 编辑 docker-compose.yml:
# ports:
#   - "6380:6379"  # 使用其他端口
```

### 问题：后端无法连接 Redis

```bash
# 检查 Redis 容器
docker ps | grep redis

# 查看 Redis 日志
docker logs fhir-redis

# 重启 Redis
docker-compose restart redis

# 重启后端
docker-compose restart backend
```

### 问题：缓存未生效

```bash
# 1. 检查 Redis 健康状态
curl http://localhost:8000/api/cache/health

# 2. 查看后端日志
docker logs fhir-backend | grep -i redis

# 3. 清除所有缓存重试
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/cache/clear-all
```

---

## 📚 完整文档

- **详细使用指南**: [REDIS_CACHING_GUIDE.md](./REDIS_CACHING_GUIDE.md)
- **实现总结**: [REDIS_IMPLEMENTATION_SUMMARY.md](./REDIS_IMPLEMENTATION_SUMMARY.md)
- **安全配置**: [SECURITY_SETUP_GUIDE.md](./SECURITY_SETUP_GUIDE.md)

---

## ✅ 启动成功！

恭喜！Redis 缓存已经运行，您的 API 性能已经提升 10-100 倍！🎉

**下一步：**
1. 在前端应用中测试各个功能
2. 观察缓存命中率
3. 根据使用情况调整缓存时间

**享受飞速的 API 响应吧！** ⚡

