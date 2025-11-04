# 🔐 審計日誌系統

## 概述

審計日誌系統是 FHIR Analytics Platform 的核心安全功能，自動記錄系統中所有重要操作，滿足醫療數據系統的合規性和安全審計要求（HIPAA、GDPR等）。

### 主要功能

- ✅ **自動記錄** - 所有 API 請求自動記錄，無需手動干預
- ✅ **用戶追蹤** - 記錄操作用戶、角色、IP 地址
- ✅ **操作詳情** - HTTP 方法、端點、請求參數、響應狀態
- ✅ **性能監控** - 記錄請求處理時間
- ✅ **敏感數據脫敏** - 自動移除密碼、令牌等敏感信息
- ✅ **強大的查詢** - 多維度過濾、全文搜索、統計分析
- ✅ **可視化儀表板** - 實時統計和趨勢分析

---

## 安裝

### 1. 運行安裝腳本

**Windows (PowerShell):**
```powershell
.\setup-audit-logs.ps1
```

**Linux/Mac (Bash):**
```bash
chmod +x setup-audit-logs.sh
./setup-audit-logs.sh
```

### 2. 手動安裝（如果腳本失敗）

```bash
# 複製 SQL 文件到容器
docker cp docker/add-audit-logs-table.sql fhir-postgres:/tmp/add-audit-logs-table.sql

# 執行 SQL
docker-compose exec postgres psql -U fhir_admin -d fhir_analytics -f /tmp/add-audit-logs-table.sql

# 重啟後端
docker-compose restart backend
```

---

## 使用方法

### 訪問審計日誌

1. **以管理員身份登錄**
   - 只有 `admin` 角色的用戶才能查看審計日誌
   - Engineer 和 Analyst 角色無權訪問

2. **導航到審計日誌頁面**
   - 點擊導航欄中的 `🔐 審計日誌`

3. **查看和過濾日誌**
   - 使用過濾器查找特定操作
   - 點擊「查看詳情」查看完整信息

### 統計儀表板

審計日誌頁面頂部顯示以下統計信息（最近 7 天）：

- **📊 總操作數** - 系統總操作次數
- **✅ 成功率** - 成功操作的百分比
- **👥 活躍用戶** - 活躍用戶數量
- **❌ 失敗操作** - 失敗操作數量

### 過濾選項

支持以下過濾條件：

- **用戶名** - 按用戶名模糊搜索
- **操作類型** - login, query_data, export_data, admin_operation 等
- **資源類型** - Patient, Condition, Encounter 等
- **狀態** - 成功/失敗
- **日期範圍** - 開始日期 ~ 結束日期
- **全文搜索** - 搜索描述、端點、錯誤信息

---

## 記錄內容

### 每條審計日誌包含以下信息：

| 字段 | 描述 | 示例 |
|------|------|------|
| **timestamp** | 操作時間戳 | 2025-11-03 15:30:45 |
| **user_id** | 用戶 ID | auth0\|user123 |
| **username** | 用戶名 | admin |
| **user_role** | 用戶角色 | admin, engineer, analyst |
| **action** | 操作類型 | login, query_data, export_data |
| **resource** | 資源類型 | Patient, Condition |
| **resource_id** | 資源 ID | patient-12345 |
| **method** | HTTP 方法 | GET, POST, PUT, DELETE |
| **endpoint** | API 端點 | /api/analytics/patients |
| **ip_address** | IP 地址 | 192.168.1.100 |
| **user_agent** | 瀏覽器信息 | Mozilla/5.0... |
| **status_code** | HTTP 狀態碼 | 200, 401, 500 |
| **duration_ms** | 處理時間 | 245 (毫秒) |
| **is_success** | 操作結果 | success, failure |
| **description** | 操作描述 | User 'admin' performed GET on /api/... |
| **request_params** | 請求參數 | {"query": "diabetes"} |
| **error_message** | 錯誤信息 | Unauthorized access |

---

## 自動記錄的操作類型

### 1. 認證操作
- `login` - 用戶登錄
- `logout` - 用戶登出

### 2. 數據訪問
- `query_data` - 查詢患者、診斷等數據
- `view` - 查看數據詳情

### 3. 數據修改
- `create` - 創建新資源
- `update` - 更新資源
- `delete` - 刪除資源

### 4. 敏感操作
- `export_data` - 導出數據
- `admin_operation` - 管理員操作
- `system_event` - 系統事件（ETL 作業等）

