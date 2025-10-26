# 🔒 安全設置指南

本指南將幫助您正確配置 FHIR Analytics Platform 的安全設置。

---

## 📋 快速檢查清單

在部署到生產環境之前，請確保完成以下所有項目：

- [ ] 生成並設置強 JWT Secret
- [ ] 更改所有默認密碼
- [ ] 配置正確的 CORS 來源
- [ ] 設置環境變量為 `production`
- [ ] 啟用 HTTPS/TLS
- [ ] 配置防火牆規則
- [ ] 設置資料庫備份
- [ ] 配置日誌監控

---

## 🔐 1. JWT Secret 配置

### 什麼是 JWT Secret？

JWT Secret 是用於加密和驗證 JSON Web Token 的密鑰。如果這個密鑰被洩露，攻擊者可以：
- 偽造任何用戶的登錄令牌
- 繞過身份驗證訪問所有數據
- 提升權限到管理員級別

### 生成強 JWT Secret

#### 方法 1：使用 OpenSSL（推薦）

```bash
# 生成 64 字符的隨機密鑰
openssl rand -hex 32
```

輸出示例：
```
a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456
```

#### 方法 2：使用 Python

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

#### 方法 3：線上工具

訪問：https://www.grc.com/passwords.htm（僅在信任的網絡環境使用）

### 設置 JWT Secret

#### 開發環境

創建 `backend/.env` 文件：

```bash
cd backend
cp .env.example .env
```

編輯 `.env` 文件：

```ini
# 使用您生成的密鑰替換
JWT_SECRET=a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456
ENVIRONMENT=development
```

#### 生產環境

**永遠不要**將 `.env` 文件提交到版本控制！

使用環境變量或密鑰管理服務：

```bash
# 直接設置環境變量
export JWT_SECRET="your-generated-secret-here"
export ENVIRONMENT="production"

# 或在 Docker Compose 中設置
```

```yaml
# docker-compose.prod.yml
services:
  backend:
    environment:
      - JWT_SECRET=${JWT_SECRET}  # 從主機環境讀取
      - ENVIRONMENT=production
```

### JWT Secret 驗證機制

系統會自動驗證 JWT Secret 的強度：

#### 開發環境 (ENVIRONMENT=development)
- ⚠️ 如果未設置，自動生成臨時密鑰並警告
- ⚠️ 如果長度 < 32 字符，顯示警告
- ⚠️ 如果使用常見弱密碼，顯示警告

#### 生產環境 (ENVIRONMENT=production)
- ❌ 如果未設置，**拒絕啟動**
- ❌ 如果長度 < 32 字符，**拒絕啟動**
- ❌ 如果使用常見弱密碼，**拒絕啟動**

### 測試配置

啟動後端服務：

```bash
cd backend
uvicorn main:app --reload
```

**正確配置的輸出：**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**配置錯誤的輸出：**
```
❌ CRITICAL SECURITY ERROR: JWT_SECRET environment variable must be set in production!
Generate a strong secret with: openssl rand -hex 32
```

---

## 🔑 2. 更改默認密碼

### 應用用戶密碼

系統默認創建兩個用戶：

| 用戶名 | 默認密碼 | 權限 | 風險等級 |
|--------|----------|------|----------|
| admin | admin123 | 完整管理權限 | 🔴 極高 |
| engineer | engineer123 | 後端管理、ETL | 🔴 極高 |

### 更改方法

#### 方法 1：通過 API（推薦）

```bash
# 首先登錄獲取 token
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.access_token')

# 更改密碼（實現此 API 端點）
curl -X PUT http://localhost:8000/api/auth/change-password \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"old_password":"admin123","new_password":"YourStrongPassword123!@#"}'
```

#### 方法 2：通過數據庫

```bash
# 生成新密碼的哈希值
python << 'EOF'
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
password = "YourStrongPassword123!@#"  # 替換為您的強密碼
hashed = pwd_context.hash(password)
print(f"UPDATE users SET hashed_password = '{hashed}' WHERE username = 'admin';")
EOF

# 複製輸出的 SQL 並執行
psql -U fhir_user -d fhir_analytics -c "你生成的SQL語句"
```

### 密碼強度要求

強密碼應該：
- ✅ 至少 12 個字符
- ✅ 包含大寫字母
- ✅ 包含小寫字母
- ✅ 包含數字
- ✅ 包含特殊字符
- ✅ 不包含用戶名
- ✅ 不是常見密碼

**強密碼示例：**
```
MyFh1r@Analyt1cs!2024
SecureP@ssw0rd#Analytics
FHIR_D@t@_S3cur3!ty
```

### 數據庫密碼

更改 PostgreSQL 密碼：

```bash
# 停止服務
docker-compose down

# 連接到數據庫
docker-compose up -d postgres
docker exec -it fhir-postgres psql -U postgres

# 在 psql 中執行
ALTER USER fhir_user WITH PASSWORD 'YourNewStrongPassword123!';
\q

# 更新所有服務的 DATABASE_URL
# 編輯 docker-compose.yml 或使用環境變量
```

---

## 🌐 3. CORS 配置

