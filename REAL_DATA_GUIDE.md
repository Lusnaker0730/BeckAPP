# 🎯 真实数据完整使用指南

## 现在系统已经完全支持真实数据！

### ✅ 已实现的功能

1. **完整的 ETL 流程**
   - Extract: 从 FHIR 服务器提取数据
   - Transform: 自动将 NDJSON 转换为结构化数据
   - Load: **自动导入到 PostgreSQL 数据库**

2. **真实的 Dashboard 和分析**
   - Dashboard 显示真实的统计数据
   - 诊断分析使用数据库中的真实数据
   - 所有图表都连接到真实 API

3. **自动化流程**
   - 下载完成后**自动转换和加载数据**
   - 无需手动触发 Transform 和 Load

---

## 📋 完整的使用流程

### 步骤 1: 登录系统

1. 访问: http://localhost:3000/login
2. 登录账号:
   ```
   用户名: engineer
   密码: engineer123
   ```

### 步骤 2: 配置并启动 Bulk Data 提取

1. **进入后端管理**
   - 点击左侧导航栏 "后端管理"
   
2. **在 BULK DATA API 标签中配置**:
   
   **推荐使用 SMART Health IT 沙盒**:
   
   a. 打开新标签页访问: https://bulk-data.smarthealthit.org/
   
   b. 配置选项：
   - Database Size: `1,000 Patients`
   - Require Authentication: `No`
   - Resources per File: `100`
   
   c. 复制页面底部的 **"FHIR Server URL"**
   
   d. 回到系统，在 FHIR Server URL 中粘贴
   
3. **选择资源类型**:
   - ✅ Patient（病患）
   - ✅ Condition（诊断）
   - ✅ Encounter（就诊）
   - ✅ Observation（观察）

4. **点击 "开始提取"**

### 步骤 3: 监控 ETL 进度

1. **切换到 "ETL 任务" 标签**

2. **查看任务状态**:
   - `in-progress`: 正在提取数据
   - `completed`: 提取完成

3. **页面每 5 秒自动刷新** - 无需手动刷新

4. **查看处理记录数**:
   - 任务完成后会显示实际处理的记录数
   - 不再是 0！

5. **点击 "查看日志" 查看详情**:
   - 任务详情
   - 下载的文件信息
   - 转换和加载的记录数

---

## 🔄 自动化 ETL 流程

**新功能：下载完成后自动执行！**

```
1. Extract（提取）
   ↓ 从 FHIR 服务器下载 NDJSON 文件
   ↓ 保存到 /data/bulk/{job_id}/
   
2. Transform（转换）
   ↓ 自动触发！
   ↓ 解析 NDJSON 
   ↓ 转换为结构化 JSON
   ↓ 保存到 /data/bulk/{job_id}/transformed/
   
3. Load（加载）
   ↓ 自动触发！
   ↓ 读取转换后的数据
   ↓ 插入到 PostgreSQL
   ↓ 处理冲突（使用 ON CONFLICT DO UPDATE）
   
4. 完成！
   ✅ 数据已在数据库中
   ✅ Dashboard 显示真实数据
   ✅ 诊断分析可用
```

---

## 📊 查看真实数据

### 在 Dashboard（仪表板）

1. **登录后点击左侧 "Dashboard"**

2. **您会看到真实的统计数据**:
   - 总病患数（Total Patients）
   - 总诊断数（Total Conditions）
   - 总就诊次数（Total Encounters）
   - 总观察记录（Total Observations）

3. **真实的图表**:
   - 诊断趋势图表（过去 12 个月）
   - 前五大诊断

### 在诊断分析

1. **点击左侧 "诊断分析"**

2. **选择诊断类型**:
   - 流感（Influenza）
   - 心肌梗塞（Myocardial Infarction）
   - 肺腺癌（Lung Adenocarcinoma）
   - 糖尿病（Diabetes）
   - 高血压（Hypertension）
   - 慢性阻塞性肺病（COPD）

3. **选择时间范围**:
   - 月度（Monthly）
   - 季度（Quarterly）
   - 年度（Yearly）

4. **查看真实分析结果**:
   - 柱状图显示发生人次
   - 折线图显示趋势
   - 详细数据表格

---

## 🗄️ 数据库详情

### 数据存储

提取的数据存储在 PostgreSQL 中的以下表：

- `patients` - 病患数据
- `conditions` - 诊断数据
- `encounters` - 就诊数据
- `observations` - 观察记录

### 查看数据库内容

