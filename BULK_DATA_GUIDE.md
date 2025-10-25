# FHIR Bulk Data API 使用指南

## 🎯 功能说明

现在系统已经完全支持**真实的 FHIR 数据提取功能**，包括：

1. ✅ **Bulk Data $export API**（如果 FHIR 服务器支持）
2. ✅ **FHIR Search API 备用方案**（当 $export 不可用时自动切换）
3. ✅ **自动下载并保存 NDJSON 文件**
4. ✅ **后台任务监控**
5. ✅ **实时状态更新**

---

## 📋 使用步骤

### 1. 登录系统

访问: http://localhost:3000/login

使用以下账号登录：
```
用户名: engineer
密码: engineer123
```

或

```
用户名: admin
密码: admin123
```

### 2. 进入后端管理面板

登录后，点击左侧导航栏的 **"后端管理"** 或访问: http://localhost:3000/admin

### 3. 配置 FHIR Server

在 **BULK DATA API** 标签页中：

#### 推荐的公开 FHIR 服务器

**HAPI FHIR 公开服务器**（推荐）:
```
FHIR Server URL: https://hapi.fhir.org/baseR4
```

**其他可用选项**:
```
https://server.fire.ly/r4
https://launch.smarthealthit.org/v/r4/fhir
```

### 4. 选择资源类型

勾选您要提取的资源类型：
- ✅ Patient（病患）
- ✅ Condition（诊断）
- ✅ Encounter（就诊）
- ✅ Observation（观察记录）

### 5. 开始提取

点击 **"开始提取"** 按钮

系统会：
1. 尝试使用 Bulk Data $export API
2. 如果不支持，自动切换到 FHIR Search API（备用方案）
3. 后台自动下载数据并保存为 NDJSON 文件
4. 实时更新任务状态

### 6. 监控进度

切换到 **"ETL 任务"** 标签页查看：
- 任务状态（pending / in-progress / completed / failed）
- 开始时间和结束时间
- 已处理的记录数

---

## 🔧 技术细节

### Bulk Data Export 流程

```
前端 → Backend API → ETL Service → FHIR Server
                           ↓
                    下载 NDJSON 文件
                           ↓
                    保存到 /data/bulk/{job_id}/
```

### 数据存储位置

在 Docker 容器内：
```
/data/bulk/{job_id}/Patient.ndjson
/data/bulk/{job_id}/Condition.ndjson
/data/bulk/{job_id}/Encounter.ndjson
/data/bulk/{job_id}/Observation.ndjson
```

这些文件挂载到 Docker volume: `fhir_bulk_data`

### API 端点

#### Backend API
```
POST /api/admin/bulk-data/fetch
GET  /api/admin/etl-jobs
GET  /api/admin/etl-jobs/{job_id}/status
```

#### ETL Service API
```
POST /api/bulk-data/kick-off
GET  /api/bulk-data/status/{job_id}
GET  /api/bulk-data/jobs
```

---

## 📊 数据量预期

### HAPI FHIR 公开服务器

使用 FHIR Search 备用方案时，每种资源类型最多提取 **1000 条记录**（10 页 × 100 条/页）

这是为了避免过载公开服务器。如果需要更多数据：
- 使用自己的 FHIR 服务器
- 或修改 `etl-service/app/api/bulk_data.py` 中的 `max_pages` 参数

---

## 🐛 常见问题

### Q: 提示"ETL service returned error"
**A**: 检查 ETL service 日志：
```bash
docker-compose logs etl-service --tail=50
```

### Q: 任务状态一直显示"pending"
**A**: 后台任务可能失败，检查 backend 日志：
```bash
docker-compose logs backend --tail=50
```

### Q: 如何查看下载的数据？
**A**: 进入 ETL service 容器：
```bash
docker exec -it fhir-etl ls -lh /data/bulk/
```

### Q: 数据下载成功后如何导入数据库？
**A**: 目前需要使用 Transform API：
```bash
POST http://localhost:8001/api/transform/process
{
  "job_id": "your_job_id",
  "resource_types": ["Patient", "Condition"]
}
```

---

## 🚀 下一步开发

要实现完整的 ETL 流程，还需要：

1. **Transform 阶段**: 将 NDJSON 转换为数据库格式
2. **Load 阶段**: 将数据插入 PostgreSQL
3. **自动化流程**: 下载完成后自动触发转换和加载
4. **增量更新**: 支持定期同步新数据

这些功能的骨架已经存在于：
- `etl-service/app/api/transform.py`
- `etl-service/app/core/transformer.py`

---

## ✅ 验证功能

### 测试 1: 手动调用 ETL Service

```bash
curl -X POST http://localhost:8001/api/bulk-data/kick-off \
  -H "Content-Type: application/json" \
  -d '{
    "fhir_server_url": "https://hapi.fhir.org/baseR4",
    "resource_types": ["Patient"],
    "since": null
  }'
```

### 测试 2: 检查任务状态

```bash
curl http://localhost:8001/api/bulk-data/jobs
```

### 测试 3: 查看具体任务

```bash
curl http://localhost:8001/api/bulk-data/status/{job_id}
```

---

**现在您的系统已经具备真实的 FHIR 数据提取能力！** 🎉

试试看，使用 engineer 账号登录并启动一个 bulk data 提取任务！

