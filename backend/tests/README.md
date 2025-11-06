# FHIR Analytics Platform - 測試指南

## 📋 測試覆蓋範圍

### 已完成的測試模組

#### 單元測試 (Unit Tests)
- ✅ `test_password_validator.py` - 密碼驗證規則
- ✅ `test_security.py` - 安全功能
- ✅ `test_audit_middleware.py` - 審計中介軟體
- ✅ `test_cache.py` - Redis 快取功能

#### 整合測試 (Integration Tests)
- ✅ `test_auth_api.py` - 認證 API
- ✅ `test_analytics_api.py` - 分析 API
- ✅ `test_survival_api.py` - 存活分析 API
- ✅ `test_export_api.py` - 資料匯出 API
- ✅ `test_cohort_api.py` - 群組分析 API

### 測試統計

```
總測試數：      150+ 個測試
單元測試：      60+ 個測試
整合測試：      90+ 個測試
目標覆蓋率：    70%+
```

---

## 🚀 快速開始

### 1. 安裝測試依賴

```bash
cd backend
pip install -r requirements.txt
```

測試依賴包含在 `requirements.txt` 中：
- pytest
- pytest-asyncio
- pytest-cov
- pytest-mock
- httpx

### 2. 執行所有測試

```bash
# 執行所有測試
pytest

# 顯示詳細輸出
pytest -v

# 顯示測試覆蓋率
pytest --cov=app --cov-report=html
```

### 3. 查看覆蓋率報告

```bash
# 生成 HTML 報告
pytest --cov=app --cov-report=html

# 開啟報告（Windows）
start htmlcov/index.html

# 開啟報告（Mac/Linux）
open htmlcov/index.html
```

---

## 📂 測試結構

```
backend/tests/
├── __init__.py
├── conftest.py              # 共用 fixtures 和配置
├── README.md                # 本文件
├── unit/                    # 單元測試
│   ├── __init__.py
│   ├── test_password_validator.py
│   ├── test_security.py
│   ├── test_audit_middleware.py
│   └── test_cache.py
└── integration/             # 整合測試
    ├── __init__.py
    ├── test_auth_api.py
    ├── test_analytics_api.py
    ├── test_survival_api.py
    ├── test_export_api.py
    └── test_cohort_api.py
```

---

## 🏃 執行測試

### 執行特定測試檔案

```bash
# 執行單一測試檔案
pytest tests/unit/test_cache.py

# 執行整合測試
pytest tests/integration/

# 執行單元測試
pytest tests/unit/
```

### 執行特定測試類別或函數

```bash
# 執行特定類別
pytest tests/unit/test_cache.py::TestCacheDecorator

# 執行特定測試
pytest tests/unit/test_cache.py::TestCacheDecorator::test_cache_hit_returns_cached_value

# 使用模糊匹配
pytest -k "cache" -v
pytest -k "export or cohort" -v
```

### 使用標記 (Markers)

```bash
# 只執行單元測試
pytest -m unit

# 只執行整合測試
pytest -m integration

# 只執行 API 測試
pytest -m api

# 只執行安全相關測試
pytest -m security

# 排除慢速測試
pytest -m "not slow"
```

### 並行執行測試（加速）

```bash
# 安裝 pytest-xdist
pip install pytest-xdist

# 使用 4 個 CPU 核心並行執行
pytest -n 4

# 自動偵測核心數
pytest -n auto
```

---

## 📊 測試覆蓋率

### 生成覆蓋率報告

```bash
# 終端機報告（顯示缺失的行）
pytest --cov=app --cov-report=term-missing

# HTML 報告（詳細互動式報告）
pytest --cov=app --cov-report=html

# XML 報告（CI/CD 整合）
pytest --cov=app --cov-report=xml

# 組合多種報告
pytest --cov=app --cov-report=html --cov-report=term-missing --cov-report=xml
```

### 覆蓋率目標

| 模組 | 目標 | 當前狀態 |
|------|------|----------|
| 認證 (auth) | 90% | ✅ 已達成 |
| 安全 (security) | 90% | ✅ 已達成 |
| 分析 (analytics) | 80% | ✅ 已達成 |
| 存活分析 (survival) | 80% | ✅ 新增 |
| 資料匯出 (export) | 80% | ✅ 新增 |
| 審計 (audit) | 85% | ✅ 新增 |
| 快取 (cache) | 75% | ✅ 新增 |
| 群組分析 (cohort) | 80% | ✅ 新增 |
| **整體** | **70%+** | **🎯 目標中** |

