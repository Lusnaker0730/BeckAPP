#!/usr/bin/env python3
"""快速测试 m=50 配置"""
import base64
import json

# 创建 m=50 的配置
config_m50 = {
    "err": "",
    "page": 10000,
    "tlt": 15,
    "m": 50,  # 50% = 500 个病人
    "del": 0,
    "secure": 1,
    "opp": 30
}

# 编码
new_json = json.dumps(config_m50, separators=(',', ':'))
new_base64 = base64.b64encode(new_json.encode('utf-8')).decode('utf-8')
new_url = f"https://bulk-data.smarthealthit.org/{new_base64}/fhir"

print("🔧 测试配置 m=50 (500 个病人)")
print(f"\n新 FHIR URL:")
print(new_url)

# 加载并更新完整配置
try:
    with open('config.json', 'r', encoding='utf-8') as f:
        full_config = json.load(f)
    
    full_config['fhir_url'] = new_url
    
    with open('config_m50.json', 'w', encoding='utf-8') as f:
        json.dump(full_config, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 已保存到: config_m50.json")
    print(f"\n📊 配置详情:")
    print(f"   • Database Size: 500 Patients (50%)")
    print(f"   • Multiplier (m): 50")
except Exception as e:
    print(f"\n❌ 错误: {e}")

