# 🔐 FHIR Analytics Platform - 完整安全設置指南

## 📋 目錄
1. [快速開始](#快速開始)
2. [環境變量配置](#環境變量配置)
3. [密碼安全](#密碼安全)
4. [網絡安全](#網絡安全)
5. [數據庫安全](#數據庫安全)
6. [應用安全](#應用安全)
7. [部署檢查清單](#部署檢查清單)
8. [故障排除](#故障排除)

---

## 🚀 快速開始

### 初次設置（必須完成！）

```bash
# 1. 生成安全密鑰
openssl rand -hex 32 > jwt_secret.txt
openssl rand -base64 24 > db_password.txt
openssl rand -base64 24 > redis_password.txt

# 2. 創建 .env 文件
cp ENV_SETUP_GUIDE.md .env
# 編輯 .env 文件，填入生成的密鑰

# 3. 設置文件權限
chmod 600 .env
chmod 600 jwt_secret.txt
chmod 600 db_password.txt
chmod 600 redis_password.txt

# 4. 驗證配置
docker-compose config

# 5. 啟動服務
docker-compose up -d
```

---

## 🔑 環境變量配置

### 必需的環境變量

在項目根目錄創建 `.env` 文件：

```bash
# ===========================================
# 數據庫配置（必需）
# ===========================================
POSTGRES_DB=fhir_analytics
POSTGRES_USER=fhir_user
POSTGRES_PASSWORD=<使用 openssl rand -base64 24 生成>

# 完整數據庫連接 URL
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}

# ===========================================
# Redis 配置（必需）
# ===========================================
REDIS_PASSWORD=<使用 openssl rand -base64 24 生成>
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0

# ===========================================
# JWT 安全配置（必需）
# ===========================================
# 使用以下命令生成：openssl rand -hex 32
JWT_SECRET=<64 字符的隨機 hex 字符串>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# ===========================================
# 管理員帳號（首次設置必需）
# ===========================================
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<強密碼 - 至少 12 字符>
ADMIN_EMAIL=admin@yourdomain.com

ENGINEER_USERNAME=engineer
ENGINEER_PASSWORD=<強密碼 - 至少 12 字符>
ENGINEER_EMAIL=engineer@yourdomain.com

# ===========================================
# CORS 配置（必需）
# ===========================================
# 開發環境
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# 生產環境（僅允許您的域名）
# ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# ===========================================
# FHIR 伺服器
# ===========================================
FHIR_SERVER_URL=https://hapi.fhir.org/baseR4

# ===========================================
# 前端配置
# ===========================================
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ANALYTICS_URL=http://localhost:8002
REACT_APP_FHIR_CLIENT_ID=your-smart-client-id

# ===========================================
# 環境設定
# ===========================================
ENVIRONMENT=development  # 或 production
LOG_LEVEL=INFO           # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### 生產環境額外配置

```bash
# ===========================================
# 生產環境特殊配置
# ===========================================
ENVIRONMENT=production

# 啟用 HTTPS（必需）
FORCE_HTTPS=true

# 更嚴格的 CORS
ALLOWED_ORIGINS=https://yourdomain.com

# 更長的 JWT 過期時間（可選）
JWT_EXPIRE_MINUTES=60

# 啟用審計日誌
ENABLE_AUDIT_LOG=true
AUDIT_LOG_PATH=/var/log/fhir-analytics/audit.log

# Sentry 錯誤追蹤（推薦）
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

---

## 🔐 密碼安全

### 密碼複雜度要求

所有密碼必須符合以下要求：

✅ **最低要求**
- 至少 12 個字符
- 包含大寫字母 (A-Z)
- 包含小寫字母 (a-z)
- 包含數字 (0-9)
- 包含特殊字符 (!@#$%^&*()等)

❌ **禁止**
- 常見密碼（password、123456、admin等）
- 連續字符（abc、123等）
- 重複字符（aaa、111等）
- 個人信息（姓名、生日等）

### 生成安全密碼

#### 方法 1：使用 OpenSSL
```bash
# 生成 24 字符的密碼
openssl rand -base64 24

# 生成 32 字符的 hex 密碼
openssl rand -hex 32
```

#### 方法 2：使用 Python
```python
import secrets
import string

# 生成 16 字符的強密碼
alphabet = string.ascii_letters + string.digits + string.punctuation
password = ''.join(secrets.choice(alphabet) for i in range(16))
print(password)
```

#### 方法 3：使用密碼管理器
- 推薦：1Password、LastPass、Bitwarden
- 設置長度：16+ 字符
- 啟用所有字符類型

### 密碼存儲最佳實踐

✅ **正確做法**
- 使用環境變量存儲
- 使用密鑰管理服務（HashiCorp Vault、AWS Secrets Manager）
- 定期輪換（建議 90 天）
- 不同服務使用不同密碼

❌ **錯誤做法**
- 硬編碼在代碼中
- 提交到 Git
- 明文存儲
- 共享密碼

---

## 🌐 網絡安全

### CORS 配置

#### 開發環境
```bash
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000
```

#### 生產環境
```bash
# 僅允許您的域名
ALLOWED_ORIGINS=https://app.yourdomain.com,https://yourdomain.com

# 如果使用多個子域名
ALLOWED_ORIGINS=https://app.yourdomain.com,https://admin.yourdomain.com
```

### 防火牆配置

```bash
# Ubuntu/Debian (使用 ufw)
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 允許 SSH（小心！）
sudo ufw allow 22/tcp

# 允許 HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 拒絕直接訪問數據庫和 Redis
sudo ufw deny 5432/tcp
sudo ufw deny 6379/tcp

# 啟用防火牆
sudo ufw enable
```

### HTTPS 配置

#### 使用 Nginx 反向代理

```nginx
# /etc/nginx/sites-available/fhir-analytics
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL 證書（使用 Let's Encrypt）
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 安全頭部
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload";
    add_header X-Frame-Options "DENY";
    add_header X-Content-Type-Options "nosniff";
    add_header X-XSS-Protection "1; mode=block";

    # 前端
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 後端 API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 獲取免費 SSL 證書（Let's Encrypt）

```bash
# 安裝 Certbot
sudo apt install certbot python3-certbot-nginx

# 獲取證書
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 自動續期
sudo certbot renew --dry-run
```

---

## 🗄️ 數據庫安全

### PostgreSQL 安全配置

#### 1. 創建專用用戶

```sql
-- 連接到 PostgreSQL
docker exec -it fhir-postgres psql -U postgres

-- 創建受限用戶
CREATE USER fhir_user WITH PASSWORD 'your_secure_password';

-- 創建數據庫
CREATE DATABASE fhir_analytics OWNER fhir_user;

-- 授予必要權限
GRANT CONNECT ON DATABASE fhir_analytics TO fhir_user;
\c fhir_analytics
GRANT USAGE ON SCHEMA public TO fhir_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO fhir_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO fhir_user;

-- 撤銷不必要的權限
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
```

#### 2. 啟用 SSL 連接

```bash
# 在 docker-compose.yml 中添加
postgres:
  command: >
    postgres
    -c ssl=on
    -c ssl_cert_file=/etc/ssl/certs/server.crt
    -c ssl_key_file=/etc/ssl/private/server.key
```

#### 3. 配置 pg_hba.conf

```
# /var/lib/postgresql/data/pg_hba.conf
# TYPE  DATABASE        USER            ADDRESS                 METHOD
host    all             fhir_user       0.0.0.0/0               scram-sha-256
host    all             all             127.0.0.1/32            scram-sha-256
```

### Redis 安全配置

#### 1. 啟用密碼認證（已在 docker-compose.yml 中配置）

```yaml
redis:
  command: redis-server --requirepass ${REDIS_PASSWORD}
```

#### 2. 禁用危險命令

```bash
# redis.conf
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command KEYS ""
rename-command CONFIG ""
rename-command SHUTDOWN SHUTDOWN_SECRET_KEY
```

#### 3. 限制網絡訪問

```yaml
redis:
  networks:
    - fhir-network  # 僅內部網絡
  # 不要暴露端口到主機（移除 ports 配置）
```

---

## 🛡️ 應用安全

### JWT Token 安全

#### 最佳實踐

1. **使用強密鑰**
```bash
# 至少 32 字節（64 個 hex 字符）
JWT_SECRET=$(openssl rand -hex 32)
```

2. **設置合理的過期時間**
```bash
# 開發環境：30 分鐘
JWT_EXPIRE_MINUTES=30

# 生產環境：15-60 分鐘（根據需求）
JWT_EXPIRE_MINUTES=60
```

3. **實施 Token 刷新機制**（待實現）
- Access Token：短期（15-30 分鐘）
- Refresh Token：長期（7-30 天）
- 存儲在 httpOnly cookie 中

4. **Token 撤銷機制**
- 使用 Redis 黑名單
- 記錄已撤銷的 Token

### 速率限制（待實現）

```python
# backend/app/core/rate_limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# 在路由中使用
@app.get("/api/analytics/stats")
@limiter.limit("100/minute")
async def get_stats():
    pass
```

### 輸入驗證

✅ **已實現**
- Pydantic 模型驗證
- SQLAlchemy ORM（防止 SQL 注入）
- 密碼複雜度驗證

✅ **額外建議**
- 文件上傳大小限制
- 請求體大小限制
- URL 參數驗證

---

## ✅ 部署檢查清單

### 首次部署前

- [ ] 已生成並設置所有密鑰和密碼
- [ ] 已創建並配置 `.env` 文件
- [ ] 已驗證密碼符合複雜度要求
- [ ] 已測試數據庫連接
- [ ] 已測試 Redis 連接
- [ ] 已配置 CORS 允許的域名
- [ ] 已設置防火牆規則
- [ ] 已獲取 SSL 證書
- [ ] 已配置反向代理（Nginx）
- [ ] 已啟用 HTTPS 重定向
- [ ] 已測試所有 API 端點
- [ ] 已檢查日誌沒有錯誤
- [ ] 已備份數據庫

### 生產環境特定

- [ ] `ENVIRONMENT=production` 已設置
- [ ] JWT_SECRET 長度 ≥ 64 字符
- [ ] 數據庫密碼長度 ≥ 16 字符
- [ ] ALLOWED_ORIGINS 僅包含生產域名
- [ ] 已禁用調試模式
- [ ] 已配置錯誤追蹤（Sentry）
- [ ] 已配置監控系統
- [ ] 已設置自動備份
- [ ] 已配置告警系統
- [ ] 已完成安全掃描
- [ ] 已進行滲透測試
- [ ] 已制定災難恢復計劃

### 定期維護（每月）

- [ ] 檢查依賴更新
- [ ] 運行安全掃描
- [ ] 檢查日誌異常
- [ ] 驗證備份完整性
- [ ] 檢查磁盤空間
- [ ] 檢查證書過期時間
- [ ] 審查訪問日誌

### 定期維護（每季度）

- [ ] 輪換 JWT Secret
- [ ] 輪換數據庫密碼
- [ ] 輪換 API 密鑰
- [ ] 審查用戶權限
- [ ] 更新安全政策
- [ ] 進行安全培訓

---

## 🔧 故障排除

### 問題：無法連接到數據庫

```bash
# 1. 檢查環境變量
docker-compose exec backend env | grep DATABASE_URL

# 2. 檢查 PostgreSQL 是否運行
docker ps | grep postgres

# 3. 檢查數據庫日誌
docker-compose logs postgres

# 4. 測試連接
docker exec -it fhir-postgres psql -U fhir_user -d fhir_analytics
```

### 問題：JWT Token 驗證失敗

```bash
# 1. 檢查 JWT_SECRET 是否一致
docker-compose exec backend env | grep JWT_SECRET

# 2. 檢查 token 是否過期
# 在瀏覽器控制台解碼 token
# https://jwt.io/

# 3. 檢查後端日誌
docker-compose logs backend | grep JWT
```

### 問題：CORS 錯誤

```bash
# 1. 檢查 ALLOWED_ORIGINS
docker-compose exec backend env | grep ALLOWED_ORIGINS

# 2. 確保前端 URL 在允許列表中
# 開發環境應包含：http://localhost:3000

# 3. 檢查瀏覽器控制台
# 查看具體的 CORS 錯誤消息
```

### 問題：Redis 連接失敗

```bash
# 1. 檢查 Redis 是否運行
docker ps | grep redis

# 2. 測試 Redis 連接
docker exec -it fhir-redis redis-cli -a your_redis_password ping

# 3. 檢查密碼是否正確
docker-compose exec backend env | grep REDIS
```

### 問題：密碼不符合複雜度要求

```bash
# 密碼必須：
# - 至少 12 個字符
# - 包含大寫字母
# - 包含小寫字母
# - 包含數字
# - 包含特殊字符

# 示例強密碼：
MySecure!Pass2024
Admin@2024Secure
Engineering#2024!
```

---

## 📞 支援與資源

### 文檔
- [環境設置指南](./ENV_SETUP_GUIDE.md)
- [安全政策](./SECURITY.md)
- [部署指南](./DEPLOYMENT.md)

### 工具
- [密碼生成器](https://www.lastpass.com/password-generator)
- [JWT 解碼器](https://jwt.io/)
- [SSL 測試](https://www.ssllabs.com/ssltest/)

### 安全資源
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/)

---

## 🚨 緊急情況

### 如果發現安全漏洞

1. **立即行動**
   ```bash
   # 關閉受影響的服務
   docker-compose stop backend
   
   # 備份當前數據
   ./backup.sh
   
   # 檢查訪問日誌
   docker-compose logs backend > incident.log
   ```

2. **通知相關人員**
   - 發送郵件至：security@yourdomain.com
   - 聯繫系統管理員
   - 記錄事件詳情

3. **修復漏洞**
   - 應用安全補丁
   - 更新依賴
   - 輪換密鑰

4. **驗證修復**
   - 進行安全掃描
   - 檢查日誌
   - 監控異常活動

### 密鑰泄露應對

如果密鑰或密碼被泄露：

```bash
# 1. 立即輪換所有密鑰
./scripts/rotate_secrets.sh

# 2. 撤銷所有現有 session
redis-cli -a $REDIS_PASSWORD FLUSHDB

# 3. 強制所有用戶重新登入

# 4. 審查訪問日誌
grep "unauthorized" /var/log/fhir-analytics/*.log

# 5. 通知用戶更改密碼
```

---

**最後更新：** 2024-10-28  
**版本：** 1.0.0  
**維護者：** FHIR Analytics Team

**⚠️ 重要提示：** 本指南是第一階段安全修復的一部分。請確保完成所有檢查項目後再部署到生產環境。

