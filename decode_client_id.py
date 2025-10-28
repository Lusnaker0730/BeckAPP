#!/usr/bin/env python3
"""
解码 client_id JWT token
"""

import json
import jwt
import base64

# 加载配置
with open("Keys.json", "r", encoding="utf-8") as f:
    config = json.load(f)

client_id_jwt = config["client id"]

print("="*70)
print("🔍 解码 Client ID JWT Token")
print("="*70)

print(f"\nClient ID (JWT): {client_id_jwt[:80]}...")

# 尝试解码（不验证签名）
try:
    # 解码 header
    header = jwt.get_unverified_header(client_id_jwt)
    print(f"\n📋 JWT Header:")
    print(json.dumps(header, indent=2))
    
    # 解码 payload
    payload = jwt.decode(client_id_jwt, options={"verify_signature": False})
    print(f"\n📋 JWT Payload:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    # 检查是否有实际的 client_id
    if "sub" in payload:
        print(f"\n💡 发现 'sub' 字段，可能这才是真正的 client_id")
        print(f"   sub: {payload['sub']}")
    
    if "client_id" in payload:
        print(f"\n💡 发现 'client_id' 字段")
        print(f"   client_id: {payload['client_id']}")
    
    if "jwks" in payload:
        print(f"\n💡 发现 'jwks' 字段，这个 token 包含公钥信息")
        print(f"   jwks keys count: {len(payload['jwks'].get('keys', []))}")
    
except Exception as e:
    print(f"\n❌ 解码失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)

