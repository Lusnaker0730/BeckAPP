"""
Unit tests for password validation module.

Tests the password strength validation, scoring, and feedback system.
"""

import pytest
from app.core.password_validator import (
    validate_password_strength,
    validate_password_or_raise,
    get_password_strength_score,
    get_password_strength_feedback,
    PasswordStrengthError
)


class TestPasswordValidation:
    """Test password validation functions."""
    
    def test_valid_strong_password(self):
        """Test that a strong password passes validation."""
        password = "MySecure!Pass2024"
        is_valid, errors = validate_password_strength(password)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_password_too_short(self):
        """Test that short passwords are rejected."""
        password = "Short1!"
        is_valid, errors = validate_password_strength(password)
        
        assert is_valid is False
        assert any("12 characters" in error for error in errors)
    
    def test_password_no_uppercase(self):
        """Test that passwords without uppercase are rejected."""
        password = "nouppercase123!"
        is_valid, errors = validate_password_strength(password)
        
        assert is_valid is False
        assert any("uppercase" in error.lower() for error in errors)
    
    def test_password_no_lowercase(self):
        """Test that passwords without lowercase are rejected."""
        password = "NOLOWERCASE123!"
        is_valid, errors = validate_password_strength(password)
        
        assert is_valid is False
        assert any("lowercase" in error.lower() for error in errors)
    
    def test_password_no_digit(self):
        """Test that passwords without digits are rejected."""
        password = "NoDigitsHere!"
        is_valid, errors = validate_password_strength(password)
        
        assert is_valid is False
        assert any("digit" in error.lower() for error in errors)
    
    def test_password_no_special_char(self):
        """Test that passwords without special characters are rejected."""
        password = "NoSpecialChar123"
        is_valid, errors = validate_password_strength(password)
        
        assert is_valid is False
        assert any("special character" in error.lower() for error in errors)
    
    def test_common_weak_password(self):
        """Test that common weak passwords are rejected."""
        weak_passwords = ["password123", "admin", "12345678"]
        
        for password in weak_passwords:
            is_valid, errors = validate_password_strength(password)
            assert is_valid is False
    
    def test_sequential_characters(self):
        """Test that passwords with sequential characters are rejected."""
        password = "Abc123!Password"
        is_valid, errors = validate_password_strength(password)
        
        assert is_valid is False
        assert any("sequential" in error.lower() for error in errors)
    
    def test_repeated_characters(self):
        """Test that passwords with repeated characters are rejected."""
        password = "Aaa123!Password"
        is_valid, errors = validate_password_strength(password)
        
        assert is_valid is False
        assert any("repeated" in error.lower() for error in errors)
    
    def test_validate_or_raise_success(self):
        """Test that validate_or_raise doesn't raise for valid passwords."""
        password = "MySecure!Pass2024"
        # Should not raise
        validate_password_or_raise(password)
    
    def test_validate_or_raise_failure(self):
        """Test that validate_or_raise raises for invalid passwords."""
        password = "weak"
        
        with pytest.raises(PasswordStrengthError) as exc_info:
            validate_password_or_raise(password)
        
        assert "security requirements" in str(exc_info.value)


class TestPasswordScoring:
    """Test password strength scoring system."""
    
    def test_score_very_weak_password(self):
        """Test scoring for very weak password."""
        password = "abc"
        score = get_password_strength_score(password)
        
        assert score < 40
    
    def test_score_weak_password(self):
        """Test scoring for weak password."""
        password = "password1"
        score = get_password_strength_score(password)
        
        assert 20 <= score < 60
    
    def test_score_good_password(self):
        """Test scoring for good password."""
        password = "GoodPass123!"
        score = get_password_strength_score(password)
        
        assert 60 <= score < 80
    
    def test_score_strong_password(self):
        """Test scoring for strong password."""
        password = "VeryStr0ng!P@ssw0rd2024"
        score = get_password_strength_score(password)
        
        assert score >= 80
    
    def test_score_increases_with_length(self):
        """Test that score increases with password length."""
        short_password = "Test123!"
        long_password = "Test123!LongerPassword"
        
        short_score = get_password_strength_score(short_password)
        long_score = get_password_strength_score(long_password)
        
        assert long_score > short_score
    
    def test_score_increases_with_variety(self):
        """Test that score increases with character variety."""
        simple_password = "testpassword"
        complex_password = "Test123!Pass"
        
        simple_score = get_password_strength_score(simple_password)
        complex_score = get_password_strength_score(complex_password)
        
        assert complex_score > simple_score


class TestPasswordFeedback:
    """Test password strength feedback system."""
    
    def test_feedback_structure(self):
        """Test that feedback contains all expected fields."""
        password = "TestPass123!"
        feedback = get_password_strength_feedback(password)
        
        assert "score" in feedback
        assert "strength" in feedback
        assert "is_valid" in feedback
        assert "errors" in feedback
        assert "length" in feedback
        assert "has_uppercase" in feedback
        assert "has_lowercase" in feedback
        assert "has_digit" in feedback
        assert "has_special" in feedback
    
    def test_feedback_strength_levels(self):
        """Test that feedback correctly categorizes strength levels."""
        weak = get_password_strength_feedback("weak")
        assert weak["strength"] == "weak"
        
        fair = get_password_strength_feedback("Fair123Pass")
        assert fair["strength"] in ["fair", "good"]
        
        strong = get_password_strength_feedback("VeryStr0ng!P@ssw0rd")
        assert strong["strength"] in ["good", "strong"]
    
    def test_feedback_character_detection(self):
        """Test that feedback correctly detects character types."""
        password = "Test123!"
        feedback = get_password_strength_feedback(password)
        
        assert feedback["has_uppercase"] is True
        assert feedback["has_lowercase"] is True
        assert feedback["has_digit"] is True
        assert feedback["has_special"] is True
    
    def test_feedback_errors_for_weak_password(self):
        """Test that feedback includes errors for weak passwords."""
        password = "weak"
        feedback = get_password_strength_feedback(password)
        
        assert feedback["is_valid"] is False
        assert len(feedback["errors"]) > 0
    
    def test_feedback_no_errors_for_strong_password(self):
        """Test that feedback has no errors for strong passwords."""
        password = "MySecure!Pass2024"
        feedback = get_password_strength_feedback(password)
        
        assert feedback["is_valid"] is True
        assert len(feedback["errors"]) == 0


class TestCustomMinLength:
    """Test custom minimum length validation."""
    
    def test_custom_min_length_pass(self):
        """Test validation with custom min length that passes."""
        password = "Short1!"  # 7 characters
        is_valid, errors = validate_password_strength(password, min_length=6)
        
        # Should still fail for other reasons, but not length
        assert not any("12 characters" in error for error in errors)
    
    def test_custom_min_length_fail(self):
        """Test validation with custom min length that fails."""
        password = "Test1!"  # 6 characters
        is_valid, errors = validate_password_strength(password, min_length=8)
        
        assert any("8 characters" in error for error in errors)


# Parametrized tests for comprehensive coverage
@pytest.mark.parametrize("password,expected_valid", [
    ("MySecure!Pass2024", True),
    ("Admin@2024Secure", True),
    ("Engineering#Pwd123!", True),
    ("weak", False),
    ("password", False),
    ("12345678", False),
    ("NoDigits!", False),
    ("nospecial123", False),
    ("NOLOWERCASE123!", False),
])
def test_various_passwords(password, expected_valid):
    """Test various password combinations."""
    is_valid, _ = validate_password_strength(password)
    assert is_valid == expected_valid

