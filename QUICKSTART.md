# Quick Start Guide

快速開始使用 FHIR Analytics Platform。

## 🚀 5分鐘快速啟動

### 1. 確認系統需求

```bash
# 檢查 Docker
docker --version
docker-compose --version

# 檢查 Node.js (可選，用於開發)
node --version

# 檢查 Python (可選，用於開發)
python --version
```

### 2. 下載專案

```bash
git clone <repository-url>
cd BeckAPP
```

### 3. 使用 Docker Compose 啟動

```bash
# 啟動所有服務
docker-compose up -d

# 查看服務狀態
docker-compose ps
```

等待約 30-60 秒讓所有服務啟動完成。

### 4. 訪問應用

開啟瀏覽器訪問：

- **前端應用**: http://localhost:3000
- **API 文檔**: http://localhost:8000/docs
- **ETL 服務**: http://localhost:8001/docs
- **分析服務**: http://localhost:8002/docs

### 5. 登入系統

使用預設管理員帳號：

```
使用者名稱: admin
密碼: admin123
```

**⚠️ 重要：請立即更改預設密碼！**

## 📋 功能導覽

### 儀錶板 (Dashboard)

登入後您會看到：

1. **總覽統計**
   - 總病患數
   - 總診斷數
   - 總就診次數
   - 總觀察記錄

2. **趨勢圖表**
   - 診斷趨勢分析
   - 前五大診斷

3. **最近活動**
   - ETL 任務狀態
   - 資料匯出記錄

### 診斷分析

1. 點擊左側選單 **診斷分析**
2. 選擇診斷類型（流感、心肌梗塞、肺腺癌等）
3. 選擇時間範圍（月度、季度、年度）
4. 查看詳細分析結果

### 數據視覺化

1. 點擊 **數據視覺化**
2. 選擇圖表類型（柱狀圖、折線圖、散點圖、圓餅圖）
3. 配置 X 軸和 Y 軸變數
4. 生成自訂圖表
5. 下載圖表圖片

### 資料匯出

1. 點擊 **資料匯出**
2. 選擇資料類型（病患、診斷、就診、觀察）
3. 選擇格式（CSV、JSON、Excel、Parquet）
4. 設定日期範圍和欄位
5. 點擊 **開始匯出**

### 後端管理 (工程師)

使用 `engineer` 帳號登入：

```
使用者名稱: engineer
密碼: engineer123
```

功能包括：

1. **BULK DATA API**
   - 配置 FHIR 伺服器
   - 啟動資料提取

2. **ETL 任務**
   - 監控處理狀態
   - 查看日誌

3. **Valuesets 管理**
   - 新增/編輯代碼集

## 🔧 常見操作

### 匯入範例資料

如果您需要測試資料：

```bash
# 啟動 ETL 任務（需要工程師權限）
# 在後端管理 > BULK DATA API 中配置並啟動
```

### 查看日誌

```bash
# 所有服務日誌
docker-compose logs -f

# 特定服務
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f etl-service
docker-compose logs -f analytics-service
```

### 重啟服務

```bash
# 重啟所有服務
docker-compose restart

# 重啟特定服務
docker-compose restart backend
```

### 停止服務

```bash
# 停止所有服務
docker-compose down

# 停止並刪除資料（慎用！）
docker-compose down -v
```

## 📊 使用範例

### 範例 1: 分析年度流感發生人次

1. 登入系統
2. 進入 **診斷分析**
3. 選擇 **流感 (Influenza)**
4. 選擇 **年度** 時間範圍
5. 點擊 **更新分析**
6. 查看：
   - 年度趨勢圖表
   - 總人次和增長率
   - 詳細數據表格

### 範例 2: 匯出診斷資料

1. 進入 **資料匯出**
2. 選擇資料類型：**診斷資料 (Conditions)**
3. 選擇格式：**CSV**
4. 設定日期：2023-01-01 到 2023-12-31
5. 勾選包含欄位
6. 點擊 **開始匯出**
7. 下載生成的 CSV 檔案

### 範例 3: 建立自訂視覺化

1. 進入 **數據視覺化**
2. 選擇圖表類型：**柱狀圖**
3. X 軸：**年齡組**
4. Y 軸：**人次**
5. 點擊 **生成圖表**
6. 查看結果
7. 點擊 **下載圖表** 儲存圖片

## 🔒 安全提醒

### 必須立即執行

1. **更改預設密碼**
   ```
   admin: admin123 → 強密碼
   engineer: engineer123 → 強密碼
   ```

2. **更新 JWT Secret**
   ```bash
   # 生成新的密鑰
   openssl rand -hex 32
   
   # 更新 backend/.env
   JWT_SECRET=<新生成的密鑰>
   ```

3. **配置 CORS**
   ```bash
   # backend/.env
   ALLOWED_ORIGINS=https://your-domain.com
   ```

## 🆘 疑難排解

### 服務無法啟動

```bash
# 檢查端口是否被佔用
netstat -an | findstr "3000 8000 8001 8002 5432"

# 停止衝突的服務或更改端口
```

### 資料庫連線錯誤

```bash
# 檢查 PostgreSQL 狀態
docker-compose ps postgres

# 重啟資料庫
docker-compose restart postgres

# 查看日誌
docker-compose logs postgres
```

### 前端無法連接後端

1. 檢查 `frontend/.env` 中的 API URL
2. 確認後端服務正在運行
3. 檢查 CORS 設定

### 權限不足

確保您使用的帳號有足夠權限：

- **一般功能**: user 角色即可
- **後端管理**: 需要 admin 或 engineer 角色

## 📚 下一步

- 閱讀 [完整文檔](README.md)
- 查看 [API 文檔](API_DOCUMENTATION.md)
- 了解 [部署指南](DEPLOYMENT.md)
- 研究 [安全政策](SECURITY.md)

## 💬 獲得幫助

- GitHub Issues: <repository-url>/issues
- Email: support@fhir-analytics.com
- 文檔: https://docs.fhir-analytics.com

---

祝您使用愉快！🎉

