# 🚀 新功能快速启动指南

## 📋 目录
- [患者群组分析](#患者群组分析)
- [自动化报告生成](#自动化报告生成)
- [数据质量监控](#数据质量监控)

---

## 👥 患者群组分析

### 快速开始

#### 1. 创建第一个群组
```bash
# 访问群组分析页面
http://localhost:3000/cohort

# 点击 "➕ 创建新群组"
# 填写：
- 名称: "糖尿病患者群组"
- 年龄: 40-70
- 诊断: Diabetes
- 日期: 2020-01-01 到 2023-12-31
```

#### 2. 查看群组统计
- 点击创建的群组卡片
- 查看：
  - 👥 患者总数
  - 📊 性别分布
  - 📈 年龄分布
  - 🏥 前五大诊断

#### 3. 对比多个群组
```bash
# 切换到 "🔍 对比模式"
# 选择2-5个群组
# 点击 "对比X个群组"
# 查看人口统计对比结果
```

### API 示例

```python
import requests

# 创建群组
response = requests.post('http://localhost:8000/api/cohort/cohorts', 
    headers={'Authorization': 'Bearer YOUR_TOKEN'},
    json={
        "name": "Diabetic Patients",
        "description": "Patients with diabetes diagnosis",
        "criteria": {
            "age_min": 40,
            "age_max": 70,
            "conditions": ["Diabetes"],
            "date_range_start": "2020-01-01",
            "date_range_end": "2023-12-31"
        }
    }
)

cohort_id = response.json()['id']

# 获取统计数据
stats = requests.get(f'http://localhost:8000/api/cohort/cohorts/{cohort_id}/stats',
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)

print(stats.json())
```

---

## 📄 自动化报告生成

### 快速开始

#### 1. 通过API生成即时报告

```python
import requests

# 生成报告
response = requests.post('http://localhost:8000/api/reports/generate',
    headers={'Authorization': 'Bearer YOUR_TOKEN'},
    json={
        "template_id": 1,  # 使用现有模板
        "name": "Monthly Summary Report",
        "format": "html",
        "filters": {}
    }
)

report_id = response.json()['id']

# 下载报告
report = requests.get(f'http://localhost:8000/api/reports/reports/{report_id}/download',
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)

# 保存为HTML文件
with open('report.html', 'w') as f:
    f.write(report.text)
```

#### 2. 创建报告模板

```python
# 创建自定义模板
response = requests.post('http://localhost:8000/api/reports/templates',
    headers={'Authorization': 'Bearer YOUR_TOKEN'},
    json={
        "name": "Quality Monthly Report",
        "description": "Monthly data quality report",
        "report_type": "quality",
        "format": "pdf",
        "template_config": {
            "sections": [
                {"type": "header", "title": "Monthly Quality Report"},
                {"type": "summary_stats"},
                {"type": "chart", "chart_type": "bar", "data_source": "top_conditions"}
            ]
        }
    }
)
```

#### 3. 设置定期报告

```python
# 创建每周自动报告
response = requests.post('http://localhost:8000/api/reports/scheduled',
    headers={'Authorization': 'Bearer YOUR_TOKEN'},
    json={
        "name": "Weekly Summary",
        "template_id": 1,
        "frequency": "weekly",
        "schedule_config": {
            "day_of_week": "monday",
            "time": "08:00"
        },
        "recipients": [
            "admin@example.com",
            "manager@example.com"
        ],
        "email_subject": "Weekly Analytics Report",
        "email_body": "Please find the weekly report attached."
    }
)
```

### 可用报告格式
- ✅ **JSON** - 结构化数据，适合程序处理
- ✅ **HTML** - 网页格式，适合在线查看
- 🔄 **PDF** - 打印友好（待完善）
- 🔄 **Excel** - 表格格式（待完善）

---

## ✅ 数据质量监控

### 快速开始

#### 1. 查看质量概览
```bash
# 访问数据质量仪表板
http://localhost:3000/data-quality

# 立即看到：
- 整体质量评分（0-100分）
- 四个维度评分（雷达图）
- 质量问题数量
```

#### 2. 查看详细指标
```bash
# 点击 "详细指标" 标签
# 查看：
- 📝 完整性（按表统计）
- 🔗 一致性（重复、孤立记录）
- ✓ 准确性（无效数据）
- ⏰ 及时性（更新延迟）
```

#### 3. 处理质量问题
```bash
# 点击 "问题" 标签
# 查看按严重程度分类的问题：
- 🔴 Critical - 立即处理
- 🟠 High - 优先处理
- 🟡 Medium - 计划处理
- 🔵 Low - 可选处理
```

#### 4. 分析质量趋势
```bash
# 点击 "趋势" 标签
# 查看30天质量变化趋势
# 识别改进或恶化的领域
```

### API 示例

```python
import requests

# 获取质量概览
overview = requests.get('http://localhost:8000/api/data-quality/overview',
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)

print(f"Overall Score: {overview.json()['overall_score']}")
print(f"Quality Issues: {overview.json()['quality_issues']}")

# 获取完整性指标
completeness = requests.get('http://localhost:8000/api/data-quality/completeness',
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)

for table in completeness.json():
    print(f"{table['table_name']}: {table['completeness_score']*100}%")

# 获取质量问题
issues = requests.get('http://localhost:8000/api/data-quality/issues?severity=critical',
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)

for issue in issues.json()['issues']:
    print(f"[{issue['severity']}] {issue['description']}")
```

### 质量评分标准
- **90-100%**: ✅ 优秀 (Excellent) - 绿色
- **70-89%**: ⚠️ 良好 (Good) - 橙色
- **50-69%**: ⚠️ 一般 (Fair) - 橙色
- **0-49%**: ❌ 较差 (Poor) - 红色

---

## 🎯 常见使用场景

### 场景1：临床研究项目
```bash
1. 创建研究群组
   - 群组分析 → 创建群组 → 设置纳入/排除标准
   
2. 导出群组数据
   - 选择群组 → 查看患者列表 → 导出CSV
   
3. 生成研究报告
   - 报告生成 → 选择模板 → 生成PDF报告
```

### 场景2：质量改进项目
```bash
1. 评估当前质量
   - 数据质量 → 查看概览 → 识别问题区域
   
2. 导出问题列表
   - 问题标签 → 筛选严重问题 → 导出处理
   
3. 监控改进效果
   - 趋势标签 → 查看30天变化 → 验证提升
```

### 场景3：月度运营报告
```bash
1. 设置自动报告
   - API调用 → 创建scheduled_report → 设置收件人
   
2. 自动生成发送
   - 每月1日自动执行 → 生成PDF → 发送邮件
   
3. 查看历史报告
   - 报告列表 → 查看所有生成的报告 → 下载存档
```

---

## 🔧 故障排查

### 问题：群组患者数为0
```bash
✅ 检查筛选条件是否过于严格
✅ 验证诊断名称是否准确（区分大小写）
✅ 确认日期范围包含数据
✅ 检查是否选择了正确的job_id
```

### 问题：报告生成失败
```bash
✅ 检查模板配置是否正确
✅ 验证用户有足够权限
✅ 查看后端日志获取详细错误
✅ 确保/tmp/reports目录可写
```

### 问题：质量评分异常低
```bash
✅ 检查是否最近导入新数据
✅ 验证数据源质量
✅ 查看具体问题列表定位原因
✅ 运行数据清洗流程
```

---

## 📊 性能提示

### 大数据集优化
```python
# 使用分页获取大量患者
for page in range(0, total_patients, 100):
    patients = requests.get(
        f'http://localhost:8000/api/cohort/cohorts/{id}/patients',
        params={'skip': page, 'limit': 100}
    )
    process(patients.json()['patients'])
```

### 并行报告生成
```python
import concurrent.futures

templates = [1, 2, 3, 4]

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(generate_report, t) for t in templates]
    reports = [f.result() for f in futures]
```

---

## 🎓 最佳实践

### 群组命名规范
```
✅ 好的命名: "糖尿病患者_40-70岁_2023"
❌ 差的命名: "群组1"

建议格式: [病症]_[年龄范围]_[时间段]
```

### 报告调度建议
```
✅ 低峰时段运行（如凌晨2点）
✅ 避免在业务高峰期生成大报告
✅ 设置合理的过期时间（30天）
✅ 定期清理旧报告
```

### 质量监控频率
```
✅ 每日检查：整体质量评分
✅ 每周检查：详细指标和问题列表
✅ 每月检查：质量趋势和改进计划
✅ 实时告警：严重质量问题
```

---

## 📖 更多资源

- **完整文档**: `PHASE_1_FEATURES_COMPLETED.md`
- **API文档**: http://localhost:8000/docs
- **示例代码**: `/examples` 目录（待创建）
- **视频教程**: [YouTube链接]（待创建）

---

## 🆘 获取帮助

遇到问题？
1. 📖 查看完整文档
2. 🔍 搜索GitHub Issues
3. 💬 在Issues中提问
4. 📧 联系技术支持

---

**开始探索新功能吧！** 🚀✨

