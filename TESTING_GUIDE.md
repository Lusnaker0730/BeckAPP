# 🧪 测试指南

## 目录
- [概述](#概述)
- [后端测试](#后端测试)
- [前端测试](#前端测试)
- [运行测试](#运行测试)
- [编写测试](#编写测试)
- [CI/CD 集成](#cicd-集成)
- [代码覆盖率](#代码覆盖率)
- [最佳实践](#最佳实践)

---

## 概述

FHIR Analytics Platform 使用全面的测试策略，包括：
- **单元测试** - 测试独立组件和函数
- **集成测试** - 测试 API 端点和服务集成
- **端到端测试** - 测试完整的用户流程

### 测试覆盖率目标

- **后端：** 70%+ 代码覆盖率
- **前端：** 60%+ 代码覆盖率
- **关键路径：** 90%+ 覆盖率（认证、安全、数据处理）

---

## 后端测试

### 技术栈

- **pytest** - 测试框架
- **pytest-asyncio** - 异步测试支持
- **pytest-cov** - 代码覆盖率
- **pytest-mock** - Mock 支持
- **httpx** - HTTP 客户端测试
- **faker** - 测试数据生成

### 测试结构

```
backend/tests/
├── __init__.py
├── conftest.py              # 共享 fixtures
├── unit/                    # 单元测试
│   ├── test_password_validator.py
│   ├── test_security.py
│   └── ...
├── integration/             # 集成测试
│   ├── test_auth_api.py
│   ├── test_analytics_api.py
│   └── ...
└── fixtures/                # 测试数据和工具
```

### 运行后端测试

#### 所有测试
```bash
cd backend
pytest
```

#### 特定测试文件
```bash
pytest tests/unit/test_password_validator.py
```

#### 特定测试类或函数
```bash
# 测试特定类
pytest tests/unit/test_password_validator.py::TestPasswordValidation

# 测试特定函数
pytest tests/unit/test_password_validator.py::TestPasswordValidation::test_valid_strong_password
```

#### 按标记运行
```bash
# 只运行单元测试
pytest -m unit

# 只运行集成测试
pytest -m integration

# 排除慢速测试
pytest -m "not slow"

# 只运行安全相关测试
pytest -m security
```

#### 带覆盖率报告
```bash
# HTML 报告
pytest --cov=app --cov-report=html

# 终端报告
pytest --cov=app --cov-report=term-missing

# 同时生成多种报告
pytest --cov=app --cov-report=html --cov-report=term-missing
```

#### 详细输出
```bash
# 显示所有输出
pytest -v -s

# 显示局部变量
pytest --showlocals

# 显示最慢的 10 个测试
pytest --durations=10
```

### 后端测试示例

#### 单元测试示例

```python
# tests/unit/test_password_validator.py
import pytest
from app.core.password_validator import validate_password_strength

def test_valid_strong_password():
    """测试强密码验证"""
    password = "MySecure!Pass2024"
    is_valid, errors = validate_password_strength(password)
    
    assert is_valid is True
    assert len(errors) == 0

def test_password_too_short():
    """测试短密码被拒绝"""
    password = "Short1!"
    is_valid, errors = validate_password_strength(password)
    
    assert is_valid is False
    assert any("12 characters" in error for error in errors)
```

#### 集成测试示例

```python
# tests/integration/test_auth_api.py
import pytest

@pytest.mark.integration
def test_login_success(client, create_test_user, test_user_data):
    """测试成功登录"""
    # 创建用户
    create_test_user()
    
    # 登录
    response = client.post(
        "/api/auth/login",
        data={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
```

### 使用 Fixtures

```python
# conftest.py 中定义
@pytest.fixture
def test_user_data():
    """测试用户数据"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123!"
    }

# 在测试中使用
def test_something(test_user_data):
    assert test_user_data["username"] == "testuser"
```

---

## 前端测试

### 技术栈

- **Jest** - 测试框架
- **React Testing Library** - React 组件测试
- **@testing-library/user-event** - 用户交互模拟
- **@testing-library/jest-dom** - 自定义匹配器

### 测试结构

```
frontend/src/
├── App.test.js
├── setupTests.js           # 测试配置
├── components/
│   ├── Auth/
│   │   ├── Login.js
│   │   └── Login.test.js
│   ├── Dashboard/
│   │   ├── Dashboard.js
│   │   └── Dashboard.test.js
│   └── ...
```

### 运行前端测试

#### 所有测试
```bash
cd frontend
npm test
```

#### 单次运行（CI 模式）
```bash
npm test -- --watchAll=false
```

#### 带覆盖率
```bash
npm test -- --coverage --watchAll=false
```

#### 更新快照
```bash
npm test -- -u
```

#### 特定测试文件
```bash
npm test Login.test.js
```

### 前端测试示例

#### 组件渲染测试

```javascript
// Login.test.js
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Login from './Login';

test('renders login form', () => {
  render(
    <BrowserRouter>
      <Login onLogin={jest.fn()} />
    </BrowserRouter>
  );
  
  expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
});
```

#### 用户交互测试

```javascript
import { render, screen, fireEvent } from '@testing-library/react';

test('updates input when typing', () => {
  render(<Login onLogin={jest.fn()} />);
  
  const input = screen.getByLabelText(/username/i);
  fireEvent.change(input, { target: { value: 'testuser' } });
  
  expect(input.value).toBe('testuser');
});
```

#### 异步操作测试

```javascript
import { render, screen, waitFor } from '@testing-library/react';
import axios from 'axios';

jest.mock('axios');

test('loads data on mount', async () => {
  axios.get.mockResolvedValue({ data: { count: 100 } });
  
  render(<Dashboard />);
  
  await waitFor(() => {
    expect(screen.getByText('100')).toBeInTheDocument();
  });
});
```

#### Mock API 调用

```javascript
jest.mock('axios');

test('handles API error', async () => {
  axios.get.mockRejectedValue(new Error('API Error'));
  
  render(<Dashboard />);
  
  await waitFor(() => {
    expect(screen.getByText(/error/i)).toBeInTheDocument();
  });
});
```

---

## 运行测试

### 本地开发

#### 后端
```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 运行所有测试
pytest

# 运行特定测试
pytest tests/unit/test_password_validator.py

# 带覆盖率
pytest --cov=app --cov-report=html
open htmlcov/index.html  # 查看覆盖率报告
```

#### 前端
```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 运行所有测试
npm test

# 单次运行带覆盖率
npm test -- --coverage --watchAll=false

# 查看覆盖率报告
open coverage/lcov-report/index.html
```

### Docker 环境

```bash
# 构建测试容器
docker-compose -f docker-compose.test.yml build

# 运行后端测试
docker-compose -f docker-compose.test.yml run backend-test

# 运行前端测试
docker-compose -f docker-compose.test.yml run frontend-test
```

---

## 编写测试

### 测试命名约定

- **测试文件：** `test_*.py` 或 `*_test.py` (Python), `*.test.js` (JavaScript)
- **测试类：** `Test*` (Python)
- **测试函数：** `test_*`

### 测试结构（AAA 模式）

```python
def test_something():
    # Arrange - 准备测试数据
    user = create_user(username="test")
    
    # Act - 执行被测试的操作
    result = user.get_profile()
    
    # Assert - 验证结果
    assert result["username"] == "test"
```

### 使用标记分类测试

```python
# 单元测试
@pytest.mark.unit
def test_password_validation():
    pass

# 集成测试
@pytest.mark.integration
def test_api_endpoint():
    pass

# 慢速测试
@pytest.mark.slow
def test_heavy_operation():
    pass

# 安全测试
@pytest.mark.security
def test_authentication():
    pass
```

### Mock 外部依赖

```python
def test_with_mock_redis(mocker):
    """使用 mock Redis"""
    mock_redis = mocker.Mock()
    mock_redis.get.return_value = "cached_value"
    
    # 测试逻辑
    result = get_from_cache("key", redis_client=mock_redis)
    assert result == "cached_value"
```

### 参数化测试

```python
@pytest.mark.parametrize("password,expected_valid", [
    ("MySecure!Pass2024", True),
    ("weak", False),
    ("12345678", False),
])
def test_various_passwords(password, expected_valid):
    is_valid, _ = validate_password_strength(password)
    assert is_valid == expected_valid
```

---

## CI/CD 集成

### GitHub Actions

测试在每次 push 和 pull request 时自动运行。

#### 工作流文件

- `.github/workflows/ci.yml` - 主 CI/CD 管道
- `.github/workflows/dependency-review.yml` - 依赖审查

#### CI 流程

1. **代码检出**
2. **依赖安装**
3. **代码检查** (linting)
4. **运行测试**
5. **生成覆盖率报告**
6. **安全扫描**
7. **构建 Docker 镜像**

#### 查看 CI 结果

1. 前往 GitHub 仓库
2. 点击 "Actions" 标签
3. 选择工作流运行
4. 查看详细日志和测试结果

#### CI 环境变量

在 GitHub Settings > Secrets 中配置：

- `DOCKER_USERNAME` - Docker Hub 用户名
- `DOCKER_PASSWORD` - Docker Hub 密码
- `CODECOV_TOKEN` - Codecov 令牌
- `SONAR_TOKEN` - SonarCloud 令牌

---

## 代码覆盖率

### 覆盖率目标

| 组件 | 目标 | 当前 | 状态 |
|------|------|------|------|
| 后端整体 | 70% | 待测 | 🔴 |
| 前端整体 | 60% | 待测 | 🔴 |
| 安全模块 | 90% | 待测 | 🔴 |
| API 端点 | 80% | 待测 | 🔴 |

### 查看覆盖率报告

#### 后端
```bash
cd backend
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

#### 前端
```bash
cd frontend
npm test -- --coverage --watchAll=false
open coverage/lcov-report/index.html
```

### 提高覆盖率

1. **识别未覆盖的代码**
   ```bash
   # 后端
   pytest --cov=app --cov-report=term-missing
   
   # 前端
   npm test -- --coverage --watchAll=false
   ```

2. **编写缺失的测试**
   - 关注红色（未覆盖）和黄色（部分覆盖）的行
   - 优先测试关键路径

3. **排除不需要测试的代码**
   ```python
   # 在代码中添加
   # pragma: no cover
   ```

---

## 最佳实践

### 通用原则

1. **测试应该快速** - 单元测试 < 100ms，集成测试 < 1s
2. **测试应该独立** - 不依赖其他测试的执行顺序
3. **测试应该可重复** - 每次运行结果一致
4. **测试应该清晰** - 易于理解测试目的
5. **一个测试一个断言** - 每个测试只验证一件事

### Do's ✅

```python
✅ 使用描述性的测试名称
def test_user_cannot_login_with_incorrect_password():
    pass

✅ 测试边界条件
def test_password_minimum_length():
    assert validate_password("12345678901") == False  # 11 chars
    assert validate_password("123456789012") == True   # 12 chars

✅ 使用 fixtures 共享设置
@pytest.fixture
def authenticated_user():
    return create_user_and_login()

✅ Mock 外部依赖
def test_api_call(mocker):
    mocker.patch('requests.get', return_value={"data": "test"})
```

### Don'ts ❌

```python
❌ 避免使用魔法数字
# 不好
assert result == 42

# 好
EXPECTED_USER_COUNT = 42
assert result == EXPECTED_USER_COUNT

❌ 不要测试框架功能
# 不要测试 SQLAlchemy 是否工作

❌ 避免测试依赖外部服务
# 使用 mock 替代真实的 API 调用

❌ 不要忽略测试失败
# 修复失败的测试，不要跳过
```

### 测试金字塔

```
        /\
       /  \      E2E Tests (少量)
      /____\     - 完整用户流程
     /      \    
    /        \   Integration Tests (适量)
   /__________\  - API 端点测试
  /            \
 /              \ Unit Tests (大量)
/________________\ - 函数和组件测试
```

---

## 故障排除

### 常见问题

#### 后端测试失败

**问题：** ImportError
```bash
# 解决方案
cd backend
export PYTHONPATH=$PWD
pytest
```

**问题：** 数据库连接失败
```bash
# 检查测试数据库配置
DATABASE_URL=sqlite:///:memory: pytest
```

#### 前端测试失败

**问题：** Module not found
```bash
# 清除缓存
npm test -- --clearCache
npm test
```

**问题：** Timeout
```javascript
// 增加超时时间
jest.setTimeout(10000);
```

### 调试测试

#### 后端
```bash
# 使用 pdb 调试器
pytest --pdb

# 在失败时停止
pytest -x

# 显示打印输出
pytest -s
```

#### 前端
```javascript
// 在测试中添加
screen.debug();  // 打印 DOM

// 使用 console.log
console.log(screen.getByRole('button').innerHTML);
```

---

## 资源和链接

### 文档
- [Pytest 文档](https://docs.pytest.org/)
- [React Testing Library](https://testing-library.com/react)
- [Jest 文档](https://jestjs.io/)

### 教程
- [Testing Best Practices](https://testingjavascript.com/)
- [Python Testing Tutorial](https://realpython.com/python-testing/)

### 工具
- [Coverage.py](https://coverage.readthedocs.io/)
- [Codecov](https://about.codecov.io/)
- [SonarCloud](https://sonarcloud.io/)

---

## 下一步

1. ✅ 运行现有测试
2. ✅ 查看覆盖率报告
3. ✅ 编写缺失的测试
4. ✅ 提高覆盖率到目标
5. ✅ 集成到 CI/CD

---

**最后更新：** 2024-10-28  
**版本：** 1.0.0  
**维护者：** FHIR Analytics Team

