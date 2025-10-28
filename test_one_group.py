#!/usr/bin/env python3
"""
测试单个 Group 的数据导出和加载
"""

import requests
import json
import time

ETL_SERVICE_URL = "http://localhost:8001"

# 加载配置
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

fhir_url = config["fhir_url"]
token_url = config["token_url"]
client_id = config["client_id"]

# 提取签名密钥
private_key = None
for key in config["jwks"]["keys"]:
    if "sign" in key.get("key_ops", []):
        private_key = key
        break

print("="*70)
print("🧪 测试单个 Group 导出")
print("="*70)
print(f"测试 Group: Fallon Health (最小的 Group，30 个病人)")

# 准备请求
payload = {
    "fhir_server_url": f"{fhir_url}/Group/FallonHealth",
    "resource_types": ["Patient", "Condition", "Observation", "Encounter"],
    "use_smart_auth": True,
    "token_url": token_url,
    "client_id": client_id,
    "private_key": json.dumps(private_key),
    "algorithm": "RS384"
}

print("\n🚀 发起导出...")
response = requests.post(
    f"{ETL_SERVICE_URL}/api/bulk-data/kick-off",
    json=payload,
    timeout=30
)

if response.status_code == 200:
    result = response.json()
    job_id = result["job_id"]
    print(f"✅ Job ID: {job_id}")
    
    # 监控状态
    print("\n⏳ 监控进度...")
    for i in range(60):  # 最多等待 10 分钟
        time.sleep(10)
        status_resp = requests.get(f"{ETL_SERVICE_URL}/api/bulk-data/status/{job_id}")
        if status_resp.status_code == 200:
            status = status_resp.json()
            current_status = status.get("status")
            print(f"   [{i+1}] 状态: {current_status}", end="")
            
            if "records_loaded" in status:
                print(f" | 已加载: {status['records_loaded']}", end="")
            if "records_transformed" in status:
                print(f" | 已转换: {status['records_transformed']}", end="")
            
            print()  # 换行
            
            if current_status == "completed":
                print(f"\n🎉 完成!")
                print(f"   文件数: {len(status.get('files', []))}")
                print(f"   已转换: {status.get('records_transformed', 0)}")
                print(f"   已加载: {status.get('records_loaded', 0)}")
                break
            elif current_status == "failed":
                print(f"\n❌ 失败: {status.get('error')}")
                break
else:
    print(f"❌ 请求失败: {response.status_code}")
    print(response.text)

print("\n" + "="*70)