---

## 敏感數據脫敏

審計日誌系統自動脫敏以下敏感字段：

- **密碼** (password)
- **令牌** (token, authorization)
- **API 密鑰** (api_key, apikey, secret)
- **信用卡號** (credit_card)
- **社會安全號** (ssn, social_security)

脫敏後顯示為：`***REDACTED***`

### 示例

**原始請求參數：**
```json
{
  "username": "admin",
  "password": "SecurePassword123!",
  "remember_me": true
}
```

**記錄到審計日誌：**
```json
{
  "username": "admin",
  "password": "***REDACTED***",
  "remember_me": true
}
```

---

## API 端點

### 1. 獲取審計日誌列表

```http
GET /api/audit/logs
```

**查詢參數：**
- `skip` - 跳過記錄數（分頁）
- `limit` - 返回記錄數（1-500）
- `username` - 用戶名過濾
- `action` - 操作類型過濾
- `resource` - 資源類型過濾
- `is_success` - 成功/失敗過濾
- `start_date` - 開始日期 (YYYY-MM-DD)
- `end_date` - 結束日期 (YYYY-MM-DD)
- `ip_address` - IP 地址過濾
- `search` - 全文搜索

**響應示例：**
```json
{
  "total": 1250,
  "skip": 0,
  "limit": 50,
  "logs": [
    {
      "id": 12345,
      "timestamp": "2025-11-03T15:30:45Z",
      "username": "admin",
      "action": "query_data",
      "endpoint": "/api/analytics/patients",
      "status_code": 200,
      "is_success": "success"
    }
  ]
}
```

### 2. 獲取單條日誌詳情

```http
GET /api/audit/logs/{log_id}
```

### 3. 獲取統計信息

```http
GET /api/audit/stats?days=7
```

**響應包含：**
- 總操作數、失敗操作數、成功率
- 活躍用戶數
- 按操作類型統計
- 按資源類型統計
- 最活躍用戶
- 每日操作趨勢

### 4. 獲取可用過濾選項

```http
GET /api/audit/actions     # 所有操作類型
GET /api/audit/resources   # 所有資源類型
```

---

## 程式化使用

### 在代碼中記錄審計事件

```python
from app.core.audit import log_authentication, log_data_access, log_system_event
from app.core.database import SessionLocal

# 1. 記錄認證操作
db = SessionLocal()
log_authentication(
    db=db,
    username="admin",
    action="login",
    is_success="success",
    ip_address="192.168.1.100",
    user_agent="Mozilla/5.0..."
)

# 2. 記錄數據訪問
log_data_access(
    db=db,
    user_id="auth0|user123",
    username="analyst",
    user_role="analyst",
    resource="Patient",
    action="query_data",
    endpoint="/api/analytics/patients",
    method="GET",
    status_code=200,
    request_params={"diagnosis": "diabetes"},
    duration_ms=245
)

# 3. 記錄系統事件
log_system_event(
    db=db,
    action="etl_job_completed",
    description="ETL job completed successfully",
    user_id="system",
    details={"job_id": "etl-2025-11-03", "records_processed": 1000}
)

db.close()
```

---

## 性能優化

審計日誌表已優化了以下索引：

1. `idx_audit_timestamp` - 時間戳索引
2. `idx_audit_user_id` - 用戶 ID 索引
3. `idx_audit_action` - 操作類型索引
4. `idx_audit_timestamp_user` - 複合索引（時間 + 用戶）
5. `idx_audit_action_resource` - 複合索引（操作 + 資源）

### 查詢性能建議

- ✅ 使用日期範圍過濾（最重要）
- ✅ 結合用戶 ID 或操作類型過濾
- ✅ 使用分頁（limit/skip）
- ❌ 避免無過濾條件的全表掃描
- ❌ 避免過度複雜的全文搜索

---

## 維護

### 定期清理舊日誌

建議定期清理過期的審計日誌以節省空間：

```sql
-- 刪除 90 天前的日誌
DELETE FROM audit_logs 
WHERE timestamp < NOW() - INTERVAL '90 days';

-- 或者歸檔到其他表
INSERT INTO audit_logs_archive 
SELECT * FROM audit_logs 
WHERE timestamp < NOW() - INTERVAL '90 days';

DELETE FROM audit_logs 
WHERE timestamp < NOW() - INTERVAL '90 days';
```

