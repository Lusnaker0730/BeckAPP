#!/usr/bin/env python3
"""
使用 SMART Health IT 完整配置导出所有 Groups 的数据
"""

import requests
import json
import time
from typing import Dict, List, Optional
from datetime import datetime

# ============================================================================
# 配置
# ============================================================================

ETL_SERVICE_URL = "http://localhost:8001"

# 所有可用的 Groups
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

# 要导出的资源类型（只包含系统支持的类型）
RESOURCE_TYPES = [
    "Patient",
    "Condition",
    "Observation",
    "Encounter"  # 注意: AllergyIntolerance, MedicationRequest, Procedure 暂不支持
]

# ============================================================================
# 辅助函数
# ============================================================================

def load_smart_config() -> Dict:
    """从 config.json 加载 SMART Health IT 配置"""
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ 错误: 找不到 config.json 文件")
        print("请从 SMART Health IT 下载完整配置文件并保存为 config.json")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ 错误: config.json 格式不正确: {e}")
        exit(1)

def extract_private_key(config: Dict) -> Dict:
    """提取用于签名的私钥 JWK"""
    jwks = config.get("jwks", {})
    keys = jwks.get("keys", [])
    
    # 查找包含 "sign" 操作的密钥
    for key in keys:
        if "sign" in key.get("key_ops", []):
            return key
    
    print("❌ 错误: 在配置中找不到用于签名的私钥")
    exit(1)

