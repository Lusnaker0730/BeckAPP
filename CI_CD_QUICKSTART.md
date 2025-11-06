# 🚀 CI/CD 快速開始指南

## ⚡ 5分鐘設置 CI/CD

### 1. 推送工作流配置到 GitHub

```bash
# 添加所有 CI/CD 檔案
git add .github/workflows/
git add .github/dependabot.yml
git add sonar-project.properties
git add CI_CD_GUIDE.md

# 提交
git commit -m "ci: add GitHub Actions workflows"

# 推送到 GitHub
git push origin main
```

### 2. 查看 CI/CD 執行

訪問您的 GitHub repository：

```
https://github.com/YOUR_USERNAME/YOUR_REPO/actions
```

您應該看到以下工作流開始執行：
- ✅ Backend Tests
- ✅ Frontend Tests  
- ✅ Docker Build
- ✅ Code Quality

### 3. 等待結果（約 15-20 分鐘）

CI 管道會自動執行所有檢查。

---

## 🔑 配置 Secrets（可選但推薦）

### Codecov（覆蓋率報告）

1. 訪問 https://codecov.io/
2. 使用 GitHub 登入
3. 添加您的 repository
4. 複製 token
5. 在 GitHub：Settings > Secrets > New repository secret
   - Name: `CODECOV_TOKEN`
   - Value: `<your_token>`

### SonarCloud（程式碼品質）

1. 訪問 https://sonarcloud.io/
2. 使用 GitHub 登入
3. 導入您的 repository
4. 複製 token
5. 在 GitHub：Settings > Secrets > New repository secret
   - Name: `SONAR_TOKEN`
   - Value: `<your_token>`
6. 更新 `sonar-project.properties`：
   ```properties
   sonar.organization=your-org
   sonar.projectKey=your-project-key
   ```

---

## 🧪 本地測試（Push 之前）

### 快速測試

```bash
# 後端測試
cd backend
pytest --cov=app --cov-report=term-missing

# 前端測試
cd frontend
npm test -- --coverage --watchAll=false
```

### 完整 CI 模擬

```bash
# Linux / Mac
chmod +x test-ci-locally.sh
./test-ci-locally.sh

# Windows
.\test-ci-locally.ps1
```

---

## 📊 查看結果

### CI 狀態

```
https://github.com/YOUR_REPO/actions
```

### 覆蓋率報告

```
https://codecov.io/gh/YOUR_USERNAME/YOUR_REPO
```

### 程式碼品質

```
https://sonarcloud.io/project/overview?id=YOUR_PROJECT_KEY
```

---

## 🎨 添加狀態徽章

在 `README.md` 頂部添加：

```markdown
![CI](https://github.com/YOUR_REPO/actions/workflows/complete-ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/YOUR_REPO/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_REPO)
```

---

## ✅ 檢查清單

- [ ] 工作流檔案已推送到 GitHub
- [ ] CI 在 Actions 頁面可見
- [ ] 所有檢查執行並通過
- [ ] Codecov token 已配置（可選）
- [ ] SonarCloud token 已配置（可選）
- [ ] 狀態徽章已添加到 README

---

## 🎉 完成！

您的專案現在擁有：

✅ **自動化測試**：每次 push 和 PR  
✅ **覆蓋率追蹤**：70%+ 目標  
✅ **程式碼品質**：自動分析  
✅ **安全掃描**：漏洞檢測  
✅ **Docker 測試**：容器構建驗證  
✅ **依賴更新**：Dependabot 自動 PR  

**每次 push 都會自動執行完整的品質檢查！** 🚀

---

## 📚 詳細文檔

查看完整的 CI/CD 指南：[CI_CD_GUIDE.md](CI_CD_GUIDE.md)

---

## 🆘 需要幫助？

- 查看 [故障排除](CI_CD_GUIDE.md#故障排除)
- GitHub Issues：提交問題
- 文檔：CI_CD_GUIDE.md

