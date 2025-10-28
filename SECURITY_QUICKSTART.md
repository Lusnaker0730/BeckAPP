# 🚀 安全設置快速開始

## ⚡ 5 分鐘安全設置

### Windows 用戶

```powershell
# 運行設置腳本
.\setup-security.ps1

# 或手動設置
# 1. 生成密鑰（PowerShell）
$JWT_SECRET = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object {[char]$_})
$DB_PASSWORD = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 24 | ForEach-Object {[char]$_})

# 2. 複製並編輯 .env 文件
# 參考 ENV_SETUP_GUIDE.md
```

### Linux/Mac 用戶

```bash
# 運行設置腳本
./setup-security.sh

# 或手動設置
# 1. 生成密鑰
openssl rand -hex 32        # JWT_SECRET
openssl rand -base64 24     # POSTGRES_PASSWORD
openssl rand -base64 24     # REDIS_PASSWORD

# 2. 創建 .env 文件
# 參考 ENV_SETUP_GUIDE.md
```

---

## ✅ 必需步驟

### 1. 生成並設置環境變量

**選項 A: 使用自動化腳本（推薦）**

```bash
# Windows
.\setup-security.ps1

# Linux/Mac
./setup-security.sh
```

**選項 B: 手動設置**

查看 [ENV_SETUP_GUIDE.md](./ENV_SETUP_GUIDE.md) 獲取詳細說明。

### 2. 驗證配置

```bash
# 檢查 .env 文件存在
ls -la .env  # Linux/Mac
dir .env     # Windows

# 驗證 docker-compose 配置
docker-compose config
```

### 3. 啟動服務

```bash
docker-compose up -d
```

### 4. 驗證啟動

```bash
# 檢查所有服務運行中
docker-compose ps

# 檢查日誌沒有錯誤
docker-compose logs backend | grep -i error
docker-compose logs backend | grep -i password
```

### 5. 首次登入

1. 訪問 http://localhost:3000
2. 使用您設置的 admin 憑證登入
3. **立即更改密碼**（推薦）

---

## 🔒 密碼要求

所有密碼必須包含：
- ✅ 至少 12 個字符
- ✅ 大寫字母 (A-Z)
- ✅ 小寫字母 (a-z)
- ✅ 數字 (0-9)
- ✅ 特殊字符 (!@#$%^&*)

**示例強密碼：**
```
MySecure!Pass2024
Admin@2024Secure
Engineering#Pwd123!
```

**❌ 避免使用：**
- password、admin123、12345678
- 您的姓名、生日、公司名稱
- 重複字符（aaa、111）
- 連續字符（abc、123）

---

## 📁 重要文件說明

| 文件 | 用途 | 提交到 Git? |
|------|------|------------|
| `.env` | 主要配置文件 | ❌ 絕不 |
| `.env.example` | 配置範例 | ✅ 可以 |
| `docker-compose.yml` | Docker 配置 | ✅ 可以 |
| `.jwt_secret` | JWT 密鑰備份 | ❌ 絕不 |
| `.postgres_password` | 數據庫密碼備份 | ❌ 絕不 |
| `.redis_password` | Redis 密碼備份 | ❌ 絕不 |

---

## 🚨 安全檢查清單

首次部署前必須完成：

- [ ] 已運行 `setup-security.ps1` 或 `setup-security.sh`
- [ ] `.env` 文件已創建並包含所有必需變量
- [ ] 所有密碼符合複雜度要求
- [ ] JWT_SECRET 至少 64 字符
- [ ] 數據庫密碼不同於 Redis 密碼
- [ ] ALLOWED_ORIGINS 僅包含信任的域名
- [ ] 已驗證 `.env` 文件不在 Git 中
- [ ] 已啟動所有 Docker 服務
- [ ] 可以成功登入前端
- [ ] 已測試基本 API 功能

生產環境額外檢查：

- [ ] ENVIRONMENT=production
- [ ] 已配置 HTTPS
- [ ] 已配置防火牆
- [ ] 已設置自動備份
- [ ] 已配置監控和告警
- [ ] 已進行安全掃描

---

## 📖 完整文檔

- **快速開始（本文檔）**: `SECURITY_QUICKSTART.md` ⭐
- **環境變量詳細說明**: `ENV_SETUP_GUIDE.md`
- **完整安全指南**: `SECURITY_SETUP_COMPLETE_GUIDE.md`
- **安全政策**: `SECURITY.md`
- **部署指南**: `DEPLOYMENT.md`

---

## 🆘 常見問題

### Q: 忘記管理員密碼怎麼辦？

**方法 1: 通過數據庫重置**
```bash
# 連接到數據庫
docker exec -it fhir-postgres psql -U fhir_user -d fhir_analytics

# 查看用戶
SELECT username, email, role FROM users;

# 注意：密碼已加密，無法直接修改
# 需要使用 Python 腳本生成新的哈希密碼
```

**方法 2: 重新創建用戶**
```bash
# 停止服務
docker-compose down

# 刪除數據庫卷（警告：會刪除所有數據）
docker volume rm beckapp_postgres_data

# 更新 .env 中的 ADMIN_PASSWORD

# 重新啟動
docker-compose up -d
```

### Q: JWT Token 驗證失敗？

```bash
# 確認 JWT_SECRET 一致
docker-compose exec backend env | grep JWT_SECRET

# 檢查是否使用了弱密鑰
# 查看後端日誌中的警告
docker-compose logs backend | grep JWT
```

### Q: 無法連接到數據庫？

```bash
# 檢查數據庫是否運行
docker ps | grep postgres

# 檢查連接字符串
docker-compose exec backend env | grep DATABASE_URL

# 測試連接
docker exec -it fhir-postgres psql -U fhir_user -d fhir_analytics
```

### Q: CORS 錯誤？

確保 `.env` 中的 `ALLOWED_ORIGINS` 包含前端 URL：
```bash
# 開發環境
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# 檢查當前設置
docker-compose exec backend env | grep ALLOWED_ORIGINS
```

---

## 💡 專業提示

1. **使用密碼管理器** - 存儲生成的密碼到 1Password、LastPass 等
2. **定期備份 .env** - 加密後存儲到安全位置
3. **定期輪換密鑰** - 建議每 90 天輪換一次
4. **監控日誌** - 定期檢查異常登入嘗試
5. **啟用 2FA** - 如果系統支持，務必啟用

---

## 📞 需要幫助？

- 📖 查看完整文檔：`SECURITY_SETUP_COMPLETE_GUIDE.md`
- 🐛 報告問題：GitHub Issues
- 🔒 安全問題：security@yourdomain.com

---

**最後更新：** 2024-10-28  
**版本：** 1.0.0

---

## 🎯 下一步

安全設置完成後：

1. ✅ 測試所有功能
2. ✅ 配置數據備份
3. ✅ 設置監控和告警
4. ✅ 進行安全掃描
5. ✅ 查看 [測試覆蓋率改進計劃](./README.md)

**祝您使用愉快！** 🚀

