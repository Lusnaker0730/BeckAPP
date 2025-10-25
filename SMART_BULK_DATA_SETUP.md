# SMART Health IT Bulk Data 测试指南

## 🌐 关于 SMART Health IT Bulk Data Server

[SMART Health IT Bulk Data Server](https://bulk-data.smarthealthit.org/) 是一个专门用于测试 FHIR Bulk Data API 的沙盒环境。

### 优势
- ✅ 完整支持 Bulk Data $export API
- ✅ 可配置数据库大小（100 到 1,000,000 患者）
- ✅ 支持 Group-based export
- ✅ 可选的认证功能
- ✅ 模拟各种错误场景
- ✅ 比公开 FHIR 服务器更稳定

---

## 🚀 快速开始（无需认证）

### 步骤 1: 获取 FHIR Server URL

访问: https://bulk-data.smarthealthit.org/

#### 配置选项（推荐设置）:

1. **Database Size**: 选择 `1,000 Patients`（测试用）
2. **Require Authentication**: 选择 `No`
3. **Resources per File**: 保持 `100`
4. **其他选项**: 保持默认

#### 获取 FHIR Server URL:

在页面底部找到 **"FHIR Server URL"**，复制 URL。

格式类似：
```
https://bulk-data.smarthealthit.org/eyJ...很长的字符串.../fhir
```

### 步骤 2: 在系统中使用

1. **登录**: http://localhost:3000/login
   ```
   用户名: engineer
   密码: engineer123
   ```

2. **进入后端管理面板**

3. **配置 BULK DATA API**:
   - **FHIR Server URL**: 粘贴刚才复制的完整 URL
   - **资源类型**: 勾选 Patient, Condition, Encounter, Observation
   - **Since Date**: 留空

4. **点击"开始提取"**

5. **监控进度**: 切换到"ETL 任务"标签

---

## 🔐 使用认证（可选，更真实）

如果您想测试完整的认证流程：

### 步骤 1: 在沙盒配置认证

1. 访问 https://bulk-data.smarthealthit.org/
2. **Require Authentication**: 选择 `Yes`
3. **Authentication Type**: 
   - 选择 `Backend Services` (SMART Backend Services)
4. 记录以下信息：
   - FHIR Server URL
   - Token Endpoint URL
   - Client ID

### 步骤 2: 生成密钥对（JWKS）

在沙盒页面：
1. 点击 **"Generate"** 按钮
2. 选择 `Generate RS384` 或 `Generate ES384`
3. 保存生成的：
   - Private Key（私钥）
   - Public Key（公钥）
   - JWKS（公钥集）

### 步骤 3: 配置系统支持认证

需要在 ETL Service 中添加 JWT 认证功能（见下方代码）

---

## 📊 推荐的测试配置

### 配置 A: 快速测试（小数据集）
```
Database Size: 100 Patients
Require Authentication: No
Resources per File: 10
```
**适合**: 首次测试，验证功能

### 配置 B: 标准测试（中等数据集）
```
Database Size: 1,000 Patients
Require Authentication: No
Resources per File: 100
```
**适合**: 常规开发和测试

### 配置 C: 压力测试（大数据集）
```
Database Size: 10,000 Patients
Require Authentication: Yes
Resources per File: 1,000
```
**适合**: 性能测试

---

## 🎯 Group-Based Export

SMART Bulk Data 支持按 Group 导出数据：

### 获取可用的 Groups

1. 在沙盒配置页面，查看 **"Available Groups"** 表格
2. 复制 Group ID

### 使用 Group Export

在系统中使用以下 URL 格式：
```
{FHIR_SERVER_URL}/Group/{group_id}/$export
```

例如：
```
https://bulk-data.smarthealthit.org/.../fhir/Group/example-group-id/$export
```

---

## 🧪 测试示例

### 示例 1: 无认证导出

**沙盒配置**:
- Require Authentication: `No`
- Database Size: `1,000 Patients`

**系统配置**:
```
FHIR Server URL: https://bulk-data.smarthealthit.org/eyJ...../fhir
Resource Types: Patient, Condition, Encounter, Observation
```

**预期结果**:
- 状态变为 "in-progress"
- 几秒到几分钟后完成
- 下载约 1000 条 Patient 记录和相关资源

### 示例 2: 测试错误处理

**沙盒配置**:
- Simulate Error: 选择 `Bulk Status - File generation failed`

**预期结果**:
- 任务应该显示失败状态
- 错误日志包含错误信息

---

## 🔧 直接 API 测试

### 测试 1: 发起 Bulk Export

```bash
# PowerShell
$serverUrl = "https://bulk-data.smarthealthit.org/YOUR_CONFIG/fhir"
$exportUrl = "$serverUrl/`$export?_type=Patient,Condition"

Invoke-WebRequest -Uri $exportUrl `
  -Method GET `
  -Headers @{
    "Accept" = "application/fhir+json"
    "Prefer" = "respond-async"
  }
```

应该返回 **202 Accepted** 和 `Content-Location` header

### 测试 2: 检查导出状态

```bash
# 使用从上面获得的 Content-Location URL
$statusUrl = "从 Content-Location header 获取"

Invoke-WebRequest -Uri $statusUrl `
  -Method GET `
  -Headers @{
    "Accept" = "application/fhir+json"
  }
```

**进行中**: 返回 202
**完成**: 返回 200 + manifest JSON

---

## 📝 完整工作流程

### 使用我们的系统

```
1. 配置沙盒
   ↓
2. 复制 FHIR Server URL
   ↓
3. 登录系统 (engineer/engineer123)
   ↓
4. 进入后端管理
   ↓
5. 粘贴 URL 并选择资源类型
   ↓
6. 点击"开始提取"
   ↓
7. 系统自动：
   - 调用 $export API
   - 轮询状态
   - 下载 NDJSON 文件
   - 保存到 /data/bulk/
   ↓
8. 查看"ETL 任务"标签的进度
```

### 查看结果

```bash
# 列出所有任务
docker exec -it fhir-etl ls -lh /data/bulk/

# 查看具体任务的文件
docker exec -it fhir-etl ls -lh /data/bulk/{job_id}/

# 查看文件内容（前10行）
docker exec -it fhir-etl head -n 10 /data/bulk/{job_id}/Patient.ndjson
```

---

## 🐛 常见问题

### Q: URL 太长无法粘贴？
**A**: SMART Bulk Data 的 URL 包含配置参数，所以很长。这是正常的，直接复制粘贴即可。

### Q: 提示认证错误？
**A**: 确保沙盒配置中 "Require Authentication" 设置为 `No`，或者实现 JWT 认证。

### Q: 数据下载很慢？
**A**: 
- 减少 Database Size
- 检查网络连接
- 查看 ETL service 日志：`docker-compose logs etl-service -f`

### Q: 想要更多数据？
**A**: 在沙盒中增加 Database Size，但注意：
- 100 Patients: 几秒
- 1,000 Patients: ~30秒
- 10,000 Patients: 几分钟
- 100,000+ Patients: 可能需要很长时间

---

## 🎓 学习资源

- [SMART Bulk Data 文档](https://bulk-data.smarthealthit.org/)
- [Bulk Data Access IG](https://hl7.org/fhir/uv/bulkdata/)
- [Backend Services 认证](https://hl7.org/fhir/uv/bulkdata/authorization/index.html)

---

## ✅ 快速检查清单

使用此清单确保设置正确：

- [ ] 访问 https://bulk-data.smarthealthit.org/
- [ ] 设置 Database Size 为 1,000 Patients
- [ ] 设置 Require Authentication 为 No
- [ ] 复制 FHIR Server URL
- [ ] 登录系统 (engineer/engineer123)
- [ ] 进入后端管理面板
- [ ] 粘贴 FHIR Server URL
- [ ] 选择资源类型
- [ ] 点击"开始提取"
- [ ] 在"ETL 任务"查看进度
- [ ] 等待任务完成（状态变为 completed）
- [ ] 检查下载的文件

---

**现在就试试吧！这是测试 Bulk Data API 最好的沙盒环境！** 🚀

