# 🚀 JWKS 认证快速参考

5分钟快速测试 SMART Health IT Bulk Data with JWKS 认证！

---

## ⚡ 最快速的测试方法

### 步骤 1：配置 SMART Health IT 沙盒（2分钟）

1. 访问：https://bulk-data.smarthealthit.org/
2. 配置：
   - **Database Size**: `1,000 Patients`
   - **Require Authentication**: `Yes` ✅  
   - **Authentication Type**: `Backend Services`
   - **JWT Algorithm**: `RS384`
3. 点击 **"Generate RS384 Key Pair"**
4. **复制并保存**：
   - FHIR Server URL
   - Token Endpoint
   - Client ID
   - Private Key（⚠️ 保密！）

### 步骤 2：安装依赖（1分钟）

```bash
# 进入 ETL Service 目录
cd etl-service

# 安装新依赖
pip install PyJWT==2.8.0 cryptography==41.0.7

# 或重新安装所有依赖
pip install -r requirements.txt
```

### 步骤 3：创建测试脚本（1分钟）

创建 `test_jwks.py`：

```python
import requests
import json

# 从沙盒复制的配置
config = {
    "fhir_server_url": "粘贴你的 FHIR Server URL",
    "resource_types": ["Patient", "Condition"],
    "use_smart_auth": True,  # 启用 SMART 认证
    "token_url": "粘贴你的 Token Endpoint",
    "client_id": "粘贴你的 Client ID",
    "private_key": """粘贴你的 Private Key（包含 BEGIN/END 标记）""",
    "algorithm": "RS384"
}

# 调用 API
response = requests.post(
    "http://localhost:8001/api/bulk-data/kick-off",
    json=config
)

print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))
```

### 步骤 4：运行测试（1分钟）

```bash
python test_jwks.py
```

**成功输出**：
```json
{
  "job_id": "...",
  "status": "accepted",
  "message": "Bulk export initiated",
  "status_url": "..."
}
```

---

## 📋 API 配置参数

### 必需参数

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `fhir_server_url` | string | FHIR 服务器 URL | `https://bulk-data.smarthealthit.org/.../fhir` |
| `resource_types` | array | 要导出的资源类型 | `["Patient", "Condition"]` |
| `use_smart_auth` | boolean | 启用 SMART 认证 | `true` |
| `token_url` | string | OAuth Token 端点 | `https://.../auth/token` |
| `client_id` | string | 客户端 ID | `your-client-id` |
| `private_key` | string | 私钥（PEM 格式） | `-----BEGIN PRIVATE KEY-----\n...` |

### 可选参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `algorithm` | string | `"RS384"` | JWT 签名算法 |
| `jwks_url` | string | `null` | JWKS URL（可选） |
| `since` | string | `null` | 仅获取此日期后的数据 |

---

## 🔧 支持的算法

| 算法 | 密钥类型 | 推荐度 | 说明 |
|------|----------|--------|------|
| **RS384** | RSA | ⭐⭐⭐⭐⭐ | 最常用，兼容性好 |
| RS256 | RSA | ⭐⭐⭐⭐ | 较常用 |
| ES384 | ECDSA | ⭐⭐⭐ | 更安全，但支持较少 |
| ES256 | ECDSA | ⭐⭐⭐ | 适合移动设备 |

---

## 🎯 测试场景

### 场景 1：小数据集快速测试

```python
config = {
    # ...基本配置...
    "resource_types": ["Patient"],  # 只导出患者
}
```

**预期时间**: 10-30 秒

### 场景 2：完整数据测试

```python
config = {
    # ...基本配置...
    "resource_types": ["Patient", "Condition", "Encounter", "Observation"],
}
```

**预期时间**: 1-3 分钟

### 场景 3：增量更新

```python
config = {
    # ...基本配置...
    "since": "2024-01-01T00:00:00Z",  # 只获取此日期后的数据
}
```

---

## ⚠️ 常见错误

### 错误 1：401 Unauthorized

```
Failed to get access token: 401
```

**解决**：
- 检查 `client_id` 是否正确
- 确认 `token_url` 没有拼写错误
- 验证私钥格式完整

### 错误 2：Invalid private key

```
ValueError: Invalid private key
```

**解决**：
- 确保私钥包含 `-----BEGIN PRIVATE KEY-----` 和 `-----END PRIVATE KEY-----`
- 不要有多余的空格或换行
- 使用正确的算法（RS384 需要 RSA 密钥）

### 错误 3：JWT signature verification failed

```
JWT signature verification failed
```

**解决**：
- 确认算法设置正确（`RS384` vs `ES384`）
- 检查系统时间是否同步
- 重新生成密钥对

---

## 📊 监控进度

### 查看任务状态

```bash
# 查看后端日志
docker logs -f fhir-etl | grep -i "SMART\|authentication\|token"

# 查看任务列表
curl http://localhost:8001/api/bulk-data/status/{job_id}
```

### 日志示例

**成功的认证**：
```
Using SMART Backend Services authentication
✅ Private key loaded successfully (RS384)
Requesting access token from https://.../auth/token
✅ Access token obtained (expires in 300s)
✅ SMART authentication successful
```

**失败的认证**：
```
Using SMART Backend Services authentication
❌ SMART authentication failed: Failed to get access token: 401
```

---

## 🚀 下一步

### 1. 集成到前端

查看 [JWKS_AUTHENTICATION_GUIDE.md](./JWKS_AUTHENTICATION_GUIDE.md) 的"前端集成"部分

### 2. 生产环境部署

- 将私钥存储在安全的密钥管理服务（如 AWS Secrets Manager）
- 使用环境变量而不是硬编码
- 定期轮换密钥
- 启用访问日志和审计

### 3. 高级功能

- 实现密钥轮换
- 添加 JWKS 端点（发布公钥）
- 支持多个客户端
- 集成监控和告警

---

## 📞 获取帮助

**详细文档**：
- [完整认证指南](./JWKS_AUTHENTICATION_GUIDE.md)
- [SMART Health IT 文档](https://docs.smarthealthit.org/)

**常见问题**：
- 私钥格式问题 → 查看指南"生成密钥对"部分
- 认证失败 → 查看指南"故障排除"部分
- API 使用 → 查看指南"使用 API 测试"部分

---

**最后更新**: 2025-01-15

**快速开始，立即测试！** 🎉

