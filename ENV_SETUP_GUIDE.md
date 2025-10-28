# 環境變量設置指南

## 🔐 安全設置步驟

### 第 1 步：生成安全密鑰

```bash
# 生成 JWT Secret (64 字符)
openssl rand -hex 32

# 生成數據庫密碼 (建議至少 16 字符)
openssl rand -base64 24

# 生成 Redis 密碼
openssl rand -base64 24
```

### 第 2 步：創建根目錄 .env 文件

在項目根目錄創建 `.env` 文件：

```bash
# .env
# ============================================
# Database Configuration
# ============================================
POSTGRES_DB=fhir_analytics
POSTGRES_USER=fhir_user
POSTGRES_PASSWORD=<從上面生成的密碼>
DATABASE_URL=postgresql://fhir_user:<密碼>@postgres:5432/fhir_analytics

# ============================================
# Redis Configuration
# ============================================
REDIS_URL=redis://:redis_password@redis:6379/0
REDIS_PASSWORD=<從上面生成的 Redis 密碼>

# ============================================
# Backend Security
# ============================================
JWT_SECRET=<從上面生成的 64 字符 hex>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# ============================================
# Admin Credentials (首次設置)
# ============================================
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<強密碼，至少 12 字符，包含大小寫、數字、特殊字符>
ADMIN_EMAIL=admin@fhir-analytics.local

ENGINEER_USERNAME=engineer
ENGINEER_PASSWORD=<強密碼>
ENGINEER_EMAIL=engineer@fhir-analytics.local

# ============================================
# CORS Configuration
# ============================================
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com

# ============================================
# FHIR Server
# ============================================
FHIR_SERVER_URL=https://hapi.fhir.org/baseR4

# ============================================
# Frontend
# ============================================
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ANALYTICS_URL=http://localhost:8002
REACT_APP_FHIR_CLIENT_ID=your-client-id

# ============================================
# Environment
# ============================================
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 第 3 步：創建服務專屬 .env 文件

#### backend/.env
```bash
DATABASE_URL=${DATABASE_URL}
REDIS_URL=${REDIS_URL}
JWT_SECRET=${JWT_SECRET}
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30
ADMIN_USERNAME=${ADMIN_USERNAME}
ADMIN_PASSWORD=${ADMIN_PASSWORD}
ADMIN_EMAIL=${ADMIN_EMAIL}
ENGINEER_USERNAME=${ENGINEER_USERNAME}
ENGINEER_PASSWORD=${ENGINEER_PASSWORD}
ENGINEER_EMAIL=${ENGINEER_EMAIL}
ALLOWED_ORIGINS=${ALLOWED_ORIGINS}
FHIR_SERVER_URL=${FHIR_SERVER_URL}
LOG_LEVEL=INFO
```

#### frontend/.env
```bash
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ANALYTICS_URL=http://localhost:8002
REACT_APP_FHIR_CLIENT_ID=your-smart-client-id
REACT_APP_ENV=development
```

#### etl-service/.env
```bash
DATABASE_URL=${DATABASE_URL}
REDIS_URL=${REDIS_URL}
FHIR_SERVER_URL=${FHIR_SERVER_URL}
RETRY_MAX_ATTEMPTS=5
RETRY_BASE_DELAY=1.0
RETRY_MAX_DELAY=60.0
LOG_LEVEL=INFO
```

#### analytics-service/.env
```bash
DATABASE_URL=${DATABASE_URL}
REDIS_URL=${REDIS_URL}
LOG_LEVEL=INFO
```

### 第 4 步：設置文件權限

```bash
# 確保 .env 文件只有所有者可讀
chmod 600 .env
chmod 600 backend/.env
chmod 600 frontend/.env
chmod 600 etl-service/.env
chmod 600 analytics-service/.env
```

### 第 5 步：驗證設置

```bash
# 檢查 .env 文件是否被 git 忽略
git status

# .env 文件不應該出現在未追蹤文件列表中
```

## 🔒 密碼複雜度要求

所有密碼必須符合以下要求：
- ✅ 至少 12 個字符
- ✅ 包含大寫字母 (A-Z)
- ✅ 包含小寫字母 (a-z)
- ✅ 包含數字 (0-9)
- ✅ 包含特殊字符 (!@#$%^&*()等)

## 🚨 重要安全提醒

1. **永遠不要提交 .env 文件到 Git**
2. **定期輪換密鑰** (建議每 90 天)
3. **使用不同的密碼** 給不同的服務
4. **生產環境使用更長的密鑰** (至少 32 字符)
5. **限制 ALLOWED_ORIGINS** 只允許信任的域名

## 📋 生產環境檢查清單

- [ ] 所有默認密碼已更改
- [ ] JWT_SECRET 使用隨機生成的 64 字符 hex
- [ ] 數據庫密碼至少 16 字符
- [ ] ALLOWED_ORIGINS 僅包含生產域名
- [ ] HTTPS 已啟用
- [ ] 防火牆規則已配置
- [ ] 備份策略已實施
- [ ] 監控和告警已設置

## 🔄 密鑰輪換流程

### 輪換 JWT Secret
```bash
# 1. 生成新的 secret
NEW_SECRET=$(openssl rand -hex 32)

# 2. 更新 .env 文件
# JWT_SECRET=$NEW_SECRET

# 3. 重啟 backend 服務
docker-compose restart backend

# 注意：這會使所有現有 token 失效，用戶需要重新登入
```

### 輪換數據庫密碼
```bash
# 1. 連接到數據庫
docker exec -it fhir-postgres psql -U postgres

# 2. 更改密碼
ALTER USER fhir_user WITH PASSWORD 'new_secure_password';

# 3. 更新 .env 文件中的 DATABASE_URL

# 4. 重啟所有服務
docker-compose restart
```

## 🛠️ 故障排除

### 問題：服務無法連接到數據庫
```bash
# 檢查環境變量是否正確加載
docker-compose config

# 檢查數據庫連接
docker exec -it fhir-postgres psql -U fhir_user -d fhir_analytics
```

### 問題：JWT token 驗證失敗
```bash
# 確認 JWT_SECRET 在所有服務中一致
docker-compose exec backend env | grep JWT_SECRET
```

## 📞 支援

如有問題，請聯繫系統管理員或查看：
- [SECURITY.md](./SECURITY.md)
- [DEPLOYMENT.md](./DEPLOYMENT.md)