### 監控表大小

```sql
SELECT 
    pg_size_pretty(pg_total_relation_size('audit_logs')) as total_size,
    COUNT(*) as record_count
FROM audit_logs;
```

---

## 合規性

### HIPAA 合規

審計日誌系統滿足 HIPAA 的以下要求：

- ✅ **§164.308(a)(1)(ii)(D)** - 信息系統活動審查
- ✅ **§164.308(a)(5)(ii)(C)** - 登錄監控
- ✅ **§164.312(b)** - 審計控制
- ✅ **§164.312(d)** - 人員或實體認證

### GDPR 合規

- ✅ **Article 30** - 處理活動記錄
- ✅ **Article 32** - 處理安全性
- ✅ **Article 33** - 個人數據洩露通知

---

## 故障排除

### 問題 1：審計日誌未記錄

**可能原因：**
- 審計中間件未啟用
- 數據庫連接問題

**解決方案：**
```bash
# 檢查後端日誌
docker-compose logs backend | grep -i audit

# 確認中間件已註冊
# 檢查 backend/main.py 中是否有：
# app.add_middleware(AuditMiddleware)
```

### 問題 2：頁面加載緩慢

**可能原因：**
- 審計日誌表過大
- 缺少索引

**解決方案：**
```sql
-- 檢查表大小
SELECT pg_size_pretty(pg_total_relation_size('audit_logs'));

-- 重建索引
REINDEX TABLE audit_logs;

-- 清理舊數據
DELETE FROM audit_logs WHERE timestamp < NOW() - INTERVAL '90 days';
```

### 問題 3：權限錯誤

**可能原因：**
- 非管理員用戶嘗試訪問

**解決方案：**
- 確認用戶角色為 `admin`
- 檢查 JWT token 中的 role 字段

---

## 最佳實踐

1. **定期審查日誌** - 每周檢查異常活動
2. **設置告警** - 對失敗操作過多的情況設置告警
3. **定期備份** - 審計日誌也需要備份
4. **訪問控制** - 嚴格限制審計日誌訪問權限
5. **日誌保留** - 根據合規要求保留足夠長的時間（通常 6-7 年）
6. **定期清理** - 歸檔舊日誌以保持性能

---

## 常見問題

**Q: 審計日誌會影響性能嗎？**  
A: 影響很小。審計日誌異步記錄，不會阻塞主請求。

**Q: 可以關閉某些端點的審計嗎？**  
A: 可以。在 `AuditMiddleware.SKIP_PATHS` 中添加路徑。

**Q: 審計日誌會記錄請求 body 嗎？**  
A: 默認不記錄。只記錄查詢參數，且敏感字段會被脫敏。

**Q: 可以導出審計日誌嗎？**  
A: 目前未實現，但可以直接查詢數據庫：
```bash
docker-compose exec postgres psql -U fhir_admin -d fhir_analytics \
  -c "COPY (SELECT * FROM audit_logs) TO STDOUT WITH CSV HEADER" > audit_logs.csv
```

---

## 技術架構

### 組件

1. **數據模型** - `backend/app/models/audit_log.py`
2. **核心功能** - `backend/app/core/audit.py`
3. **中間件** - `backend/app/middleware/audit_middleware.py`
4. **API 端點** - `backend/app/api/routes/audit.py`
5. **前端組件** - `frontend/src/components/AuditLogs/`

### 數據流

```
API 請求 
  → AuditMiddleware 攔截
  → 提取請求信息（用戶、端點、參數等）
  → 執行實際請求
  → 記錄響應信息（狀態碼、處理時間）
  → 異步寫入 audit_logs 表
  → 返回響應給客戶端
```

---

## 更新日誌

### v1.0.0 (2025-11-03)
- ✨ 初始發布
- ✅ 自動記錄所有 API 請求
- ✅ 敏感數據脫敏
- ✅ 可視化儀表板
- ✅ 多維度過濾和搜索
- ✅ 統計分析功能

---

## 支持

如有問題或建議，請聯繫系統管理員或查看：
- 📖 [FastAPI 文檔](https://fastapi.tiangolo.com/)
- 📖 [SQLAlchemy 文檔](https://www.sqlalchemy.org/)
- 📖 [FHIR Analytics 文檔](./README.md)

---

**🔐 保護您的醫療數據，從審計開始！**

