#!/usr/bin/env python3
"""
测试 SMART Health IT 认证
"""

import json
import requests
import jwt
import time
import uuid
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers, RSAPrivateNumbers
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import base64

# 加载配置
with open("Keys.json", "r", encoding="utf-8") as f:
    config = json.load(f)

token_url = config["token"]
client_id = config["client id"]
jwk_key = None

# 找到签名密钥
for key in config["keys"]:
    if "sign" in key.get("key_ops", []):
        jwk_key = key
        break

print("="*70)
print("🔍 SMART Health IT 认证测试")
print("="*70)
print(f"\n📋 配置信息:")
print(f"Token URL: {token_url}")
print(f"Client ID (前50字符): {client_id[:50]}...")
print(f"Key ID: {jwk_key.get('kid')}")

# 函数：base64url 转整数
def base64_to_int(b64_string):
    missing_padding = len(b64_string) % 4
    if missing_padding:
        b64_string += '=' * (4 - missing_padding)
    b64_string = b64_string.replace('-', '+').replace('_', '/')
    decoded = base64.b64decode(b64_string)
    return int.from_bytes(decoded, byteorder='big')

# 转换 JWK 到 RSA 私钥
def jwk_to_rsa_key(jwk):
    n = base64_to_int(jwk['n'])
    e = base64_to_int(jwk['e'])
    d = base64_to_int(jwk['d'])
    p = base64_to_int(jwk['p'])
    q = base64_to_int(jwk['q'])
    dmp1 = base64_to_int(jwk['dp'])
    dmq1 = base64_to_int(jwk['dq'])
    iqmp = base64_to_int(jwk['qi'])
    
    public_numbers = RSAPublicNumbers(e, n)
    private_numbers = RSAPrivateNumbers(
        p=p, q=q, d=d,
        dmp1=dmp1, dmq1=dmq1, iqmp=iqmp,
        public_numbers=public_numbers
    )
    
    return private_numbers.private_key(default_backend())

# 转换密钥
print("\n🔑 转换 JWK 到 PEM...")
try:
    private_key_obj = jwk_to_rsa_key(jwk_key)
    private_key_pem = private_key_obj.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    print("✅ 密钥转换成功")
except Exception as e:
    print(f"❌ 密钥转换失败: {e}")
    exit(1)

# 创建 JWT Assertion
print("\n📝 创建 JWT Assertion...")
now = int(time.time())

header = {
    "alg": "RS384",
    "typ": "JWT",
    "kid": jwk_key['kid']
}

payload = {
    "iss": client_id,
    "sub": client_id,
    "aud": token_url,
    "exp": now + 300,
    "iat": now,
    "jti": str(uuid.uuid4())
}

try:
    jwt_assertion = jwt.encode(
        payload,
        private_key_pem,
        algorithm="RS384",
        headers=header
    )
    print("✅ JWT Assertion 创建成功")
    print(f"   Header: {header}")
    print(f"   Payload iss: {payload['iss'][:50]}...")
    print(f"   Payload sub: {payload['sub'][:50]}...")
    print(f"   JWT (前100字符): {jwt_assertion[:100]}...")
except Exception as e:
    print(f"❌ JWT 创建失败: {e}")
    exit(1)

# 请求 Access Token
print("\n🚀 请求 Access Token...")
data = {
    "grant_type": "client_credentials",
    "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
    "client_assertion": jwt_assertion,
    "scope": "system/*.read"
}

headers_req = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json"
}

try:
    response = requests.post(
        token_url,
        data=data,
        headers=headers_req,
        timeout=30
    )
    
    print(f"\n📊 响应状态: {response.status_code}")
    print(f"📊 响应 Headers:")
    for key, value in response.headers.items():
        print(f"   {key}: {value}")
    
    print(f"\n📊 响应内容:")
    try:
        response_json = response.json()
        print(json.dumps(response_json, indent=2))
        
        if response.status_code == 200:
            print("\n✅ 认证成功!")
            print(f"Access Token (前50字符): {response_json.get('access_token', '')[:50]}...")
            print(f"Token Type: {response_json.get('token_type')}")
            print(f"Expires In: {response_json.get('expires_in')}s")
            print(f"Scope: {response_json.get('scope')}")
        else:
            print("\n❌ 认证失败!")
            print(f"错误: {response_json.get('error')}")
            print(f"错误描述: {response_json.get('error_description')}")
    except:
        print(response.text)
        
except Exception as e:
    print(f"❌ 请求失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)

