# FHIR Analysis Platform (醫療公衛 FHIR 分析平台)

一個完整的 FHIR 數據分析平台，支援 SMART on FHIR 整合、BULK DATA ETL、數據視覺化和分析功能。

## 專案架構

本專案採用模組化設計，各模組獨立管理：

```
BeckAPP/
├── frontend/                 # 前端應用 (React + SMART on FHIR)
├── backend/                  # 後端 API (FastAPI)
├── etl-service/             # FHIR BULK DATA ETL 服務
├── analytics-service/       # 數據分析服務
├── shared/                  # 共用配置和工具
└── docker/                  # Docker 容器配置
```

## 功能特點

### 前端功能
- ✅ 使用者登入 (Standalone Launch)
- ✅ EHR SMART Launch 整合
- ✅ 年度診斷發生人次分析（流感、心肌梗塞、肺腺癌等）
- ✅ FHIR SCOPE 支援：patient, condition, encounter, observation
- ✅ 互動式儀錶板
- ✅ 數據視覺化（可配置 X/Y 軸變數）
- ✅ 資料匯出功能

### 後端功能
- ✅ FHIR 伺服器 BULK DATA API 整合
- ✅ FHIR BULK DATA 解析和轉換
- ✅ PostgreSQL 數據載入
- ✅ 數據分析 API
- ✅ Valuesets 定義管理
- ✅ RESTful API 端點
- ✅ JWT 認證和授權
- ✅ HIPAA 合規性考量

## 快速開始

### 前置需求
- Node.js 18+
- Python 3.11+
- PostgreSQL 15+
- Docker & Docker Compose

### 安裝步驟

1. **克隆專案**
```bash
git clone <repository-url>
cd BeckAPP
```

2. **使用 Docker Compose 啟動所有服務**
```bash
docker-compose up -d
```

3. **或分別啟動各服務**

```bash
# 前端
cd frontend
npm install
npm start

# 後端
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# ETL 服務
cd etl-service
pip install -r requirements.txt
python main.py

# 分析服務
cd analytics-service
pip install -r requirements.txt
python main.py
```

## 服務端口

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- ETL Service: http://localhost:8001
- Analytics Service: http://localhost:8002
- PostgreSQL: localhost:5432

## 環境配置

每個模組都有自己的 `.env` 配置文件，請參考各模組的 `.env.example` 文件。

## 文檔

- [前端文檔](./frontend/README.md)
- [後端文檔](./backend/README.md)
- [ETL 服務文檔](./etl-service/README.md)
- [分析服務文檔](./analytics-service/README.md)

## 安全性與合規性

- JWT Token 認證
- OAuth 2.0 / SMART on FHIR
- HTTPS/TLS 加密
- 資料加密儲存
- 審計日誌
- HIPAA 合規性設計

## 授權

MIT License

## 貢獻

歡迎提交 Pull Request 和 Issue。