def check_etl_service() -> bool:
    """检查 ETL Service 是否运行"""
    try:
        response = requests.get(f"{ETL_SERVICE_URL}/api/bulk-data/jobs", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def export_group(
    group_id: str,
    group_name: str,
    fhir_url: str,
    token_url: str,
    client_id: str,
    private_key: Dict
) -> Optional[str]:
    """
    导出指定 Group 的数据
    
    返回: job_id 如果成功，否则 None
    """
    print(f"\n{'='*70}")
    print(f"📦 开始导出: {group_name}")
    print(f"   Group ID: {group_id}")
    print(f"{'='*70}")
    
    # 构建 Group Export URL（Group-level export）
    # 注意：SMART Health IT 的 Group Export 需要在 FHIR URL 后添加 /Group/{id}
    group_export_url = f"{fhir_url}/Group/{group_id}"
    
    # 准备请求负载
    payload = {
        "fhir_server_url": group_export_url,
        "resource_types": RESOURCE_TYPES,
        "use_smart_auth": True,
        "token_url": token_url,
        "client_id": client_id,
        "private_key": json.dumps(private_key),  # 转为 JSON 字符串
        "algorithm": "RS384"
    }
    
    try:
        # 发起 Bulk Data Export
        print("🚀 发起导出请求...")
        response = requests.post(
            f"{ETL_SERVICE_URL}/api/bulk-data/kick-off",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            job_id = result.get("job_id")
            status_url = result.get("status_url", "N/A")
            method = result.get("method", "bulk_export")
            
            print(f"✅ 导出已启动!")
            print(f"   Job ID: {job_id}")
            print(f"   Method: {method}")
            if status_url != "N/A":
                print(f"   Status URL: {status_url[:80]}...")
            
            return job_id
        else:
            print(f"❌ 导出失败: HTTP {response.status_code}")
            error_detail = response.json().get("detail", response.text) if response.text else "Unknown error"
            print(f"   错误: {error_detail[:200]}")
            return None
    
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        return None

def monitor_job(job_id: str, group_name: str, max_wait_minutes: int = 15) -> Dict:
    """
    监控导出任务状态
    
    返回: 任务最终状态
    """
    print(f"\n⏳ 监控任务进度...")
    
    max_wait = max_wait_minutes * 60
    elapsed = 0
    check_interval = 10
    last_status = None
    
    while elapsed < max_wait:
        try:
            response = requests.get(
                f"{ETL_SERVICE_URL}/api/bulk-data/status/{job_id}",
                timeout=60  # 增加到 60 秒，因为数据库加载需要时间
            )
            
            if response.status_code == 200:
                status = response.json()
                current_status = status.get("status")
                
                # 只在状态变化时打印
                if current_status != last_status:
                    print(f"   📊 状态: {current_status}")
                    last_status = current_status
                
                # 显示进度信息
                if "progress" in status and current_status == last_status:
                    print(f"      进度: {status['progress']}", end="\r")
                
                if "file_count" in status:
                    print(f"      文件数: {status['file_count']}")
                
                if "records_loaded" in status:
                    print(f"      已加载记录: {status['records_loaded']}")
                
                # 检查是否完成
                if current_status == "completed":
                    print(f"\n✅ {group_name} 导出完成!")
                    print(f"   ✓ 文件数: {len(status.get('files', []))}")
                    print(f"   ✓ 已转换: {status.get('records_transformed', 0)} 条记录")
                    print(f"   ✓ 已加载: {status.get('records_loaded', 0)} 条记录")
                    return status
                
                elif current_status == "failed":
                    print(f"\n❌ {group_name} 导出失败!")
                    error_msg = status.get('error', 'Unknown error')
                    print(f"   错误: {error_msg[:200]}")
                    return status
                
                elif current_status in ["in-progress", "downloading"]:
                    pass
                
                # 等待后继续
                time.sleep(check_interval)
                elapsed += check_interval
            else:
                print(f"❌ 无法获取状态: HTTP {response.status_code}")
                return {"status": "error", "error": f"Status check failed: {response.status_code}"}
        
        except requests.exceptions.RequestException as e:
            print(f"❌ 状态检查失败: {e}")
            return {"status": "error", "error": str(e)}
    
    print(f"\n⏰ 超时: 任务执行时间超过 {max_wait_minutes} 分钟")
    return {"status": "timeout", "elapsed_minutes": max_wait_minutes}

def print_summary(results: List[Dict]):
    """打印导出摘要"""
    print("\n" + "="*70)
    print("📊 导出摘要报告")
    print("="*70)
    
    total_records = 0
    total_patients = 0
    successful = 0
    failed = 0
    
    for result in results:
        status_icon = "✅" if result["success"] else "❌"
        records = result.get("records_loaded", 0)
        patients = result.get("expected_patients", 0)
        
        print(f"\n{status_icon} {result['group_name']}")
        print(f"   Group ID: {result['group_id']}")
        print(f"   预期病人数: {patients}")
        
        if result["success"]:
            print(f"   已加载记录数: {records}")
            if result.get("job_id"):
                print(f"   Job ID: {result['job_id']}")
            successful += 1
            total_records += records
            total_patients += patients
        else:
            print(f"   失败原因: {result.get('error', 'Unknown')}")
            failed += 1
    
    print("\n" + "-"*70)
    print(f"总计:")
    print(f"  ✅ 成功: {successful}/{len(results)}")
    print(f"  ❌ 失败: {failed}/{len(results)}")
    print(f"  👥 病人数: {total_patients}")
    print(f"  📝 记录数: {total_records}")
    print("="*70)
    
    # 保存结果到文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = f"export_results_{timestamp}.json"
    
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 详细结果已保存到: {result_file}")

# ============================================================================
# 主程序
# ============================================================================

def main():
    """主函数"""
    print("="*70)
    print("🏥 SMART Health IT Bulk Data 批量导出工具")
    print("   使用完整配置文件")
    print("="*70)
    
    # 1. 加载配置
    print("\n📖 步骤 1/4: 加载配置...")
    config = load_smart_config()
    
    fhir_url = config.get("fhir_url")
    token_url = config.get("token_url")
    client_id = config.get("client_id")
    private_key = extract_private_key(config)
    
    print(f"   ✓ FHIR Server: {fhir_url[:50]}...")
    print(f"   ✓ Token URL: {token_url}")
    print(f"   ✓ Client ID: {client_id[:50]}...")
    print(f"   ✓ 私钥 Key ID: {private_key.get('kid')}")
    
    # 2. 检查服务
    print("\n🔍 步骤 2/4: 检查 ETL Service...")
    if not check_etl_service():
        print("❌ 错误: ETL Service 未运行或无法访问")
        print(f"   请确保服务运行在: {ETL_SERVICE_URL}")
        print("   提示: 运行 'docker-compose up -d' 启动服务")
        exit(1)
    print(f"   ✓ ETL Service 正常运行")
    
    # 3. 导出所有 Groups
    print("\n🚀 步骤 3/4: 开始导出所有 Groups...")
    print(f"   总共 {len(GROUPS)} 个 Groups")
    print(f"   资源类型: {', '.join(RESOURCE_TYPES)}")
    
    results = []
    
    for i, group in enumerate(GROUPS, 1):
        print(f"\n" + "─"*70)
        print(f"进度: [{i}/{len(GROUPS)}]")
        
        # 导出 Group
        job_id = export_group(
            group_id=group["id"],
            group_name=group["name"],
            fhir_url=fhir_url,
            token_url=token_url,
            client_id=client_id,
            private_key=private_key
        )
        
        if job_id:
            # 监控任务
            status = monitor_job(job_id, group["name"])
            
            results.append({
                "group_name": group["name"],
                "group_id": group["id"],
                "expected_patients": group["patients"],
                "job_id": job_id,
                "success": status.get("status") == "completed",
                "records_loaded": status.get("records_loaded", 0),
                "records_transformed": status.get("records_transformed", 0),
                "files": len(status.get("files", [])),
                "error": status.get("error")
            })
        else:
            results.append({
                "group_name": group["name"],
                "group_id": group["id"],
                "expected_patients": group["patients"],
                "success": False,
                "error": "Failed to start export"
            })
        
        # 在两个 Groups 之间稍作延迟
        if i < len(GROUPS):
            wait_time = 5
            print(f"\n⏸️  等待 {wait_time} 秒后继续下一个 Group...")
            time.sleep(wait_time)
    
    # 4. 打印摘要
    print("\n" + "─"*70)
    print("📊 步骤 4/4: 生成摘要报告...")
    print_summary(results)
    
    print("\n🎉 所有操作完成!")
    print("💡 提示: 您可以访问 http://localhost:3000 查看导入的数据")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        exit(0)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

