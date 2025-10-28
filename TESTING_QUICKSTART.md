# 🚀 测试快速开始

## ⚡ 5 分钟开始测试

### 后端测试

```bash
# 1. 安装依赖
cd backend
pip install -r requirements.txt

# 2. 运行所有测试
pytest

# 3. 查看覆盖率
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### 前端测试

```bash
# 1. 安装依赖
cd frontend
npm install

# 2. 运行所有测试
npm test

# 3. 单次运行带覆盖率
npm test -- --coverage --watchAll=false
open coverage/lcov-report/index.html
```

---

## 📝 常用命令

### 后端 (pytest)

| 命令 | 用途 |
|------|------|
| `pytest` | 运行所有测试 |
| `pytest -v` | 详细输出 |
| `pytest -m unit` | 只运行单元测试 |
| `pytest -m integration` | 只运行集成测试 |
| `pytest --cov=app` | 带覆盖率 |
| `pytest -x` | 第一个失败时停止 |
| `pytest tests/unit/test_security.py` | 运行特定文件 |
| `pytest -k "password"` | 运行名称包含 password 的测试 |

### 前端 (Jest)

| 命令 | 用途 |
|------|------|
| `npm test` | 运行所有测试（监视模式） |
| `npm test -- --watchAll=false` | 单次运行 |
| `npm test -- --coverage` | 带覆盖率 |
| `npm test Login.test.js` | 运行特定文件 |
| `npm test -- -u` | 更新快照 |
| `npm test -- --clearCache` | 清除缓存 |

---

## ✅ 测试检查清单

### 运行测试前

- [ ] 已安装所有依赖
- [ ] 环境变量已配置（测试环境）
- [ ] 数据库/服务可访问（如需要）

### 编写新测试时

- [ ] 测试文件命名符合约定（`test_*.py` / `*.test.js`）
- [ ] 测试函数命名清晰（`test_user_can_login`）
- [ ] 使用 AAA 模式（Arrange, Act, Assert）
- [ ] Mock 外部依赖
- [ ] 添加适当的测试标记

### 提交代码前

- [ ] 所有测试通过
- [ ] 代码覆盖率达标
- [ ] 没有跳过的测试
- [ ] Linter 检查通过

---

## 🎯 测试类型

### 单元测试
```python
# backend/tests/unit/test_password_validator.py
def test_valid_password():
    assert validate_password("Secure123!") == True
```

### 集成测试
```python
# backend/tests/integration/test_auth_api.py
def test_login_endpoint(client):
    response = client.post("/api/auth/login", data={...})
    assert response.status_code == 200
```

### 前端组件测试
```javascript
// frontend/src/components/Login.test.js
test('renders login form', () => {
  render(<Login />);
  expect(screen.getByRole('button')).toBeInTheDocument();
});
```

---

## 🐛 调试测试

### 后端调试
```bash
# 使用 pdb 调试器
pytest --pdb

# 显示打印输出
pytest -s

# 只运行失败的测试
pytest --lf
```

### 前端调试
```javascript
// 在测试中
screen.debug();  // 打印 DOM
console.log(screen.getByRole('button'));
```

---

## 📊 查看覆盖率

### 后端
```bash
# 生成 HTML 报告
pytest --cov=app --cov-report=html

# 在终端查看
pytest --cov=app --cov-report=term-missing

# XML 报告（CI 用）
pytest --cov=app --cov-report=xml
```

### 前端
```bash
# 生成覆盖率报告
npm test -- --coverage --watchAll=false

# 查看报告
open coverage/lcov-report/index.html
```

---

## 🔍 常见问题

### Q: 测试运行很慢？
**A:** 使用标记只运行需要的测试
```bash
pytest -m unit  # 只运行快速的单元测试
```

### Q: 测试在 CI 通过，本地失败？
**A:** 检查环境变量和依赖版本
```bash
pip list  # 检查 Python 包版本
npm list  # 检查 Node 包版本
```

### Q: 如何跳过某个测试？
**A:** 使用 skip 装饰器
```python
@pytest.mark.skip(reason="待修复")
def test_something():
    pass
```

### Q: 如何只运行一个测试？
```bash
# 后端
pytest tests/unit/test_file.py::TestClass::test_method

# 前端
npm test -- test_file.test.js -t "test name"
```

---

## 📚 完整文档

查看 [TESTING_GUIDE.md](./TESTING_GUIDE.md) 获取完整测试文档。

---

## 🎊 开始测试！

```bash
# 快速开始
cd backend && pytest
cd frontend && npm test
```

**祝测试顺利！** ✨

