#!/usr/bin/env python3
"""
解码和修改 SMART Health IT Bulk Data Server 配置
将 multiplier 从 10% 改为 100% 以获取完整数据
"""
import base64
import json

# 当前的 FHIR URL (从截图中获取)
current_url = "https://bulk-data.smarthealthit.org/eyJlcnIiOiIiLCJwYWdlIjoxMDAwMCwidGx0IjoxNSwibSI6MTAsImRlbCI6MCwic2VjdXJlIjoxLCJvcHAiOjMwfQ/fhir"

# 提取 base64 编码的部分
base64_part = current_url.split("/")[3]
print(f"📖 原始 Base64 配置: {base64_part}\n")

# 解码 (添加 padding 如果需要)
# Base64 需要长度是4的倍数
padding = len(base64_part) % 4
if padding:
    base64_part += '=' * (4 - padding)

decoded = base64.b64decode(base64_part).decode('utf-8')
config = json.loads(decoded)
print(f"🔍 当前配置:")
print(json.dumps(config, indent=2, ensure_ascii=False))
print()

# 修改 multiplier
old_m = config.get('m', 10)
config['m'] = 100  # 改为 100% (完整数据)
print(f"✏️  修改 multiplier: {old_m} → {config['m']}")
print()

# 重新编码
new_json = json.dumps(config, separators=(',', ':'), ensure_ascii=False)
new_base64 = base64.b64encode(new_json.encode('utf-8')).decode('utf-8')
new_url = f"https://bulk-data.smarthealthit.org/{new_base64}/fhir"

print(f"✅ 新的 FHIR Server URL:")
print(new_url)
print()

# 保存新配置
with open('config_full.json', 'w', encoding='utf-8') as f:
    # 从 config.json 读取完整配置
    try:
        with open('config.json', 'r', encoding='utf-8') as old_f:
            full_config = json.load(old_f)
        full_config['fhir_url'] = new_url
        json.dump(full_config, f, indent=2, ensure_ascii=False)
        print(f"💾 已保存新配置到: config_full.json")
        print()
        print(f"🎯 配置说明:")
        print(f"   • Database Size: 1,000 Patients (100%)")
        print(f"   • Multiplier (m): {config['m']}")
        print(f"   • Access Token Lifetime (tlt): {config.get('tlt', config.get('ttl', 15))} minutes")
        print(f"   • Page Size (page): {config['page']:,}")
        print(f"   • Secure: {'Yes' if config['secure'] else 'No'}")
    except FileNotFoundError:
        # 如果没有 config.json，只输出 URL
        print("⚠️  未找到 config.json，请手动更新 FHIR Server URL")