```bash
# 连接到数据库容器
docker exec -it fhir-postgres psql -U fhir_user -d fhir_analytics

# 查看病患总数
SELECT COUNT(*) FROM patients;

# 查看诊断总数
SELECT COUNT(*) FROM conditions;

# 查看最近的诊断
SELECT fhir_id, code_text, onset_datetime FROM conditions LIMIT 10;

# 退出
\q
```

---

## 🎯 完整测试示例

### 示例：提取 1000 个病患的数据

**预期结果**:

1. **ETL 任务**:
   - 状态: `completed`
   - 处理记录数: ~1,000-2,000 条（Patient + Condition + Encounter + Observation）

2. **Dashboard 显示**:
   - Total Patients: ~1,000
   - Total Conditions: ~200-500
   - Total Encounters: ~300-600
   - Total Observations: ~100-300

3. **诊断分析**:
   - 可以看到各种诊断的真实分布
   - 图表显示时间趋势

**耗时**: 约 1-2 分钟（包括提取、转换、加载）

---

## 🔍 故障排除

### 问题 1: Dashboard 还是显示 0

**原因**: ETL 任务可能还在进行中

**解决**:
1. 进入 "后端管理" → "ETL 任务"
2. 确认任务状态为 `completed`
3. 刷新 Dashboard 页面（Ctrl+F5）

### 问题 2: ETL 任务失败

**检查日志**:
```bash
# 查看 ETL service 日志
docker-compose logs etl-service --tail=100

# 查看 backend 日志
docker-compose logs backend --tail=100
```

**常见原因**:
- FHIR Server URL 不正确
- 网络连接问题
- 数据库连接失败

### 问题 3: 记录数为 0

**原因**: 这是旧任务（修复前创建的）

**解决**: 启动一个新的提取任务

---

## 📈 数据质量说明

### SMART Health IT 沙盒数据

- **真实的 FHIR 格式**
- **模拟的医疗数据**
- **符合 FHIR R4 标准**
- **包含完整的关联关系**

### 数据特点

1. **Patient（病患）**:
   - 包含姓名、性别、出生日期
   - 地址和联系方式
   - 婚姻状况

2. **Condition（诊断）**:
   - ICD-10 代码
   - 临床状态
   - 发病时间
   - 关联的就诊记录

3. **Encounter（就诊）**:
   - 就诊类型
   - 就诊时间
   - 就诊原因
   - 关联的病患

4. **Observation（观察）**:
   - 观察项目（如生命体征）
   - 测量值
   - 测量时间
   - LOINC 代码

---

## 🔮 高级功能

### 增量更新

使用 `Since Date` 参数只提取新数据：

1. 在 BULK DATA API 中设置 "Since Date"
2. 例如: `2024-01-01`
3. 只会提取该日期之后的数据
4. 适合定期同步

### 大数据集测试

在 SMART Health IT 沙盒中选择更大的数据集：
- 10,000 Patients: ~5-10 分钟
- 100,000 Patients: ~30-60 分钟
- 1,000,000 Patients: 测试环境不推荐

---

## ✅ 验证数据成功导入

### 方法 1: 通过 Dashboard

1. 访问 Dashboard
2. 应该看到非零的统计数字
3. 图表应该显示数据点

### 方法 2: 通过 API

```bash
# 测试 stats API
Invoke-WebRequest -Uri "http://localhost:8000/api/analytics/stats" `
  -Headers @{Authorization="Bearer YOUR_TOKEN"} `
  -UseBasicParsing | ConvertFrom-Json
```

应该返回类似：
```json
{
  "totalPatients": 1000,
  "totalConditions": 450,
  "totalEncounters": 560,
  "totalObservations": 280
}
```

### 方法 3: 直接查询数据库

```bash
docker exec fhir-postgres psql -U fhir_user -d fhir_analytics -c "SELECT COUNT(*) FROM patients;"
```

---

## 🎉 成功！

现在您的系统：
- ✅ 使用真实的 FHIR 数据
- ✅ 自动化 ETL 流程
- ✅ Dashboard 显示真实统计
- ✅ 诊断分析基于真实数据
- ✅ 所有图表都是动态生成的

**不再是假数据或静态展示 - 这是一个真正能用的 FHIR Analytics 平台！** 🚀

---

## 📚 相关文档

- [Bulk Data 使用指南](BULK_DATA_GUIDE.md)
- [SMART Health IT 配置](SMART_BULK_DATA_SETUP.md)
- [快速开始](QUICKSTART.md)
- [API 文档](API_DOCUMENTATION.md)

