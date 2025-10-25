# Contributing to FHIR Analytics Platform

感謝您考慮為 FHIR Analytics Platform 做出貢獻！

## 如何貢獻

### 回報 Bug

如果您發現 bug，請建立一個 issue，包含：

1. **Bug 描述**：清楚簡潔地描述 bug
2. **重現步驟**：
   - 第一步做什麼
   - 第二步做什麼
   - ...
3. **預期行為**：應該發生什麼
4. **實際行為**：實際發生什麼
5. **環境資訊**：
   - 作業系統
   - 瀏覽器版本
   - Node.js/Python 版本
6. **截圖**：如果適用

### 建議新功能

提交功能請求時，請包含：

1. **功能描述**：詳細描述建議的功能
2. **使用場景**：為什麼需要這個功能
3. **替代方案**：考慮過的其他解決方案
4. **附加資訊**：任何其他相關資訊

### Pull Request 流程

1. **Fork 專案**
   ```bash
   git clone https://github.com/your-username/BeckAPP.git
   cd BeckAPP
   ```

2. **建立分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

3. **進行修改**
   - 遵循程式碼風格指南
   - 撰寫清晰的 commit 訊息
   - 添加必要的測試
   - 更新文檔

4. **提交變更**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   # 或
   git commit -m "fix: resolve issue #123"
   ```

5. **推送到 GitHub**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **建立 Pull Request**
   - 提供清楚的標題和描述
   - 關聯相關的 issue
   - 確保所有測試通過

## 開發規範

### Commit 訊息格式

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type:**
- `feat`: 新功能
- `fix`: Bug 修復
- `docs`: 文檔更新
- `style`: 程式碼格式（不影響功能）
- `refactor`: 重構
- `test`: 測試相關
- `chore`: 建置/工具相關

**範例:**
```
feat(frontend): add diagnosis filter component

Add a new component to filter diagnoses by ICD-10 code.
Includes dropdown selection and search functionality.

Closes #123
```

### 程式碼風格

#### Python (Backend)

遵循 [PEP 8](https://pep8.org/):

```python
# Good
def calculate_age(birth_date: date) -> int:
    """Calculate age from birth date."""
    today = date.today()
    return today.year - birth_date.year

# Bad
def calc_age(bd):
    return date.today().year - bd.year
```

使用 type hints：
```python
from typing import List, Optional

def get_patients(limit: int = 10) -> List[Patient]:
    """Fetch patients from database."""
    pass
```

#### JavaScript/React (Frontend)

使用 ES6+ 語法：

```javascript
// Good
const DiagnosisCard = ({ diagnosis, count }) => {
  return (
    <div className="card">
      <h3>{diagnosis}</h3>
      <p>{count} cases</p>
    </div>
  );
};

// Bad
function DiagnosisCard(props) {
  return (
    <div class="card">
      <h3>{props.diagnosis}</h3>
      <p>{props.count} cases</p>
    </div>
  );
}
```

### 測試

#### Backend 測試

```python
# test_analytics.py
import pytest
from app.api.routes import analytics

def test_get_stats(client):
    response = client.get("/api/analytics/stats")
    assert response.status_code == 200
    assert "totalPatients" in response.json()
```

執行測試：
```bash
cd backend
pytest
```

#### Frontend 測試

```javascript
// DiagnosisCard.test.js
import { render, screen } from '@testing-library/react';
import DiagnosisCard from './DiagnosisCard';

test('renders diagnosis card', () => {
  render(<DiagnosisCard diagnosis="Influenza" count={150} />);
  const diagnosisElement = screen.getByText(/Influenza/i);
  expect(diagnosisElement).toBeInTheDocument();
});
```

執行測試：
```bash
cd frontend
npm test
```

### 文檔

更新相關文檔：

- `README.md`: 主要文檔
- `API_DOCUMENTATION.md`: API 變更
- 程式碼註釋：複雜邏輯
- Docstrings: Python 函數
- JSDoc: JavaScript 函數

## 專案結構

```
BeckAPP/
├── frontend/           # React 前端
├── backend/           # FastAPI 後端
├── etl-service/       # ETL 服務
├── analytics-service/ # 分析服務
├── shared/           # 共用工具
├── docker/           # Docker 配置
└── docs/            # 額外文檔
```

## 開發環境設定

### 前置需求

- Node.js 18+
- Python 3.11+
- PostgreSQL 15+
- Docker & Docker Compose

### 設定步驟

1. **複製專案**
   ```bash
   git clone <repository-url>
   cd BeckAPP
   ```

2. **安裝依賴**
   ```bash
   # Frontend
   cd frontend
   npm install

   # Backend
   cd ../backend
   pip install -r requirements.txt

   # ETL Service
   cd ../etl-service
   pip install -r requirements.txt

   # Analytics Service
   cd ../analytics-service
   pip install -r requirements.txt
   ```

3. **設定環境變數**
   ```bash
   cp frontend/.env.example frontend/.env
   cp backend/.env.example backend/.env
   ```

4. **啟動資料庫**
   ```bash
   docker-compose up -d postgres
   ```

5. **執行服務**
   ```bash
   # 在不同終端視窗中
   cd frontend && npm start
   cd backend && uvicorn main:app --reload
   cd etl-service && uvicorn main:app --port 8001 --reload
   cd analytics-service && uvicorn main:app --port 8002 --reload
   ```

## 審查流程

所有 Pull Request 都會經過：

1. **自動化檢查**
   - 程式碼風格檢查
   - 單元測試
   - 建置測試

2. **程式碼審查**
   - 至少一位維護者審查
   - 解決所有評論
   - 獲得批准

3. **合併**
   - Squash and merge
   - 刪除分支

## 行為準則

### 我們的承諾

為了營造開放和歡迎的環境，我們承諾：

- 使用歡迎和包容的語言
- 尊重不同的觀點和經驗
- 優雅地接受建設性批評
- 專注於對社群最有利的事情

### 不可接受的行為

- 使用性化語言或圖像
- 人身攻擊
- 騷擾（公開或私下）
- 發布他人私人資訊

## 聯絡方式

- GitHub Issues: <repository-url>/issues
- Email: dev@fhir-analytics.com
- 討論區: <repository-url>/discussions

## 授權

貢獻的程式碼將採用 MIT 授權。

---

再次感謝您的貢獻！🎉

