"""
Unit tests for security module.

Tests password hashing, token generation, and JWT validation.
"""

import pytest
from datetime import timedelta
from jose import jwt, JWTError

from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    verify_token
)
from app.core.config import settings


class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_hash_password(self):
        """Test that passwords are properly hashed."""
        password = "TestPass123!"
        hashed = get_password_hash(password)
        
        # Hash should be different from original
        assert hashed != password
        # Hash should be a string
        assert isinstance(hashed, str)
        # Hash should have reasonable length
        assert len(hashed) > 50
    
    def test_verify_correct_password(self):
        """Test that correct password verification works."""
        password = "TestPass123!"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_incorrect_password(self):
        """Test that incorrect password verification fails."""
        password = "TestPass123!"
        wrong_password = "WrongPass456!"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes (salt)."""
        password = "TestPass123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Different hashes
        assert hash1 != hash2
        # But both verify correctly
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


class TestTokenGeneration:
    """Test JWT token generation and validation."""
    
    def test_create_access_token(self):
        """Test that access token is created correctly."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_token_with_expiry(self):
        """Test token creation with custom expiry."""
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=15)
        token = create_access_token(data, expires_delta=expires_delta)
        
        # Decode token to check expiry
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        assert "exp" in payload
    
    def test_token_contains_user_data(self):
        """Test that token contains user data."""
        data = {"sub": "testuser", "role": "admin"}
        token = create_access_token(data)
        
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        assert payload["sub"] == "testuser"
        assert payload["role"] == "admin"
    
    def test_verify_valid_token(self):
        """Test verification of valid token."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "testuser"
    
    def test_verify_invalid_token(self):
        """Test verification of invalid token."""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(JWTError):
            verify_token(invalid_token)
    
    def test_verify_expired_token(self):
        """Test verification of expired token."""
        data = {"sub": "testuser"}
        # Create token that expires immediately
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        
        with pytest.raises(JWTError):
            verify_token(token)
    
    def test_token_with_additional_claims(self):
        """Test token with additional claims."""
        data = {
            "sub": "testuser",
            "email": "test@example.com",
            "role": "user",
            "permissions": ["read", "write"]
        }
        token = create_access_token(data)
        
        payload = verify_token(token)
        assert payload["email"] == "test@example.com"
        assert payload["role"] == "user"
        assert payload["permissions"] == ["read", "write"]


class TestSecurityHelpers:
    """Test security helper functions."""
    
    def test_password_hash_is_bcrypt(self):
        """Test that password hash uses bcrypt."""
        password = "TestPass123!"
        hashed = get_password_hash(password)
        
        # Bcrypt hashes start with $2b$
        assert hashed.startswith("$2b$")
    
    def test_empty_password_hash(self):
        """Test hashing empty password."""
        password = ""
        hashed = get_password_hash(password)
        
        # Should still produce a hash
        assert isinstance(hashed, str)
        assert len(hashed) > 0
    
    def test_very_long_password(self):
        """Test hashing very long password."""
        password = "A" * 1000 + "1!"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed)
    
    def test_special_characters_in_password(self):
        """Test password with special characters."""
        password = "T€st!@#$%^&*()_+-=[]{}|;':\",./<>?`~"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed)

