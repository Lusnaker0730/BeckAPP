# 🚀 CI/CD 自動化測試指南

## 📋 目錄

- [概述](#概述)
- [快速開始](#快速開始)
- [工作流說明](#工作流說明)
- [配置設置](#配置設置)
- [本地測試](#本地測試)
- [故障排除](#故障排除)

---

## 🎯 概述

### CI/CD 架構

本專案使用 **GitHub Actions** 實現完整的 CI/CD 管道，包括：

- ✅ 自動測試（單元測試 + 整合測試）
- ✅ 覆蓋率檢查（目標：70%+）
- ✅ 程式碼品質分析（SonarCloud）
- ✅ 安全掃描（Trivy, Bandit）
- ✅ Docker 構建測試
- ✅ 依賴更新（Dependabot）

### 工作流觸發條件

| 工作流 | Push | Pull Request | 定時 |
|--------|------|--------------|------|
| Backend Tests | ✅ main, develop | ✅ | - |
| Frontend Tests | ✅ main, develop | ✅ | - |
| Docker Build | ✅ main, develop | ✅ | - |
| Code Quality | ✅ main, develop | ✅ | 每週日 |
| Complete CI | ✅ main | ✅ | - |

---

## 🚀 快速開始

### 1. 啟用 GitHub Actions

工作流已配置完成，推送到 GitHub 即可自動觸發：

```bash
git add .github/workflows/
git commit -m "chore: add CI/CD workflows"
git push origin main
```

### 2. 配置 Secrets

在 GitHub Repository Settings > Secrets and variables > Actions 中添加：

#### 必需的 Secrets

```
# Codecov（覆蓋率報告）
CODECOV_TOKEN=your_codecov_token

# SonarCloud（程式碼品質）
SONAR_TOKEN=your_sonar_token
```

#### 可選的 Secrets

```
# Docker Hub（如需推送映像）
DOCKER_USERNAME=your_docker_username
DOCKER_PASSWORD=your_docker_password

# Slack 通知
SLACK_WEBHOOK_URL=your_slack_webhook
```

### 3. 查看執行結果

訪問：`https://github.com/YOUR_USERNAME/YOUR_REPO/actions`

---

## 📁 工作流說明

### 1. Backend Tests (`backend-tests.yml`)

**目的**：測試後端 Python 程式碼

**執行內容**：
- ✅ 安裝依賴
- ✅ 程式碼檢查（flake8, black, isort）
- ✅ 執行 pytest 測試
- ✅ 生成覆蓋率報告
- ✅ 上傳到 Codecov
- ✅ 在 PR 上評論覆蓋率

**觸發條件**：
- Push 到 main/develop 分支（backend/ 變更）
- Pull Request 到 main/develop（backend/ 變更）

**服務依賴**：
- PostgreSQL 15
- Redis 7

**執行時間**：~3-5 分鐘

**配置檔案**：
```yaml
.github/workflows/backend-tests.yml
backend/pytest.ini
backend/pyproject.toml
```

---

### 2. Frontend Tests (`frontend-tests.yml`)

**目的**：測試前端 React 程式碼

**執行內容**：
- ✅ 安裝 npm 依賴
- ✅ 執行 linting
- ✅ 執行 Jest 測試
- ✅ 生成覆蓋率報告
- ✅ 構建生產版本
- ✅ 上傳構建產物

**觸發條件**：
- Push 到 main/develop（frontend/ 變更）
- Pull Request 到 main/develop（frontend/ 變更）

**執行時間**：~2-4 分鐘

---

### 3. Docker Build (`docker-build.yml`)

**目的**：測試 Docker 映像構建

**執行內容**：
- ✅ 構建 4 個服務映像
  - backend
  - frontend
  - etl-service
  - analytics-service
- ✅ Docker Compose 整合測試
- ✅ 健康檢查所有服務
- ✅ API 端點測試

**觸發條件**：
- Push 到 main/develop
- Pull Request 到 main/develop
- 需要前端和後端測試通過

**執行時間**：~8-12 分鐘

**測試內容**：
```bash
# 健康檢查
GET http://localhost:8000/health  # Backend
GET http://localhost:8001/health  # ETL Service
GET http://localhost:8002/health  # Analytics Service
GET http://localhost:3000/        # Frontend

# API 文檔
GET http://localhost:8000/docs
```

---

### 4. Code Quality (`code-quality.yml`)

**目的**：程式碼品質和安全檢查

**執行內容**：

#### 安全掃描
- ✅ Trivy 漏洞掃描
- ✅ Bandit Python 安全檢查
- ✅ Safety 依賴檢查
- ✅ npm audit

#### 程式碼分析
- ✅ SonarCloud 品質分析
- ✅ 技術債務追蹤
- ✅ Bug 偵測
- ✅ Code smell 檢測

#### Linting
- ✅ flake8（Python）
- ✅ black（Python 格式化）
- ✅ isort（導入排序）
- ✅ mypy（類型檢查）
- ✅ pylint（程式碼分析）
- ✅ ESLint（JavaScript）

**觸發條件**：
- Push 到 main/develop
- Pull Request 到 main/develop
- 每週日自動執行

**執行時間**：~5-8 分鐘

---

### 5. Complete CI (`complete-ci.yml`)

**目的**：協調所有 CI 工作流

**執行內容**：
- ✅ 按順序執行所有工作流
- ✅ 收集所有測試結果
- ✅ 生成摘要報告
- ✅ 在 PR 上評論結果

**工作流順序**：
```
1. Backend Tests + Frontend Tests（並行）
2. Docker Build（需要 1 完成）
3. Code Quality（並行）
4. Summary（生成報告）
```

**觸發條件**：
- Push 到 main
- Pull Request 到 main

**執行時間**：~15-20 分鐘

---

## ⚙️ 配置設置

### GitHub Actions Secrets

#### 1. Codecov 設置

```bash
# 1. 訪問 https://codecov.io/
# 2. 使用 GitHub 登入
# 3. 添加 repository
# 4. 複製 token

# 添加到 GitHub Secrets
CODECOV_TOKEN=<your_token>
```

#### 2. SonarCloud 設置

```bash
# 1. 訪問 https://sonarcloud.io/
# 2. 使用 GitHub 登入
# 3. 創建新組織和專案
# 4. 複製 token

# 添加到 GitHub Secrets
SONAR_TOKEN=<your_token>

# 更新 sonar-project.properties
sonar.organization=<your_org>
sonar.projectKey=<your_project_key>
```

#### 3. Docker Hub（可選）

```bash
# 如果需要推送映像到 Docker Hub

DOCKER_USERNAME=your_username
DOCKER_PASSWORD=your_password_or_token
```

### Dependabot 設置

已配置在 `.github/dependabot.yml`

**功能**：
- 每週一自動檢查依賴更新
- 自動創建 Pull Request
- 分別追蹤：
  - Python 依賴（pip）
  - Node.js 依賴（npm）
  - Docker 基礎映像
  - GitHub Actions

**管理**：
1. 查看 PR：`https://github.com/YOUR_REPO/pulls`
2. 審查變更
3. 合併或關閉

---

## 🧪 本地測試 CI

### 使用 Act（本地執行 GitHub Actions）

#### 安裝 Act

```bash
# macOS
brew install act

# Linux
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Windows (使用 Chocolatey)
choco install act-cli
```

#### 執行工作流

```bash
# 測試 backend-tests 工作流
act -W .github/workflows/backend-tests.yml

# 測試所有 push 觸發的工作流
act push

# 測試 pull_request 工作流
act pull_request

# 使用特定的 secrets
act -s CODECOV_TOKEN=test_token
```

### 本地 Docker Compose 測試

```bash
# 完整的本地測試
./test-ci-locally.sh
```

---

## 📊 CI/CD 儀表板

### 1. GitHub Actions

查看執行歷史：
```
https://github.com/YOUR_REPO/actions
```

### 2. Codecov 儀表板

查看覆蓋率趨勢：
```
https://codecov.io/gh/YOUR_USERNAME/YOUR_REPO
```

### 3. SonarCloud 儀表板

查看程式碼品質：
```
https://sonarcloud.io/project/overview?id=YOUR_PROJECT_KEY
```

---

## 🎨 狀態徽章

在 `README.md` 中添加徽章：

```markdown
<!-- CI 狀態 -->
![Backend Tests](https://github.com/YOUR_REPO/actions/workflows/backend-tests.yml/badge.svg)
![Frontend Tests](https://github.com/YOUR_REPO/actions/workflows/frontend-tests.yml/badge.svg)
![Docker Build](https://github.com/YOUR_REPO/actions/workflows/docker-build.yml/badge.svg)

<!-- 覆蓋率 -->
[![codecov](https://codecov.io/gh/YOUR_REPO/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_REPO)

<!-- 程式碼品質 -->
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=YOUR_PROJECT&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=YOUR_PROJECT)

<!-- 依賴狀態 -->
[![Dependencies](https://img.shields.io/librariesio/github/YOUR_REPO)](https://libraries.io/github/YOUR_REPO)
```

---

## 🔧 故障排除

### 問題 1：測試失敗

**症狀**：pytest 測試失敗

**解決方案**：
```bash
# 本地執行測試
cd backend
pytest -v

# 檢查環境變數
echo $DATABASE_URL
echo $REDIS_URL

# 查看詳細日誌
pytest -vv --tb=long
```

### 問題 2：Docker 構建失敗

**症狀**：Docker 映像構建錯誤

**解決方案**：
```bash
# 本地測試構建
docker build -t test-backend ./backend

# 檢查 Dockerfile
cat backend/Dockerfile

# 清理並重新構建
docker system prune -af
docker-compose build --no-cache
```

### 問題 3：覆蓋率上傳失敗

**症狀**：Codecov 上傳錯誤

**解決方案**：
```bash
# 檢查 token 是否正確設置
# GitHub Settings > Secrets > CODECOV_TOKEN

# 本地測試覆蓋率生成
cd backend
pytest --cov=app --cov-report=xml

# 驗證 coverage.xml 存在
ls -la coverage.xml
```

### 問題 4：SonarCloud 分析失敗

**症狀**：SonarCloud 掃描錯誤

**解決方案**：
```bash
# 檢查 sonar-project.properties
cat sonar-project.properties

# 驗證專案 key 和組織
# 確保 SONAR_TOKEN 正確設置

# 查看 SonarCloud 日誌
# Actions > Code Quality > View logs
```

### 問題 5：工作流未觸發

**症狀**：Push 後沒有執行 CI

**解決方案**：
```bash
# 檢查檔案路徑過濾器
# 確保變更的檔案符合 paths 設置

# 例如：backend-tests.yml
# paths:
#   - 'backend/**'

# 強制觸發（無過濾器）
git commit --allow-empty -m "Trigger CI"
git push
```

---

## 📈 效能優化

### 1. 加速測試

```yaml
# 使用快取
- uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}

# 並行執行
pytest -n auto
```

### 2. 減少 Docker 構建時間

```yaml
# 使用構建快取
- uses: docker/build-push-action@v5
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

### 3. 條件執行

```yaml
# 只在特定變更時執行
on:
  push:
    paths:
      - 'backend/**'
      - '.github/workflows/backend-tests.yml'
```

---

## 📝 最佳實踐

### 1. Commit 訊息

遵循 Conventional Commits：

```
feat(backend): add survival analysis API
fix(frontend): resolve export button issue
test(backend): add cache unit tests
chore(ci): update GitHub Actions versions
docs(readme): update installation guide
```

### 2. Pull Request

- ✅ 描述變更內容
- ✅ 連結相關 Issue
- ✅ 等待 CI 通過再合併
- ✅ 保持 PR 小而專注

### 3. 分支策略

```
main        # 生產環境（受保護）
  ├── develop    # 開發環境
  │   ├── feature/new-feature
  │   ├── fix/bug-fix
  │   └── test/add-tests
```

### 4. 程式碼審查

- ✅ 檢查 CI 狀態
- ✅ 查看覆蓋率變化
- ✅ 審查程式碼品質報告
- ✅ 測試功能

---

## 🎯 CI/CD 檢查清單

### 推送前

- [ ] 本地測試通過：`pytest`
- [ ] 程式碼格式化：`black app && isort app`
- [ ] Linting 通過：`flake8 app`
- [ ] 覆蓋率 ≥ 70%：`pytest --cov=app`

### Pull Request

- [ ] CI 所有檢查通過
- [ ] 覆蓋率未下降
- [ ] 無新的安全漏洞
- [ ] 程式碼品質良好
- [ ] 至少一人審查

### 合併到 main

- [ ] 所有檢查通過
- [ ] PR 已被批准
- [ ] 無衝突
- [ ] 文檔已更新

---

## 📞 獲取幫助

### 資源

- [GitHub Actions 文檔](https://docs.github.com/actions)
- [Codecov 文檔](https://docs.codecov.com/)
- [SonarCloud 文檔](https://docs.sonarcloud.io/)
- [Docker 文檔](https://docs.docker.com/)

### 聯繫

- GitHub Issues：提交 bug 或功能請求
- Email：your-team@example.com
- Slack：#ci-cd-support

---

## 🎉 總結

您的專案現在擁有：

✅ **完整的 CI/CD 管道**  
✅ **自動化測試**（150+ 測試）  
✅ **覆蓋率追蹤**（目標 70%+）  
✅ **程式碼品質監控**  
✅ **安全掃描**  
✅ **自動依賴更新**  

**每次 Push 和 PR 都會自動執行完整的品質檢查！** 🚀

