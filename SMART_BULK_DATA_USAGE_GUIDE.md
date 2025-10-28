# SMART Health IT Bulk Data 使用指南

## 📋 概述

本指南将教您如何使用我们的 ETL 服务从 SMART Health IT Bulk Data Server 抓取各个 Group 的病人数据。

## 🔑 前置准备

### 1. 从 SMART Health IT 获取配置信息

访问 [SMART Bulk Data Server](https://bulk-data.smarthealthit.org/) 并配置您的设置：

- **FHIR Server URL**: 从页面复制（包含完整的 token）
- **Authentication URL**: `https://bulk-data.smarthealthit.org/auth/token`
- **Client ID**: 从页面复制
- **Private Key**: 点击 "Download as JSON" 后，从 JSON 文件中提取

### 2. 准备认证密钥

从下载的 JSON 配置文件中提取私钥：

```json
{
  "auth_type": "backend-services",
  "token_endpoint": "https://bulk-data.smarthealthit.org/auth/token",
  "client_id": "your-client-id",
  "key": {
    "kty": "RSA",
    "kid": "...",
    "n": "...",
    "e": "...",
    "d": "...",
    // ... 其他字段
  }
}
```

您需要将整个 `key` 对象转换为 PEM 格式，或直接使用 JSON 格式的密钥。

## 📦 方法一：使用 HTTP API（推荐）

### Step 1: 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 检查服务状态
docker-compose ps
```

### Step 2: 抓取单个 Group 的数据

使用以下 Python 脚本或 curl 命令：

#### Python 脚本示例

```python
import requests
import json
import time

# ETL 服务地址
ETL_SERVICE_URL = "http://localhost:8001"  # ETL Service 端口

# SMART Health IT 配置（从页面复制）
FHIR_SERVER_URL = "https://bulk-data.smarthealthit.org/eyJlcnIi..."  # 完整的 URL
TOKEN_URL = "https://bulk-data.smarthealthit.org/auth/token"
CLIENT_ID = "eyJhbGciOiJIUzI1Ni..."  # 您的 Client ID

# 私钥（从下载的 JSON 文件中提取）
PRIVATE_KEY = {
    "kty": "RSA",
    "kid": "...",
    "n": "...",
    "e": "AQAB",
    "d": "...",
    # ... 完整的 JWK
}

# Group 列表（从页面查看）
GROUPS = [
    {"name": "BMC HealthNet", "id": "BMCHealthNet", "patients": 100},
    {"name": "Blue Cross Blue Shield", "id": "BlueCrossBlueShield", "patients": 270},
    {"name": "Fallon Health", "id": "FallonHealth", "patients": 30},
    {"name": "Harvard Pilgrim Health Care", "id": "HarvardPilgrimHealthCare", "patients": 30},
    {"name": "Health New England", "id": "HealthNewEngland", "patients": 250},
    {"name": "Minuteman Health", "id": "MinutemanHealth", "patients": 30},
    {"name": "Neighborhood Health Plan", "id": "NeighborhoodHealthPlan", "patients": 70},
    {"name": "Tufts Health Plan", "id": "TuftsHealthPlan", "patients": 220},
]

def export_group(group_id, group_name):
    """导出指定 Group 的数据"""
    print(f"\n{'='*60}")
    print(f"📦 开始导出: {group_name} (Group ID: {group_id})")
    print(f"{'='*60}")
    
    # 构建 Group 专用的 FHIR URL
    group_fhir_url = f"{FHIR_SERVER_URL}/Group/{group_id}"
    
    # 准备请求数据
    payload = {
        "fhir_server_url": group_fhir_url,
        "resource_types": ["Patient", "Condition", "Observation", "MedicationRequest", "Encounter"],
        "use_smart_auth": True,
        "token_url": TOKEN_URL,
        "client_id": CLIENT_ID,
        "private_key": json.dumps(PRIVATE_KEY),  # 转为 JSON 字符串
        "algorithm": "RS384"
    }
    
    try:
        # 启动导出
        response = requests.post(
            f"{ETL_SERVICE_URL}/api/bulk-data/kick-off",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            job_id = result.get("job_id")
            status_url = result.get("status_url")
            
            print(f"✅ 导出已启动!")
            print(f"   Job ID: {job_id}")
            print(f"   Status URL: {status_url}")
            
            # 轮询状态
            return monitor_job(job_id)
        else:
            print(f"❌ 导出失败: {response.status_code}")
            print(f"   错误: {response.text}")
            return None
    
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None

def monitor_job(job_id):
    """监控导出任务状态"""
    print(f"\n⏳ 监控任务状态...")
    
    max_wait = 600  # 最多等待 10 分钟
    elapsed = 0
    
    while elapsed < max_wait:
        try:
            response = requests.get(
                f"{ETL_SERVICE_URL}/api/bulk-data/status/{job_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                status = response.json()
                current_status = status.get("status")
                
                print(f"   状态: {current_status}", end="")
                
                if "progress" in status:
                    print(f" - 进度: {status['progress']}", end="")
                
                if current_status == "completed":
                    print("\n✅ 导出完成!")
                    print(f"   文件数: {len(status.get('files', []))}")
                    print(f"   已加载记录数: {status.get('records_loaded', 0)}")
                    return status
                
                elif current_status == "failed":
                    print("\n❌ 导出失败!")
                    print(f"   错误: {status.get('error', 'Unknown error')}")
                    return None
                
                elif current_status in ["in-progress", "downloading"]:
                    print(" - 继续等待...")
                    time.sleep(10)
                    elapsed += 10
                else:
                    print()
                    time.sleep(5)
                    elapsed += 5
            else:
                print(f"❌ 无法获取状态: {response.status_code}")
                return None
        
        except Exception as e:
            print(f"❌ 状态检查失败: {e}")
            return None
    
    print(f"\n⏰ 超时: 任务执行时间超过 {max_wait/60} 分钟")
    return None

def export_all_groups():
    """导出所有 Group 的数据"""
    print("🚀 开始导出所有 Groups 的数据")
    print(f"   总共 {len(GROUPS)} 个 Groups")
    
    results = []
    
    for i, group in enumerate(GROUPS, 1):
        print(f"\n[{i}/{len(GROUPS)}] 处理中...")
        result = export_group(group["id"], group["name"])
        
        results.append({
            "group": group["name"],
            "group_id": group["id"],
            "success": result is not None,
            "records_loaded": result.get("records_loaded", 0) if result else 0
        })
        
        # 在两个请求之间稍作延迟
        if i < len(GROUPS):
            print("\n⏸️  等待 5 秒后继续...")
            time.sleep(5)
    
    # 打印摘要
    print("\n" + "="*60)
    print("📊 导出摘要")
    print("="*60)
    
    total_records = 0
    successful = 0
    
    for result in results:
        status_icon = "✅" if result["success"] else "❌"
        print(f"{status_icon} {result['group']}: {result['records_loaded']} 条记录")
        
        if result["success"]:
            successful += 1
            total_records += result["records_loaded"]
    
    print(f"\n成功: {successful}/{len(GROUPS)}")
    print(f"总记录数: {total_records}")

if __name__ == "__main__":
    # 导出所有 Groups
    export_all_groups()
    
    # 或者只导出特定 Group
    # export_group("BMCHealthNet", "BMC HealthNet")
```

#### 使用 curl 命令示例

```bash
#!/bin/bash

# 配置
ETL_SERVICE="http://localhost:8002"
FHIR_SERVER="https://bulk-data.smarthealthit.org/eyJlcnIi..."  # 您的完整 URL
TOKEN_URL="https://bulk-data.smarthealthit.org/auth/token"
CLIENT_ID="eyJhbGciOiJIUzI1Ni..."  # 您的 Client ID

# 私钥（需要转义）
PRIVATE_KEY='{"kty":"RSA","kid":"...","n":"...","e":"AQAB","d":"..."}'

# Group ID
GROUP_ID="BMCHealthNet"

# 启动导出
curl -X POST "$ETL_SERVICE/api/bulk-data/kick-off" \
  -H "Content-Type: application/json" \
  -d "{
    \"fhir_server_url\": \"$FHIR_SERVER/Group/$GROUP_ID\",
    \"resource_types\": [\"Patient\", \"Condition\", \"Observation\", \"MedicationRequest\", \"Encounter\"],
    \"use_smart_auth\": true,
    \"token_url\": \"$TOKEN_URL\",
    \"client_id\": \"$CLIENT_ID\",
    \"private_key\": \"$PRIVATE_KEY\",
    \"algorithm\": \"RS384\"
  }"
```

### Step 3: 检查导出状态

```bash
# 使用返回的 job_id 检查状态
curl http://localhost:8002/api/bulk-data/status/{job_id}

# 列出所有任务
curl http://localhost:8002/api/bulk-data/jobs
```

## 📦 方法二：使用官方 Bulk Data Client（参考）

如果您想直接使用 SMART 的官方客户端进行测试：

```bash
# 克隆官方客户端
git clone https://github.com/smart-on-fhir/bulk-data-client.git
cd bulk-data-client
npm install

# 从 SMART Health IT 下载配置文件
# 点击页面上的 "Download as JSON"

# 运行导出（使用配置文件）
node . --config your-downloaded-config.json --group BMCHealthNet
```

## 🔧 高级配置

### 指定资源类型

```python
# 只导出特定资源类型
payload = {
    "fhir_server_url": f"{FHIR_SERVER_URL}/Group/{group_id}",
    "resource_types": ["Patient", "Condition"],  # 只导出这两种
    # ...
}
```

### 增量导出（使用 _since 参数）

```python
# 只导出 2023 年后的数据
payload = {
    "fhir_server_url": f"{FHIR_SERVER_URL}/Group/{group_id}",
    "resource_types": ["Patient", "Condition"],
    "since": "2023-01-01T00:00:00Z",  # 增量导出
    # ...
}
```

### 恢复中断的导出

如果导出过程中断，使用保存的 `status_url` 恢复：

```python
# 恢复导出
resume_payload = {
    "status_url": "https://bulk-data.smarthealthit.org/status/...",
    "bearer_token": "your-token"  # 如果需要
}

response = requests.post(
    f"{ETL_SERVICE_URL}/api/bulk-data/resume",
    json=resume_payload
)
```

## 📊 查看导出结果

### 1. 检查数据库

```bash
# 连接到 PostgreSQL
docker-compose exec postgres psql -U fhir_user -d fhir_analytics

# 查看已导入的数据
SELECT 
    etl_job_id,
    COUNT(*) as patient_count
FROM patients
GROUP BY etl_job_id;

SELECT 
    etl_job_id,
    COUNT(*) as condition_count
FROM conditions
GROUP BY etl_job_id;
```

### 2. 使用前端查看

访问 `http://localhost:3000` 并登录：
- 进入 **数据可视化** 页面
- 使用 **ETL Job ID** 筛选查看特定 Group 的数据

## ⚠️ 注意事项

1. **速率限制**: SMART Health IT 服务器可能有速率限制，建议在导出多个 Groups 时加入延迟
2. **数据量**: 某些 Groups 的数据量较大（如 Blue Cross Blue Shield 有 270 个病人），导出可能需要几分钟
3. **认证 Token**: SMART Health IT 的配置 token 有有效期，过期后需要重新生成
4. **存储空间**: 确保有足够的磁盘空间存储导出的数据

## 🐛 故障排查

### 认证失败

```
❌ SMART authentication failed: Invalid JWT
```

**解决方案**:
- 确认 Client ID 正确
- 检查私钥格式是否正确
- 验证 Token URL 是否正确

### 超时错误

```
❌ Error: Timeout exceeded
```

**解决方案**:
- 增加超时时间配置（在 `.env` 中设置 `HTTP_TIMEOUT_READ=600`）
- 检查网络连接
- 尝试减少资源类型数量

### 导出失败

```
❌ Bulk export reported error: Too many files
```

**解决方案**:
- 系统会自动切换到 FHIR search fallback 模式
- 如果仍然失败，尝试减少资源类型或使用 `_since` 参数限制数据范围

## 📚 相关文档

- [JWKS Authentication Guide](./JWKS_AUTHENTICATION_GUIDE.md)
- [ETL Service README](./etl-service/README.md)
- [SMART Bulk Data Specification](https://hl7.org/fhir/uv/bulkdata/)
- [SMART Health IT Documentation](https://docs.smarthealthit.org/)

## 💡 最佳实践

1. **分批导出**: 不要一次性导出所有 Groups，分批进行
2. **错误处理**: 使用 try-catch 捕获错误，失败的 Group 可以稍后重试
3. **日志记录**: 保存每次导出的 job_id 和结果，便于追踪
4. **数据验证**: 导出后验证数据完整性（检查记录数是否合理）
5. **定期清理**: 定期清理旧的导出文件（在 `/data/bulk` 目录下）

## 🎯 快速开始示例

```bash
# 1. 启动服务
docker-compose up -d

# 2. 保存上面的 Python 脚本为 export_groups.py

# 3. 更新脚本中的配置信息
# - FHIR_SERVER_URL
# - CLIENT_ID
# - PRIVATE_KEY

# 4. 运行脚本
python export_groups.py

# 5. 等待完成，然后在前端查看数据
# http://localhost:3000
```

## 📞 获取帮助

如果遇到问题：
1. 检查 Docker 日志: `docker-compose logs etl-service`
2. 查看 ETL Service 日志以获取详细错误信息
3. 确认所有服务都在运行: `docker-compose ps`

