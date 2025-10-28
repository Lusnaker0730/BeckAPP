"""
Password Validation Module
Implements strong password policies for HIPAA compliance and security best practices.
"""

import re
from typing import List, Tuple


class PasswordStrengthError(ValueError):
    """Exception raised for weak passwords"""
    pass


def validate_password_strength(password: str, min_length: int = 12) -> Tuple[bool, List[str]]:
    """
    Validate password strength against security requirements.
    
    Requirements:
    - Minimum length (default: 12 characters)
    - At least one uppercase letter (A-Z)
    - At least one lowercase letter (a-z)
    - At least one digit (0-9)
    - At least one special character (!@#$%^&*(),.?":{}|<>)
    - No common weak passwords
    
    Args:
        password: Password to validate
        min_length: Minimum required length (default: 12)
    
    Returns:
        Tuple of (is_valid: bool, errors: List[str])
    
    Examples:
        >>> validate_password_strength("Admin@123456")
        (True, [])
        >>> validate_password_strength("weak")
        (False, ['Password must be at least 12 characters long', ...])
    """
    errors = []
    
    # Check minimum length
    if len(password) < min_length:
        errors.append(f"Password must be at least {min_length} characters long")
    
    # Check for uppercase letter
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter (A-Z)")
    
    # Check for lowercase letter
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter (a-z)")
    
    # Check for digit
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one digit (0-9)")
    
    # Check for special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)")
    
    # Check for common weak passwords
    common_weak_passwords = [
        "password", "password123", "admin", "admin123", "12345678",
        "qwerty", "letmein", "welcome", "monkey", "dragon",
        "master", "sunshine", "princess", "football", "shadow",
        "abc123", "111111", "123123", "password1", "qwertyuiop"
    ]
    
    if password.lower() in common_weak_passwords:
        errors.append("Password is too common. Please choose a more unique password")
    
    # Check for sequential characters (like "123" or "abc")
    if re.search(r"(012|123|234|345|456|567|678|789|abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)", password.lower()):
        errors.append("Password should not contain sequential characters (e.g., '123', 'abc')")
    
    # Check for repeated characters (like "aaa" or "111")
    if re.search(r"(.)\1{2,}", password):
        errors.append("Password should not contain repeated characters (e.g., 'aaa', '111')")
    
    return (len(errors) == 0, errors)


def validate_password_or_raise(password: str, min_length: int = 12) -> None:
    """
    Validate password strength and raise exception if invalid.
    
    Args:
        password: Password to validate
        min_length: Minimum required length
    
    Raises:
        PasswordStrengthError: If password doesn't meet requirements
    """
    is_valid, errors = validate_password_strength(password, min_length)
    
    if not is_valid:
        error_message = "Password does not meet security requirements:\n" + "\n".join(f"  • {err}" for err in errors)
        raise PasswordStrengthError(error_message)


def get_password_strength_score(password: str) -> int:
    """
    Calculate password strength score (0-100).
    
    Scoring:
    - Length: +10 points per character (up to 50 points)
    - Uppercase: +10 points
    - Lowercase: +10 points
    - Digits: +10 points
    - Special chars: +10 points
    - Variety bonus: +10 points if all categories present
    
    Args:
        password: Password to score
    
    Returns:
        Score from 0-100
    """
    score = 0
    
    # Length score (up to 50 points)
    score += min(len(password) * 2, 50)
    
    # Character variety
    has_upper = bool(re.search(r"[A-Z]", password))
    has_lower = bool(re.search(r"[a-z]", password))
    has_digit = bool(re.search(r"\d", password))
    has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
    
    if has_upper:
        score += 10
    if has_lower:
        score += 10
    if has_digit:
        score += 10
    if has_special:
        score += 10
    
    # Bonus for having all categories
    if has_upper and has_lower and has_digit and has_special:
        score += 10
    
    return min(score, 100)


def get_password_strength_feedback(password: str) -> dict:
    """
    Get comprehensive password strength feedback.
    
    Args:
        password: Password to analyze
    
    Returns:
        Dictionary with score, is_valid, errors, and strength level
    """
    score = get_password_strength_score(password)
    is_valid, errors = validate_password_strength(password)
    
    # Determine strength level
    if score >= 80:
        strength = "strong"
    elif score >= 60:
        strength = "good"
    elif score >= 40:
        strength = "fair"
    else:
        strength = "weak"
    
    return {
        "score": score,
        "strength": strength,
        "is_valid": is_valid,
        "errors": errors,
        "length": len(password),
        "has_uppercase": bool(re.search(r"[A-Z]", password)),
        "has_lowercase": bool(re.search(r"[a-z]", password)),
        "has_digit": bool(re.search(r"\d", password)),
        "has_special": bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password)),
    }


# Example usage and testing
if __name__ == "__main__":
    test_passwords = [
        "weak",
        "Password123",
        "Admin@123456",
        "SuperSecure!Pass2023",
        "p@ssw0rd",
        "MyStr0ng!P@ssw0rd"
    ]
    
    print("Password Strength Testing")
    print("=" * 60)
    
    for pwd in test_passwords:
        feedback = get_password_strength_feedback(pwd)
        print(f"\nPassword: {pwd}")
        print(f"Score: {feedback['score']}/100")
        print(f"Strength: {feedback['strength']}")
        print(f"Valid: {feedback['is_valid']}")
        if feedback['errors']:
            print("Errors:")
            for error in feedback['errors']:
                print(f"  • {error}")

