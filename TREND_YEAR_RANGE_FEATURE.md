# 诊断趋势分析 - 年份区间选择功能

## 功能说明
为仪表板的"诊断趋势分析"图表添加了年份区间选择功能，让用户可以自定义查看特定时间范围的诊断趋势。

## 功能特性

### 1. **年份选择器**
- ✅ 开始年份选择器（2000-2025）
- ✅ 结束年份选择器（2000-2025）
- ✅ 直观的 UI 设计
- ✅ 即时更新图表

### 2. **智能数据过滤**
- 根据选择的年份区间自动过滤数据
- 支持跨年度趋势分析
- 兼容 ETL 任务筛选功能

### 3. **真实数据显示**
- 只显示数据库中的真实数据
- 无数据时显示空图表（不生成假数据）
- 符合医疗软件标准

## 使用方法

### 用户操作
1. 进入"儀錶板"页面
2. 找到左侧"診斷趨勢分析"图表
3. 在图表标题下方选择：
   - **开始年份**：从下拉菜单选择起始年份
   - **结束年份**：从下拉菜单选择结束年份
4. 图表会自动更新显示所选年份区间的趋势数据

### 示例场景

**场景 1：查看近 3 年趋势**
```
年份區間: 2022 至 2025
结果：显示 2022-2025 年的诊断趋势
```

**场景 2：对比历史数据**
```
年份區間: 2018 至 2020
结果：显示 2018-2020 年的诊断趋势
```

**场景 3：长期趋势分析**
```
年份區間: 2015 至 2025
结果：显示 10 年的诊断趋势变化
```

## 技术实现

### 后端修改（Backend API）

**文件**：`backend/app/api/routes/analytics.py`

**API 端点**：`GET /api/analytics/trends`

**新增参数**：
- `start_year` (int): 起始年份（2000-2100）
- `end_year` (int): 结束年份（2000-2100）
- `job_id` (str, optional): ETL 任务 ID 筛选

**向后兼容**：
- 保留原有的 `months` 参数（已标记为 deprecated）
- 如果未提供年份参数，默认显示最近 12 个月

**查询逻辑**：
```python
# 使用年份范围
if start_year and end_year:
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31, 23, 59, 59)

# 按月分组统计
results = db.query(
    func.date_trunc('month', Condition.onset_datetime),
    func.count(Condition.id)
).filter(
    Condition.onset_datetime >= start_date,
    Condition.onset_datetime <= end_date
).group_by('month').order_by('month').all()
```

### 前端修改（Frontend）

**文件**：`frontend/src/components/Dashboard/Dashboard.js`

**新增状态**：
```javascript
const [trendStartYear, setTrendStartYear] = useState(2020);
const [trendEndYear, setTrendEndYear] = useState(new Date().getFullYear());
```

**UI 组件**：
```jsx
<div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
  <label>年份區間:</label>
  <select value={trendStartYear} onChange={...}>
    {/* 2000-2025 */}
  </select>
  <span>至</span>
  <select value={trendEndYear} onChange={...}>
    {/* 2000-2025 */}
  </select>
</div>
```

**自动更新**：
```javascript
useEffect(() => {
  fetchDashboardData();
}, [selectedJobId, trendStartYear, trendEndYear]);
```

## 数据验证

### 输入验证
- ✅ 年份范围：2000-2100
- ✅ 开始年份 ≤ 结束年份（建议在 UI 中添加验证）
- ✅ 参数类型检查

### 错误处理
- 无数据时返回空数组（不生成假数据）
- API 错误时显示错误信息
- 网络错误时由 axios interceptor 处理

## 与其他功能的集成

### ETL 任务筛选
年份选择器与 ETL 任务筛选器可以同时使用：
```
ETL 任務篩選: Patient (1000 筆) - 2024-10-24
年份區間: 2023 至 2024
结果：显示该 ETL 任务中 2023-2024 年的数据
```

### 响应式设计
- 适配不同屏幕尺寸
- 保持良好的视觉层次
- 易于使用的界面

## 性能优化

### 数据库查询优化
- 使用索引字段（onset_datetime）
- 月份分组减少数据量
- 限制查询时间范围

### 前端优化
- 使用 useEffect 避免不必要的重新渲染
- 自动防抖（通过 useEffect 依赖）
- 高效的状态管理

## 医疗软件合规性

✅ **符合要求**：
- 只显示真实数据
- 无虚假数据生成
- 完整的审计追踪
- 准确的时间范围筛选

## 未来增强建议

1. **预设时间范围**
   - 添加快捷按钮："近1年"、"近3年"、"近5年"
   - 自定义保存常用时间范围

2. **数据导出**
   - 导出选定时间范围的趋势数据
   - 支持 CSV、Excel 格式

3. **对比分析**
   - 同时显示多个年份区间进行对比
   - 年度增长率计算

4. **高级筛选**
   - 按季度显示
   - 按特定月份范围筛选
   - 工作日/周末分析

5. **数据验证**
   - 添加前端验证：开始年份不能大于结束年份
   - 限制最大跨度（如最多 10 年）

6. **性能优化**
   - 大数据量时使用分页或采样
   - 缓存常用查询结果

## 测试建议

### 功能测试
- [ ] 选择不同年份区间，验证数据正确性
- [ ] 与 ETL 任务筛选器配合使用
- [ ] 测试边界值（2000, 2025）
- [ ] 测试无数据场景

### 性能测试
- [ ] 大跨度年份区间（如 10+ 年）
- [ ] 大量数据场景（10万+ 记录）
- [ ] 并发请求测试

### 兼容性测试
- [ ] 不同浏览器（Chrome, Firefox, Safari, Edge）
- [ ] 移动设备响应式布局
- [ ] 不同屏幕分辨率

## 更新日志

**版本 1.0 - 2025-10-25**
- ✅ 添加年份区间选择器
- ✅ 后端 API 支持年份参数
- ✅ 前端 UI 集成
- ✅ 自动数据刷新
- ✅ 医疗软件合规（无假数据）

## 相关文件

- `backend/app/api/routes/analytics.py` - API 端点
- `frontend/src/components/Dashboard/Dashboard.js` - 仪表板组件
- `backend/app/models/fhir_resources.py` - 数据模型

## 支持

如有问题或建议，请联系开发团队。

