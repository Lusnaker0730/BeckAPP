"""
SMART Backend Services Authentication Module

Implements OAuth 2.0 Backend Services authorization for FHIR Bulk Data API
Reference: https://hl7.org/fhir/smart-app-launch/backend-services.html
"""

import jwt
import uuid
import time
import httpx
import json
import logging
import base64
from typing import Optional, Dict, Union
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers, RSAPrivateNumbers

logger = logging.getLogger(__name__)


class SMARTBackendAuth:
    """
    SMART Backend Services authentication handler
    
    Supports:
    - RS384 (RSA with SHA-384)
    - ES384 (ECDSA with P-384 and SHA-384)
    """
    
    def __init__(
        self,
        token_url: str,
        client_id: str,
        private_key: str,
        jwks_url: Optional[str] = None,
        algorithm: str = "RS384"
    ):
        """
        Initialize SMART Backend Services authentication
        
        Args:
            token_url: OAuth 2.0 token endpoint
            client_id: Client identifier (registered with FHIR server)
            private_key: Private key (PEM format or JWK JSON string) for signing JWT
            jwks_url: JWKS URL (public key set URL) - optional, server may use this
            algorithm: JWT signing algorithm (RS384 or ES384)
        """
        self.token_url = token_url
        self.client_id = client_id
        self.jwks_url = jwks_url
        self.algorithm = algorithm
        self.access_token = None
        self.token_expiry = None
        
        # Process private key (support both PEM and JWK formats)
        self.jwk_data = self._process_private_key(private_key)
        
        # Extract kid (Key ID) from JWK if available
        self.kid = None
        if isinstance(self.jwk_data, dict):
            self.kid = self.jwk_data.get('kid')
            logger.info(f"📝 Key ID (kid): {self.kid}")
        
        # Convert to PEM format for signing
        self.private_key = self._to_pem_format(self.jwk_data)
        
        logger.info(f"✅ Private key loaded successfully ({algorithm})")
    
    def _process_private_key(self, private_key: str):
        """
        Process private key - supports both PEM and JWK formats
        
        Args:
            private_key: Private key as PEM string or JWK JSON string/dict
            
        Returns:
            Private key in format suitable for PyJWT (PEM string or dict)
        """
        try:
            # Check if it's a JSON string (JWK format)
            if isinstance(private_key, str) and (private_key.strip().startswith('{') or private_key.strip().startswith('[')):
                try:
                    jwk_data = json.loads(private_key)
                    logger.info("🔑 Detected JWK format private key")
                    
                    # If it's a dict with 'keys' array, extract the signing key
                    if isinstance(jwk_data, dict) and 'keys' in jwk_data:
                        keys = jwk_data['keys']
                        # Find the key with 'sign' operation
                        for key in keys:
                            if 'sign' in key.get('key_ops', []):
                                logger.info(f"🔑 Found signing key with kid: {key.get('kid')}")
                                return key
                        raise ValueError("No signing key found in JWK set")
                    
                    # If it's already a single JWK
                    elif isinstance(jwk_data, dict) and 'kty' in jwk_data:
                        return jwk_data
                    
                    else:
                        raise ValueError("Invalid JWK format")
                
                except json.JSONDecodeError:
                    # Not JSON, treat as PEM
                    logger.info("🔑 Detected PEM format private key")
                    return private_key
            
            elif isinstance(private_key, dict):
                # Already a JWK dict
                logger.info("🔑 Received JWK dict format private key")
                return private_key
            
            else:
                # Assume PEM format
                logger.info("🔑 Assuming PEM format private key")
                return private_key
                
        except Exception as e:
            logger.error(f"Failed to process private key: {e}")
            raise
    
    def _base64_to_int(self, b64_string: str) -> int:
        """Convert base64url encoded string to integer"""
        # Add padding if needed
        missing_padding = len(b64_string) % 4
        if missing_padding:
            b64_string += '=' * (4 - missing_padding)
        
        # Replace URL-safe characters
        b64_string = b64_string.replace('-', '+').replace('_', '/')
        
        # Decode and convert to int
        decoded = base64.b64decode(b64_string)
        return int.from_bytes(decoded, byteorder='big')
    
    def _jwk_to_rsa_key(self, jwk: Dict) -> rsa.RSAPrivateKey:
        """
        Convert JWK to RSA private key object
        
        Args:
            jwk: JWK dictionary with RSA key components
            
        Returns:
            RSAPrivateKey object
        """
        try:
            # Extract key components
            n = self._base64_to_int(jwk['n'])
            e = self._base64_to_int(jwk['e'])
            d = self._base64_to_int(jwk['d'])
            p = self._base64_to_int(jwk['p'])
            q = self._base64_to_int(jwk['q'])
            
            # Calculate additional parameters
            dmp1 = self._base64_to_int(jwk.get('dp', '')) if 'dp' in jwk else rsa.rsa_crt_dmp1(d, p)
            dmq1 = self._base64_to_int(jwk.get('dq', '')) if 'dq' in jwk else rsa.rsa_crt_dmq1(d, q)
            iqmp = self._base64_to_int(jwk.get('qi', '')) if 'qi' in jwk else rsa.rsa_crt_iqmp(p, q)
            
            # Create public numbers
            public_numbers = RSAPublicNumbers(e, n)
            
            # Create private numbers
            private_numbers = RSAPrivateNumbers(
                p=p,
                q=q,
                d=d,
                dmp1=dmp1,
                dmq1=dmq1,
                iqmp=iqmp,
                public_numbers=public_numbers
            )
            
            # Generate private key
            private_key = private_numbers.private_key(default_backend())
            
            logger.info("✅ Successfully converted JWK to RSA private key")
            return private_key
            
        except Exception as e:
            logger.error(f"Failed to convert JWK to RSA key: {e}")
            raise
    
    def _to_pem_format(self, key_data: Union[str, Dict]) -> str:
        """
        Convert key to PEM format string
        
        Args:
            key_data: Either a PEM string or JWK dict
            
        Returns:
            PEM-formatted private key string
        """
        try:
            # If already a PEM string, return as is
            if isinstance(key_data, str):
                if key_data.startswith('-----BEGIN'):
                    logger.info("Key is already in PEM format")
                    return key_data
                else:
                    raise ValueError("String key is not in PEM format")
            
            # If it's a JWK dict, convert to PEM
            if isinstance(key_data, dict):
                if key_data.get('kty') == 'RSA':
                    logger.info("Converting JWK to PEM format")
                    
                    # Validate required fields
                    required_fields = ['kty', 'n', 'e', 'd', 'p', 'q']
                    for field in required_fields:
                        if field not in key_data:
                            raise ValueError(f"JWK missing required field: {field}")
                    
                    logger.info("✅ JWK key structure validated")
                    
                    # Convert JWK to RSA key object
                    private_key_obj = self._jwk_to_rsa_key(key_data)
                    
                    # Serialize to PEM format
                    pem_bytes = private_key_obj.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption()
                    )
                    
                    pem_string = pem_bytes.decode('utf-8')
                    logger.info("✅ Successfully converted JWK to PEM format")
                    
                    return pem_string
                else:
                    raise ValueError(f"Unsupported key type: {key_data.get('kty')}")
            
            raise ValueError("Invalid key format")
            
        except Exception as e:
            logger.error(f"Failed to convert key to PEM format: {e}")
            raise
    
    def create_jwt_assertion(self, expires_in: int = 300) -> str:
        """
        Create JWT assertion for authentication
        
        Args:
            expires_in: JWT expiration time in seconds (default: 5 minutes)
        
        Returns:
            Signed JWT assertion string
        """
        now = int(time.time())
        
        # JWT Header - include kid if available
        header = {
            "alg": self.algorithm,
            "typ": "JWT"
        }
        
        # Add kid (Key ID) to header if available (required by some servers)
        if self.kid:
            header["kid"] = self.kid
            logger.debug(f"Including kid in JWT header: {self.kid}")
        
        # JWT Claims
        claims = {
            "iss": self.client_id,  # Issuer (client_id)
            "sub": self.client_id,  # Subject (client_id)
            "aud": self.token_url,  # Audience (token endpoint)
            "exp": now + expires_in,  # Expiration time
            "iat": now,  # Issued at
            "jti": str(uuid.uuid4())  # Unique identifier
        }
        
        # Sign JWT with private key
        try:
            encoded_jwt = jwt.encode(
                claims,
                self.private_key,
                algorithm=self.algorithm,
                headers=header
            )
            
            logger.debug(f"Created JWT assertion with header: {header}")
            logger.debug(f"Claims: {claims}")
            return encoded_jwt
            
        except Exception as e:
            logger.error(f"Failed to create JWT assertion: {e}")
            raise
    
    async def get_access_token(self, scope: str = "system/*.read") -> str:
        """
        Get access token using Backend Services flow
        
        Args:
            scope: OAuth 2.0 scope (e.g., "system/*.read")
        
        Returns:
            Access token string
        """
        # Check if we have a valid cached token
        if self.access_token and self.token_expiry:
            if datetime.now() < self.token_expiry - timedelta(seconds=60):
                logger.debug("Using cached access token")
                return self.access_token
        
        # Create JWT assertion
        jwt_assertion = self.create_jwt_assertion()
        
        # Prepare token request
        data = {
            "grant_type": "client_credentials",
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": jwt_assertion,
            "scope": scope
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.info(f"Requesting access token from {self.token_url}")
                
                response = await client.post(
                    self.token_url,
                    data=data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    
                    self.access_token = token_data.get("access_token")
                    expires_in = token_data.get("expires_in", 300)
                    self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
                    
                    logger.info(f"✅ Access token obtained (expires in {expires_in}s)")
                    logger.debug(f"Token type: {token_data.get('token_type')}")
                    logger.debug(f"Scope: {token_data.get('scope')}")
                    
                    return self.access_token
                else:
                    error_body = response.text
                    logger.error(f"Token request failed: {response.status_code}")
                    logger.error(f"Response: {error_body}")
                    
                    raise Exception(
                        f"Failed to get access token: {response.status_code} - {error_body}"
                    )
        
        except httpx.RequestError as e:
            logger.error(f"Network error requesting token: {e}")
            raise Exception(f"Network error: {e}")
    
    async def get_auth_header(self, scope: str = "system/*.read") -> Dict[str, str]:
        """
        Get authentication header with Bearer token
        
        Args:
            scope: OAuth 2.0 scope
        
        Returns:
            Dictionary with Authorization header
        """
        token = await self.get_access_token(scope)
        return {"Authorization": f"Bearer {token}"}


def create_jwks_from_private_key(private_key_pem: str, algorithm: str = "RS384") -> Dict:
    """
    Generate JWKS (JSON Web Key Set) from private key
    
    Args:
        private_key_pem: Private key in PEM format
        algorithm: Algorithm (RS384 or ES384)
    
    Returns:
        JWKS dictionary (for publishing public key)
    """
    try:
        # Load private key
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None,
            backend=default_backend()
        )
        
        # Get public key
        public_key = private_key.public_key()
        
        # Serialize public key for JWKS
        if algorithm.startswith("RS"):
            # RSA key
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
            import base64
            
            if not isinstance(public_key, rsa.RSAPublicKey):
                raise ValueError("Public key is not RSA")
            
            # Get public numbers
            public_numbers = public_key.public_numbers()
            
            # Convert to base64url
            def int_to_base64url(n):
                # Convert integer to bytes
                byte_length = (n.bit_length() + 7) // 8
                n_bytes = n.to_bytes(byte_length, byteorder='big')
                # Base64url encode
                return base64.urlsafe_b64encode(n_bytes).decode('utf-8').rstrip('=')
            
            jwk = {
                "kty": "RSA",
                "alg": algorithm,
                "use": "sig",
                "kid": str(uuid.uuid4()),
                "n": int_to_base64url(public_numbers.n),
                "e": int_to_base64url(public_numbers.e)
            }
            
        elif algorithm.startswith("ES"):
            # ECDSA key
            from cryptography.hazmat.primitives.asymmetric import ec
            import base64
            
            if not isinstance(public_key, ec.EllipticCurvePublicKey):
                raise ValueError("Public key is not EC")
            
            # Get public numbers
            public_numbers = public_key.public_numbers()
            
            # Determine curve
            curve_name = public_key.curve.name
            if curve_name == "secp384r1":
                crv = "P-384"
            elif curve_name == "secp256r1":
                crv = "P-256"
            else:
                crv = curve_name
            
            # Convert to base64url
            def int_to_base64url(n, byte_length):
                n_bytes = n.to_bytes(byte_length, byteorder='big')
                return base64.urlsafe_b64encode(n_bytes).decode('utf-8').rstrip('=')
            
            # P-384 uses 48 bytes for each coordinate
            byte_length = 48 if crv == "P-384" else 32
            
            jwk = {
                "kty": "EC",
                "alg": algorithm,
                "use": "sig",
                "kid": str(uuid.uuid4()),
                "crv": crv,
                "x": int_to_base64url(public_numbers.x, byte_length),
                "y": int_to_base64url(public_numbers.y, byte_length)
            }
        
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        # Return JWKS
        jwks = {
            "keys": [jwk]
        }
        
        return jwks
        
    except Exception as e:
        logger.error(f"Failed to create JWKS: {e}")
        raise


def extract_public_key_from_private(private_key_pem: str) -> str:
    """
    Extract public key from private key
    
    Args:
        private_key_pem: Private key in PEM format
    
    Returns:
        Public key in PEM format
    """
    try:
        # Load private key
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None,
            backend=default_backend()
        )
        
        # Get public key
        public_key = private_key.public_key()
        
        # Serialize to PEM
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return public_pem.decode('utf-8')
        
    except Exception as e:
        logger.error(f"Failed to extract public key: {e}")
        raise