---

## 🧪 測試類型

### 單元測試 (Unit Tests)

**目的**：測試獨立的函數和類別

**特點**：
- 快速執行（< 100ms）
- 不依賴外部服務
- 使用 Mock 隔離依賴

**範例**：
```python
@pytest.mark.unit
def test_password_validation():
    """測試密碼驗證規則"""
    assert validate_password("ValidPass123!") == True
    assert validate_password("weak") == False
```

### 整合測試 (Integration Tests)

**目的**：測試 API 端點和服務整合

**特點**：
- 測試完整的請求-回應流程
- 使用測試資料庫
- 驗證業務邏輯

**範例**：
```python
@pytest.mark.integration
@pytest.mark.api
def test_export_patients_csv(authenticated_client):
    """測試病患資料匯出為 CSV"""
    client, token, user = authenticated_client
    
    response = client.post(
        "/api/export/patients",
        json={"format": "csv"}
    )
    
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
```

### 慢速測試 (Slow Tests)

**標記**：`@pytest.mark.slow`

**執行方式**：
```bash
# 排除慢速測試（日常開發）
pytest -m "not slow"

# 只執行慢速測試（完整測試）
pytest -m slow
```

---

## 🛠️ 常用 Fixtures

### 資料庫 Fixtures

```python
def test_with_database(test_db):
    """使用測試資料庫"""
    # test_db 是一個 SQLAlchemy Session
    from app.models.user import User
    user = User(username="test")
    test_db.add(user)
    test_db.commit()
```

### 認證 Fixtures

```python
def test_authenticated_request(authenticated_client):
    """使用已認證的客戶端"""
    client, token, user = authenticated_client
    
    response = client.get("/api/patients")
    assert response.status_code == 200
```

```python
def test_admin_request(admin_client):
    """使用管理員客戶端"""
    client, token, admin = admin_client
    
    response = client.post("/api/cohorts", json={...})
    assert response.status_code == 200
```

### Mock Redis

```python
def test_with_redis(mock_redis):
    """使用 Mock Redis"""
    with patch('app.core.cache.redis_client', mock_redis):
        # 測試快取功能
        pass
```

### 測試資料 Fixtures

```python
def test_with_patient_data(sample_patient_data):
    """使用範例病患資料"""
    assert sample_patient_data["fhir_id"] == "patient-123"
```

---

## 🔍 調試測試

### 顯示 print 輸出

```bash
# 顯示 print 語句
pytest -s

# 或
pytest --capture=no
```

### 在失敗時進入調試器

```bash
# 使用 pdb
pytest --pdb

# 在第一個失敗時停止
pytest -x --pdb
```

### 只執行失敗的測試

```bash
# 第一次執行（記錄失敗）
pytest

# 只重新執行失敗的測試
pytest --lf

# 先執行失敗的，再執行其他的
pytest --ff
```

### 詳細輸出

```bash
# 非常詳細的輸出
pytest -vv

# 顯示局部變量
pytest --showlocals

# 顯示完整的差異
pytest --tb=long
```

---

## 📝 編寫新測試

### 測試模板

```python
"""
測試模組說明
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit  # 或 @pytest.mark.integration
class TestYourFeature:
    """測試套件說明"""
    
    @pytest.fixture(autouse=True)
    def setup(self, test_db):
        """每個測試前的設置"""
        # 創建測試資料
        pass
    
    def test_feature_success(self, authenticated_client):
        """測試成功情況"""
        client, token, user = authenticated_client
        
        response = client.get("/api/your-endpoint")
        
        assert response.status_code == 200
        data = response.json()
        assert "expected_field" in data
    
    def test_feature_error(self, authenticated_client):
        """測試錯誤情況"""
        client, token, user = authenticated_client
        
        response = client.get("/api/invalid-endpoint")
        
        assert response.status_code == 404
    
    def test_feature_validation(self, authenticated_client):
        """測試輸入驗證"""
        client, token, user = authenticated_client
        
        response = client.post(
            "/api/your-endpoint",
            json={"invalid": "data"}
        )
        
        assert response.status_code == 422
```

### 測試命名規範

```python
# ✅ 好的命名
def test_user_cannot_login_with_incorrect_password():
    pass

def test_export_returns_csv_format():
    pass

def test_cache_expires_after_ttl():
    pass

# ❌ 不好的命名
def test_1():
    pass

def test_function():
    pass

def test_it_works():
    pass
```

