# 🔐 SMART Backend Services (JWKS) 认证指南

完整指南：如何使用 JWKS URL 验证测试 SMART Health IT Bulk Data API

---

## 📋 目录

- [什么是 SMART Backend Services](#什么是-smart-backend-services)
- [快速开始](#快速开始)
- [生成密钥对](#生成密钥对)
- [配置 SMART Health IT](#配置-smart-health-it)
- [使用 API 测试](#使用-api-测试)
- [前端集成](#前端集成)
- [故障排除](#故障排除)

---

## 🎯 什么是 SMART Backend Services

SMART Backend Services 是 FHIR 的 OAuth 2.0 授权流程，专门用于后端服务（不涉及用户交互）。

### 认证流程

```
1. 客户端创建 JWT assertion（使用私钥签名）
   ↓
2. 发送 JWT 到 Token 端点
   ↓
3. 服务器验证 JWT（使用公钥/JWKS URL）
   ↓
4. 返回 Access Token
   ↓
5. 使用 Access Token 访问 FHIR API
```

### 为什么使用 JWKS?

- ✅ **安全**：使用非对称加密（RSA/ECDSA）
- ✅ **标准**：FHIR 和 OAuth 2.0 标准
- ✅ **无密码**：不需要存储客户端密钥
- ✅ **可验证**：服务器可以验证客户端身份

---

## 🚀 快速开始

### 方法 1：使用 SMART Health IT 沙盒（推荐）

这是最简单的测试方法，SMART Health IT 会自动生成所有需要的配置。

#### 步骤 1：访问沙盒

访问：https://bulk-data.smarthealthit.org/

#### 步骤 2：配置沙盒

<details>
<summary>展开查看详细配置</summary>

**基本配置**：
1. **Database Size**: 选择 `1,000 Patients`（测试用）
2. **Require Authentication**: 选择 `Yes` ✅
3. **Authentication Type**: 选择 `Backend Services (SMART)`
4. **JWT Algorithm**: 选择 `RS384`（推荐）

**高级选项**：
- Resources per File: `100`
- Simulate Error: `None`
- 其他保持默认

</details>

#### 步骤 3：生成密钥对

在沙盒页面的 **"Backend Services Configuration"** 部分：

1. 点击 **"Generate RS384 Key Pair"** 按钮
2. 沙盒会自动生成：
   - **Private Key**（私钥）：⚠️ 保密！
   - **Public Key**（公钥）
   - **JWKS**（公钥集）

3. **记录以下信息**（稍后需要）：
   ```
   FHIR Server URL: https://bulk-data.smarthealthit.org/eyJ.../fhir
   Token Endpoint: https://bulk-data.smarthealthit.org/eyJ.../auth/token
   Client ID: <your-client-id>
   Private Key: -----BEGIN PRIVATE KEY-----...
   JWKS URL: (optional, if using hosted JWKS)
   ```

#### 步骤 4：在系统中测试

使用 API 直接测试（见下方"使用 API 测试"部分）

---

### 方法 2：自己生成密钥对

如果您想要更多控制，可以自己生成密钥。

#### 使用 OpenSSL 生成 RSA 密钥

```bash
# 生成 RSA 4096 位私钥
openssl genrsa -out private_key.pem 4096

# 从私钥提取公钥
openssl rsa -in private_key.pem -pubout -out public_key.pem

# 查看私钥（用于配置）
cat private_key.pem

# 查看公钥（注册到 FHIR 服务器）
cat public_key.pem
```

#### 使用 OpenSSL 生成 EC 密钥（ES384）

```bash
# 生成 EC P-384 私钥
openssl ecparam -genkey -name secp384r1 -noout -out private_key_ec.pem

# 从私钥提取公钥
openssl ec -in private_key_ec.pem -pubout -out public_key_ec.pem

# 查看密钥
cat private_key_ec.pem
cat public_key_ec.pem
```

#### 使用 Python 生成 JWKS

创建 `generate_jwks.py`：

```python
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64
import uuid
import json

# 生成 RSA 密钥对
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=4096,
    backend=default_backend()
)

# 序列化私钥
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

# 获取公钥
public_key = private_key.public_key()
public_numbers = public_key.public_numbers()

# 创建 JWKS
def int_to_base64url(n):
    byte_length = (n.bit_length() + 7) // 8
    n_bytes = n.to_bytes(byte_length, byteorder='big')
    return base64.urlsafe_b64encode(n_bytes).decode('utf-8').rstrip('=')

jwks = {
    "keys": [
        {
            "kty": "RSA",
            "alg": "RS384",
            "use": "sig",
            "kid": str(uuid.uuid4()),
            "n": int_to_base64url(public_numbers.n),
            "e": int_to_base64url(public_numbers.e)
        }
    ]
}

# 输出结果
print("=== Private Key ===")
print(private_pem.decode())
print("\n=== JWKS ===")
print(json.dumps(jwks, indent=2))

# 保存到文件
with open('private_key.pem', 'wb') as f:
    f.write(private_pem)

with open('jwks.json', 'w') as f:
    json.dump(jwks, f, indent=2)

print("\n✅ Files saved: private_key.pem, jwks.json")
```

运行：
```bash
python generate_jwks.py
```

---

## 🧪 使用 API 测试

### 测试 1：通过 API 直接调用

创建测试脚本 `test_smart_auth.py`：

```python
import requests
import json

# 配置（从 SMART Health IT 沙盒获取）
config = {
    "fhir_server_url": "https://bulk-data.smarthealthit.org/eyJ.../fhir",
    "resource_types": ["Patient", "Condition", "Encounter"],
    "use_smart_auth": True,
    "token_url": "https://bulk-data.smarthealthit.org/eyJ.../auth/token",
    "client_id": "your-client-id",
    "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvQ...你的私钥...
-----END PRIVATE KEY-----""",
    "algorithm": "RS384"
}

# 调用 ETL Service
response = requests.post(
    "http://localhost:8001/api/bulk-data/kick-off",
    json=config
)

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

if response.status_code == 200:
    result = response.json()
    job_id = result.get("job_id")
    print(f"\n✅ Bulk export initiated!")
    print(f"Job ID: {job_id}")
    print(f"Status URL: {result.get('status_url')}")
else:
    print(f"\n❌ Failed: {response.text}")
```

运行：
```bash
python test_smart_auth.py
```

### 测试 2：使用 cURL

```bash
# 创建配置 JSON
cat > config.json << 'EOF'
{
  "fhir_server_url": "https://bulk-data.smarthealthit.org/eyJ.../fhir",
  "resource_types": ["Patient", "Condition"],
  "use_smart_auth": true,
  "token_url": "https://bulk-data.smarthealthit.org/eyJ.../auth/token",
  "client_id": "your-client-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQ...\n-----END PRIVATE KEY-----",
  "algorithm": "RS384"
}
EOF

# 调用 API
curl -X POST http://localhost:8001/api/bulk-data/kick-off \
  -H "Content-Type: application/json" \
  -d @config.json
```

### 测试 3：通过后端管理界面

目前后端管理界面不直接支持 JWKS 配置，但您可以：

1. 使用上面的 API 方法
2. 或者先获取 Bearer Token，然后在界面中使用

**获取 Bearer Token**：

```python
from etl-service.app.core.smart_auth import SMARTBackendAuth
import asyncio

async def get_token():
    auth = SMARTBackendAuth(
        token_url="https://bulk-data.smarthealthit.org/eyJ.../auth/token",
        client_id="your-client-id",
        private_key="""-----BEGIN PRIVATE KEY-----
        ...你的私钥...
        -----END PRIVATE KEY-----""",
        algorithm="RS384"
    )
    
    token = await auth.get_access_token()
    print(f"Access Token: {token}")
    return token

# 运行
asyncio.run(get_token())
```

然后在后端管理界面的 "Bearer Token" 字段中粘贴获取的 token。

---

## 💻 前端集成

### 创建 SMART 认证配置组件

创建 `SMARTAuthConfig.js`：

```javascript
import React, { useState } from 'react';

const SMARTAuthConfig = ({ onSubmit }) => {
  const [config, setConfig] = useState({
    fhir_server_url: '',
    resource_types: ['Patient', 'Condition', 'Encounter', 'Observation'],
    use_smart_auth: true,
    token_url: '',
    client_id: '',
    private_key: '',
    algorithm: 'RS384'
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const response = await fetch('http://localhost:8001/api/bulk-data/kick-off', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config)
      });
      
      const result = await response.json();
      
      if (response.ok) {
        alert(`✅ Bulk export started!\nJob ID: ${result.job_id}`);
        if (onSubmit) onSubmit(result);
      } else {
        alert(`❌ Failed: ${result.detail}`);
      }
    } catch (error) {
      alert(`❌ Error: ${error.message}`);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: '800px', margin: '0 auto' }}>
      <h2>🔐 SMART Backend Services 配置</h2>
      
      <div className="form-group">
        <label>FHIR Server URL *</label>
        <input
          type="text"
          value={config.fhir_server_url}
          onChange={(e) => setConfig({...config, fhir_server_url: e.target.value})}
          placeholder="https://bulk-data.smarthealthit.org/.../fhir"
          required
        />
      </div>

      <div className="form-group">
        <label>Token Endpoint *</label>
        <input
          type="text"
          value={config.token_url}
          onChange={(e) => setConfig({...config, token_url: e.target.value})}
          placeholder="https://bulk-data.smarthealthit.org/.../auth/token"
          required
        />
      </div>

      <div className="form-group">
        <label>Client ID *</label>
        <input
          type="text"
          value={config.client_id}
          onChange={(e) => setConfig({...config, client_id: e.target.value})}
          placeholder="your-client-id"
          required
        />
      </div>

      <div className="form-group">
        <label>Private Key (PEM format) *</label>
        <textarea
          rows="8"
          value={config.private_key}
          onChange={(e) => setConfig({...config, private_key: e.target.value})}
          placeholder="-----BEGIN PRIVATE KEY-----&#10;MIIEvQ...&#10;-----END PRIVATE KEY-----"
          required
          style={{ fontFamily: 'monospace', fontSize: '12px' }}
        />
        <small>⚠️ 注意：私钥仅在内存中使用，不会被保存</small>
      </div>

      <div className="form-group">
        <label>Algorithm</label>
        <select
          value={config.algorithm}
          onChange={(e) => setConfig({...config, algorithm: e.target.value})}
        >
          <option value="RS384">RS384 (RSA with SHA-384)</option>
          <option value="RS256">RS256 (RSA with SHA-256)</option>
          <option value="ES384">ES384 (ECDSA with P-384)</option>
          <option value="ES256">ES256 (ECDSA with P-256)</option>
        </select>
      </div>

      <div className="form-group">
        <label>Resource Types</label>
        {['Patient', 'Condition', 'Encounter', 'Observation'].map(type => (
          <label key={type} style={{ display: 'inline-block', marginRight: '15px' }}>
            <input
              type="checkbox"
              checked={config.resource_types.includes(type)}
              onChange={(e) => {
                if (e.target.checked) {
                  setConfig({...config, resource_types: [...config.resource_types, type]});
                } else {
                  setConfig({...config, resource_types: config.resource_types.filter(t => t !== type)});
                }
              }}
            />
            {type}
          </label>
        ))}
      </div>

      <button type="submit" className="btn-primary">
        🚀 开始 Bulk Export
      </button>
    </form>
  );
};

export default SMARTAuthConfig;
```

---

## 🔍 调试和验证

### 验证 JWT Assertion

创建 `verify_jwt.py`：

```python
import jwt
from datetime import datetime

# 你生成的 JWT assertion
jwt_assertion = "eyJ..."

# 使用公钥验证（用于测试）
public_key = """-----BEGIN PUBLIC KEY-----
...
-----END PUBLIC KEY-----"""

try:
    # 不验证签名，只查看内容
    decoded = jwt.decode(jwt_assertion, options={"verify_signature": False})
    
    print("=== JWT Claims ===")
    print(f"Issuer (iss): {decoded.get('iss')}")
    print(f"Subject (sub): {decoded.get('sub')}")
    print(f"Audience (aud): {decoded.get('aud')}")
    print(f"Issued At: {datetime.fromtimestamp(decoded.get('iat'))}")
    print(f"Expires: {datetime.fromtimestamp(decoded.get('exp'))}")
    print(f"JWT ID: {decoded.get('jti')}")
    
    # 验证签名
    verified = jwt.decode(jwt_assertion, public_key, algorithms=["RS384"])
    print("\n✅ JWT signature is valid!")
    
except jwt.ExpiredSignatureError:
    print("❌ JWT has expired!")
except jwt.InvalidTokenError as e:
    print(f"❌ Invalid JWT: {e}")
```

### 查看 Access Token

```python
import jwt

access_token = "your-access-token"

# 解码 token（不验证签名）
decoded = jwt.decode(access_token, options={"verify_signature": False})

print("=== Access Token Claims ===")
print(f"Scope: {decoded.get('scope')}")
print(f"Client ID: {decoded.get('client_id')}")
print(f"Expires: {datetime.fromtimestamp(decoded.get('exp'))}")
```

---

## 🐛 故障排除

### 问题 1：Private key loading failed

**错误**：
```
ValueError: Invalid private key
```

**原因**：
- 私钥格式不正确
- 缺少头部/尾部标记
- 算法不匹配（RSA vs EC）

**解决**：
1. 确保私钥包含完整的 PEM 格式：
```
-----BEGIN PRIVATE KEY-----
...base64 encoded key...
-----END PRIVATE KEY-----
```

2. 检查算法：
   - RS384/RS256 需要 RSA 密钥
   - ES384/ES256 需要 EC 密钥

3. 验证私钥：
```bash
# 验证 RSA 私钥
openssl rsa -in private_key.pem -check

# 验证 EC 私钥
openssl ec -in private_key_ec.pem -check
```

### 问题 2：Token request failed: 401

**错误**：
```
Failed to get access token: 401 - Unauthorized
```

**原因**：
- Client ID 不正确
- JWT 签名验证失败
- Token URL 错误

**解决**：
1. 验证 Client ID 与服务器注册的一致
2. 确认 token_url 正确
3. 检查服务器日志中的错误详情

### 问题 3：JWT assertion expired

**错误**：
```
JWT has expired
```

**原因**：
- 系统时间不同步
- JWT 有效期太短

**解决**：
1. 同步系统时间：
```bash
# Windows
w32tm /resync

# Linux
sudo ntpdate pool.ntp.org
```

2. 增加 JWT 有效期（在 `smart_auth.py` 中）：
```python
def create_jwt_assertion(self, expires_in: int = 600):  # 10分钟
```

### 问题 4：JWKS URL not accessible

**错误**：
```
Cannot fetch JWKS from URL
```

**原因**：
- JWKS URL 不可访问
- 网络防火墙阻止

**解决**：
1. 验证 JWKS URL 可访问：
```bash
curl -v https://your-jwks-url.com/.well-known/jwks.json
```

2. 或者不使用 JWKS URL，让服务器使用预注册的公钥

---

## 📚 参考资源

- [SMART Backend Services Specification](https://hl7.org/fhir/smart-app-launch/backend-services.html)
- [FHIR Bulk Data Access IG](https://hl7.org/fhir/uv/bulkdata/)
- [OAuth 2.0 JWT Bearer Token](https://datatracker.ietf.org/doc/html/rfc7523)
- [SMART Health IT Sandbox](https://bulk-data.smarthealthit.org/)

---

## ✅ 完整测试检查清单

在生产环境使用前，确保：

- [ ] 私钥安全保存（不提交到版本控制）
- [ ] Client ID 已在 FHIR 服务器注册
- [ ] 公钥/JWKS 已上传到服务器
- [ ] Token endpoint 正确配置
- [ ] JWT 算法与密钥类型匹配
- [ ] 系统时间同步
- [ ] Access token 缓存工作正常
- [ ] 网络连接稳定
- [ ] 日志记录完整

---

**最后更新**: 2025-01-15

**状态**: ✅ 功能已实现并可测试

祝您测试顺利！🚀

