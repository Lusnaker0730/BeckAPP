#!/usr/bin/env python3
"""
SMART Health IT Bulk Data 系统级别导出工具 - 完整版
导出所有数据（不限定 Group）
"""
import requests
import json
import time
from datetime import datetime

# ===== 配置部分 =====
ETL_SERVICE_URL = "http://localhost:8001"
CONFIG_FILE = "config_full.json"

# 要导出的资源类型
RESOURCE_TYPES = [
    "Patient",
    "Condition",
    "Observation",
    "Encounter"
]

def load_config():
    """加载配置文件"""
    print(f"\n📖 步骤 1/3: 加载配置...")
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 提取私钥的 kid
    private_key = None
    kid = None
    for key in config['jwks']['keys']:
        if 'sign' in key.get('key_ops', []):
            private_key = json.dumps(key)
            kid = key.get('kid')
            break
    
    print(f"   ✓ FHIR Server: {config['fhir_url'][:50]}...")
    print(f"   ✓ Token URL: {config['token_url']}")
    print(f"   ✓ 私钥 Key ID: {kid}")
    
    return {
        'fhir_url': config['fhir_url'],
        'token_url': config['token_url'],
        'client_id': config['client_id'],
        'private_key': private_key
    }

def export_system_level(config):
    """执行系统级别的导出（所有数据）"""
    print(f"\n🚀 步骤 2/3: 开始系统级别导出...")
    print(f"   资源类型: {', '.join(RESOURCE_TYPES)}")
    print(f"   预期: 1000 个病人的完整数据")
    
    # 系统级别的 export URL（不使用 Group）
    export_url = f"{config['fhir_url']}/$export"
    
    print(f"\n📍 Export URL: {export_url}")
    
    # 构建请求参数
    request_data = {
        "fhir_server_url": export_url,
        "output_format": "application/fhir+ndjson",
        "resource_types": RESOURCE_TYPES,
        "use_smart_auth": True,
        "token_url": config['token_url'],
        "client_id": config['client_id'],
        "private_key": config['private_key'],
        "algorithm": "RS384"
    }
    
    try:
        # 发起导出请求
        print(f"\n🚀 发起导出请求...")
        response = requests.post(
            f"{ETL_SERVICE_URL}/api/bulk-data/kick-off",
            json=request_data,
            timeout=30
        )
        
        if response.status_code not in [200, 202]:
            print(f"❌ 导出失败: HTTP {response.status_code}")
            print(f"   响应: {response.text}")
            return None
        
        result = response.json()
        job_id = result['job_id']
        method = result.get('method', 'bulk_export')
        
        print(f"✅ 导出已启动!")
        print(f"   Job ID: {job_id}")
        print(f"   Method: {method}")
        
        # 监控任务状态
        print(f"\n⏳ 监控任务进度...")
        print(f"   (这可能需要 10-15 分钟，请耐心等待...)")
        
        max_wait = 1200  # 最大等待20分钟
        check_interval = 15  # 每15秒检查一次
        elapsed = 0
        last_status = None
        
        while elapsed < max_wait:
            time.sleep(check_interval)
            elapsed += check_interval
            
            try:
                status_response = requests.get(
                    f"{ETL_SERVICE_URL}/api/bulk-data/status/{job_id}",
                    timeout=60
                )
                
                if status_response.status_code == 200:
                    status = status_response.json()
                    current_status = status.get("status")
                    
                    # 只在状态变化时打印
                    if current_status != last_status:
                        print(f"\n   📊 状态更新: {current_status}")
                        last_status = current_status
                    
                    if current_status == "completed":
                        records_loaded = status.get("records_loaded", 0)
                        records_transformed = status.get("records_transformed", 0)
                        files = status.get("files_downloaded", 0)
                        
                        print(f"\n" + "="*70)
                        print(f"✅ 导出成功完成!")
                        print(f"="*70)
                        print(f"   已转换记录数: {records_transformed:,}")
                        print(f"   已加载记录数: {records_loaded:,}")
                        print(f"   下载文件数: {files}")
                        print(f"   总耗时: {elapsed/60:.1f} 分钟")
                        
                        return {
                            "job_id": job_id,
                            "success": True,
                            "records_loaded": records_loaded,
                            "records_transformed": records_transformed,
                            "files": files,
                            "elapsed_minutes": elapsed/60
                        }
                    
                    elif current_status == "failed":
                        error = status.get("error", "Unknown error")
                        print(f"\n❌ 任务失败: {error}")
                        return None
                    
                    elif current_status in ["downloading", "transforming", "loading"]:
                        # 显示详细进度
                        files_downloaded = status.get("files_downloaded", 0)
                        total_files = status.get("total_files", "?")
                        if files_downloaded > 0:
                            print(f"      文件进度: {files_downloaded}/{total_files}", end="\r")
                    else:
                        # 简单的进度指示
                        print(f".", end="", flush=True)
                
            except requests.exceptions.Timeout:
                print(f".", end="", flush=True)
                continue
            except Exception as e:
                print(f"\n   ⚠️  检查状态时出错: {e}")
                continue
        
        print(f"\n\n⚠️  等待超时 ({max_wait/60:.0f} 分钟)")
        print(f"   Job ID: {job_id} 可能仍在后台运行")
        return None
        
    except Exception as e:
        print(f"❌ 导出过程出错: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_database_stats():
    """检查数据库统计"""
    print(f"\n📊 步骤 3/3: 检查数据库统计...")
    
    import subprocess
    try:
        result = subprocess.run([
            "docker-compose", "exec", "-T", "postgres",
            "psql", "-U", "fhir_user", "-d", "fhir_analytics",
            "-c", "SELECT 'Patients' as table_name, COUNT(*) as count FROM patients UNION ALL SELECT 'Conditions', COUNT(*) FROM conditions UNION ALL SELECT 'Observations', COUNT(*) FROM observations UNION ALL SELECT 'Encounters', COUNT(*) FROM encounters;"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"   ⚠️  无法查询数据库")
    except Exception as e:
        print(f"   ⚠️  查询数据库时出错: {e}")

def main():
    """主函数"""
    print("\n" + "="*70)
    print("🏥 SMART Health IT 系统级别 Bulk Data 导出")
    print("   配置: 1000 个病人 (100% multiplier)")
    print("="*70)
    
    # 加载配置
    config = load_config()
    
    # 执行导出
    result = export_system_level(config)
    
    if result:
        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"export_system_full_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 导出结果已保存到: {output_file}")
    
    # 检查数据库
    check_database_stats()
    
    print("\n" + "="*70)
    print("✅ 程序执行完成")
    print("="*70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        exit(0)
    except Exception as e:
        print(f"\n\n❌ 程序出错: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