### 使用 AAA 模式

```python
def test_feature():
    # Arrange（準備）
    user = create_test_user()
    data = {"field": "value"}
    
    # Act（執行）
    response = client.post("/api/endpoint", json=data)
    
    # Assert（斷言）
    assert response.status_code == 200
    assert response.json()["field"] == "value"
```

---

## 🎯 測試最佳實踐

### 1. 測試應該獨立

```python
# ✅ 好的做法
def test_create_user(test_db):
    user = User(username="test")
    test_db.add(user)
    test_db.commit()
    assert user.id is not None

# ❌ 不好的做法（依賴其他測試）
def test_create_user():
    # 假設其他測試已經創建了 user
    user = User.query.first()
    assert user is not None
```

### 2. 使用描述性的斷言訊息

```python
# ✅ 好的做法
assert len(users) == 5, f"Expected 5 users, got {len(users)}"

# ❌ 不好的做法
assert len(users) == 5
```

### 3. 測試邊界條件

```python
def test_age_validation():
    # 測試邊界值
    assert validate_age(0) == True    # 最小值
    assert validate_age(120) == True  # 最大值
    assert validate_age(-1) == False  # 小於最小值
    assert validate_age(121) == False # 大於最大值
```

### 4. 使用 parametrize 進行多組測試

```python
@pytest.mark.parametrize("input,expected", [
    ("ValidPass123!", True),
    ("weak", False),
    ("NoNumber!", False),
    ("nouppercas3!", False),
])
def test_password_validation(input, expected):
    assert validate_password(input) == expected
```

---

## 🔧 持續整合 (CI/CD)

### GitHub Actions 配置

測試會在每次 push 和 pull request 時自動執行。

查看 `.github/workflows/ci.yml` 了解詳情。

### 本地執行 CI 測試

```bash
# 執行完整的 CI 測試套件
pytest --cov=app --cov-report=xml --cov-report=term-missing

# 檢查覆蓋率門檻
pytest --cov=app --cov-fail-under=70
```

---

## 📈 提升覆蓋率

### 1. 找出未覆蓋的程式碼

```bash
# 顯示缺失的行號
pytest --cov=app --cov-report=term-missing

# 生成 HTML 報告查看詳情
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### 2. 優先順序

**高優先級**（90%+ 覆蓋率）：
- 認證和授權
- 安全功能
- 資料驗證
- 審計日誌

**中優先級**（80%+ 覆蓋率）：
- API 端點
- 業務邏輯
- 資料處理

**低優先級**（70%+ 覆蓋率）：
- 工具函數
- 輔助功能

### 3. 排除不需測試的程式碼

```python
# pragma: no cover
def debug_only_function():  # pragma: no cover
    """只在調試時使用的函數"""
    pass
```

---

## 🆘 常見問題

### Q: 測試執行很慢怎麼辦？

```bash
# 使用並行執行
pytest -n auto

# 排除慢速測試
pytest -m "not slow"

# 只執行特定的測試
pytest tests/unit/
```

### Q: 測試資料庫衝突

測試使用記憶體資料庫（SQLite），每個測試都會重新創建。如果遇到問題：

```bash
# 清理測試資料
rm -rf __pycache__
rm -rf .pytest_cache

# 重新執行
pytest
```

### Q: Redis 連線錯誤

測試使用 Mock Redis，不需要真實的 Redis 服務。確保：

```python
# 在測試中使用 mock_redis fixture
def test_cache(mock_redis):
    with patch('app.core.cache.redis_client', mock_redis):
        # 測試程式碼
        pass
```

### Q: 如何測試異步函數？

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected
```

---

## 📚 相關資源

- [Pytest 官方文檔](https://docs.pytest.org/)
- [FastAPI 測試指南](https://fastapi.tiangolo.com/tutorial/testing/)
- [Coverage.py 文檔](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://testingjavascript.com/)

---

## 🎉 測試完成檢查清單

- [ ] 所有測試通過
- [ ] 覆蓋率 ≥ 70%
- [ ] 無警告訊息
- [ ] 關鍵路徑覆蓋率 ≥ 90%
- [ ] 文檔已更新

```bash
# 執行完整檢查
pytest --cov=app --cov-report=term-missing --cov-fail-under=70 -v
```

---

**測試覆蓋率提升完成！** 🚀

如需協助，請參考主要的 [TESTING_GUIDE.md](../../TESTING_GUIDE.md)