### 當前修復

系統已經修復了 CORS 配置：

**修復前（不安全）：**
```python
allow_origins=["*"]  # 允許任何來源 ❌
```

**修復後（安全）：**
```python
allow_origins=settings.ALLOWED_ORIGINS  # 僅允許白名單 ✅
```

### 配置 CORS 白名單

#### 開發環境

```python
# backend/app/core/config.py
ALLOWED_ORIGINS: List[str] = [
    "http://localhost:3000",      # 前端開發服務器
    "http://localhost:3001",
    "http://127.0.0.1:3000",
]
```

#### 生產環境

使用環境變量：

```bash
# .env
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

或在代碼中：

```python
ALLOWED_ORIGINS: List[str] = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
    "https://app.yourdomain.com",
]
```

### CORS 安全最佳實踐

1. **永遠不要使用 `["*"]`** 在生產環境
2. **僅列出您控制的域名**
3. **使用 HTTPS** (不要列出 http:// URL)
4. **避免通配符** 子域名（如 `*.example.com`）
5. **定期審查** 白名單

---

## 🛡️ 4. 環境配置

### ENVIRONMENT 變量的重要性

```python
ENVIRONMENT = "development"  # 寬鬆的安全檢查
ENVIRONMENT = "production"   # 嚴格的安全檢查
```

### 各環境的行為差異

| 功能 | Development | Production |
|------|-------------|------------|
| JWT Secret 驗證 | 警告 | 拒絕啟動 |
| 調試信息 | 顯示詳細錯誤 | 隱藏敏感信息 |
| CORS | 較寬鬆 | 嚴格白名單 |
| 日誌級別 | DEBUG | INFO/WARNING |
| 錯誤追踪 | 完整堆棧 | 簡化消息 |

---

## 🚀 5. 部署前檢查

### 運行安全檢查腳本

```bash
# 創建安全檢查腳本
cat > security_check.sh << 'EOF'
#!/bin/bash

echo "🔍 FHIR Analytics Security Check"
echo "================================"

# Check 1: JWT Secret
if [ -z "$JWT_SECRET" ]; then
    echo "❌ JWT_SECRET not set"
    exit 1
elif [ ${#JWT_SECRET} -lt 32 ]; then
    echo "❌ JWT_SECRET too short (${#JWT_SECRET} chars, need 32+)"
    exit 1
else
    echo "✅ JWT_SECRET configured"
fi

# Check 2: Environment
if [ "$ENVIRONMENT" != "production" ]; then
    echo "⚠️  ENVIRONMENT not set to 'production'"
else
    echo "✅ ENVIRONMENT set to production"
fi

# Check 3: Database password
if [[ "$DATABASE_URL" == *"fhir_password"* ]]; then
    echo "❌ Using default database password"
    exit 1
else
    echo "✅ Database password changed"
fi

# Check 4: HTTPS
if [[ "$ALLOWED_ORIGINS" == *"http://"* ]] && [ "$ENVIRONMENT" == "production" ]; then
    echo "⚠️  WARNING: CORS allows non-HTTPS origins"
else
    echo "✅ HTTPS configured"
fi

echo ""
echo "Security check complete!"
EOF

chmod +x security_check.sh
./security_check.sh
```

---

## 📚 6. 其他安全建議

### 啟用速率限制

參考主分析報告中的速率限制實現。

### 設置防火牆

```bash
# 僅允許必要的端口
# 80 (HTTP), 443 (HTTPS)
# 不要暴露: 5432 (PostgreSQL), 6379 (Redis), 8000-8002 (內部 API)
```

### 使用反向代理

使用 Nginx 或 Traefik 作為反向代理：
- 處理 SSL/TLS
- 速率限制
- DDoS 防護
- 隱藏內部服務

### 定期更新依賴

```bash
# 檢查過時的包
pip list --outdated

# 更新依賴
pip install --upgrade -r requirements.txt
```

### 啟用審計日誌

記錄所有：
- 登錄嘗試
- 數據訪問
- 配置更改
- 權限變更

---

## 🆘 常見問題

### Q: 忘記了 admin 密碼怎麼辦？

A: 參考上面的「方法 2：通過數據庫」重置密碼。

### Q: 如何知道我的 JWT Secret 是否安全？

A: 應該滿足：
- 64+ 字符長度
- 完全隨機生成
- 從未出現在代碼或日誌中
- 僅存儲在環境變量或密鑰管理服務中

### Q: 可以使用同一個 JWT Secret 在多個環境嗎？

A: **絕對不行！** 每個環境（開發、測試、生產）都應該使用不同的密鑰。

### Q: 多久應該輪換 JWT Secret？

A: 建議：
- 定期：每 90 天
- 在員工離職時
- 在懷疑洩露時
- 在安全事件後

---

## 📞 獲得幫助

如果您發現安全問題：

1. **不要**公開報告
2. 發送郵件到：security@fhir-analytics.com
3. 提供詳細描述和重現步驟

---

**最後更新**: 2025-01-15

**記住**：安全不是一次性的設置，而是持續的過程！ 🔒

