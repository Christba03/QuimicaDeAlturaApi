import re
from typing import Tuple

import structlog
from zxcvbn import zxcvbn

from src.config import settings

logger = structlog.get_logger()


class PasswordValidationError(Exception):
    """Exception raised when password validation fails."""
    pass


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password meets security requirements.
    
    Returns:
        tuple[bool, str]: (is_valid, error_message)
        If valid, error_message is empty string.
    """
    # Check minimum length
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long"

    # Check for uppercase letter
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"

    # Check for lowercase letter
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"

    # Check for number
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"

    # Check for special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>\[\]\\/_+\-=~`]', password):
        return False, "Password must contain at least one special character"

    # Check password strength using zxcvbn
    try:
        result = zxcvbn(password)
        strength_score = result['score']  # 0-4 scale
        
        if strength_score < settings.PASSWORD_MIN_STRENGTH_SCORE:
            feedback = result.get('feedback', {})
            suggestions = feedback.get('suggestions', [])
            
            if suggestions:
                suggestion_text = suggestions[0] if suggestions else "Choose a stronger password"
            else:
                suggestion_text = "Password is too weak. Try adding more complexity or length."
            
            return False, f"Password is too weak. {suggestion_text}"
        
        logger.debug(
            "password.validated",
            strength_score=strength_score,
            crack_time=result.get('crack_times_display', {}).get('offline_slow_hashing_1e4_per_second', 'N/A'),
        )
        
        return True, ""
    except Exception as e:
        logger.error("password.validation_error", error=str(e))
        # Fallback to basic validation if zxcvbn fails
        return True, ""


def validate_password(password: str) -> None:
    """
    Validate password and raise exception if invalid.
    
    Raises:
        PasswordValidationError: If password doesn't meet requirements
    """
    is_valid, error_message = validate_password_strength(password)
    if not is_valid:
        raise PasswordValidationError(error_message)
