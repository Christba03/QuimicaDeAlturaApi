import hashlib
import re
from typing import Optional

import structlog

logger = structlog.get_logger()


def generate_device_fingerprint(
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
    accept_language: Optional[str] = None,
) -> str:
    """
    Generate a device fingerprint from browser/device characteristics.
    
    Args:
        user_agent: Browser user agent string
        ip_address: Client IP address (optional, for additional uniqueness)
        accept_language: Accept-Language header value
    
    Returns:
        SHA256 hash of device characteristics
    """
    # Normalize user agent (remove version numbers for stability)
    normalized_ua = ""
    if user_agent:
        # Remove version numbers but keep browser/OS info
        normalized_ua = re.sub(r'/\d+\.\d+', '', user_agent)
        normalized_ua = re.sub(r'\s+', ' ', normalized_ua).strip()
    
    # Create fingerprint data
    fingerprint_data = f"{normalized_ua}:{accept_language or ''}"
    
    # Hash the fingerprint
    fingerprint_hash = hashlib.sha256(fingerprint_data.encode()).hexdigest()
    
    logger.debug("device_fingerprint.generated", fingerprint=fingerprint_hash[:16])
    return fingerprint_hash


def detect_device_type(user_agent: Optional[str] = None) -> str:
    """
    Detect device type from user agent.
    
    Returns:
        Device type: 'mobile', 'tablet', 'desktop', or 'unknown'
    """
    if not user_agent:
        return "unknown"
    
    user_agent_lower = user_agent.lower()
    
    # Mobile devices
    mobile_patterns = [
        'mobile', 'android', 'iphone', 'ipod', 'blackberry',
        'windows phone', 'opera mini', 'iemobile'
    ]
    
    # Tablets
    tablet_patterns = [
        'tablet', 'ipad', 'playbook', 'kindle', 'silk'
    ]
    
    for pattern in tablet_patterns:
        if pattern in user_agent_lower:
            return "tablet"
    
    for pattern in mobile_patterns:
        if pattern in user_agent_lower:
            return "mobile"
    
    return "desktop"


def extract_device_name(user_agent: Optional[str] = None) -> str:
    """
    Extract a user-friendly device name from user agent.
    
    Returns:
        Device name like "Chrome on Windows" or "Safari on iPhone"
    """
    if not user_agent:
        return "Unknown Device"
    
    # Try to extract browser and OS
    browser = "Unknown Browser"
    os_name = "Unknown OS"
    
    # Browser detection
    if "chrome" in user_agent.lower() and "edg" not in user_agent.lower():
        browser = "Chrome"
    elif "firefox" in user_agent.lower():
        browser = "Firefox"
    elif "safari" in user_agent.lower() and "chrome" not in user_agent.lower():
        browser = "Safari"
    elif "edg" in user_agent.lower():
        browser = "Edge"
    elif "opera" in user_agent.lower():
        browser = "Opera"
    
    # OS detection
    if "windows" in user_agent.lower():
        os_name = "Windows"
    elif "mac" in user_agent.lower() or "macintosh" in user_agent.lower():
        os_name = "macOS"
    elif "linux" in user_agent.lower():
        os_name = "Linux"
    elif "android" in user_agent.lower():
        os_name = "Android"
    elif "iphone" in user_agent.lower() or "ipad" in user_agent.lower():
        os_name = "iOS"
    
    device_type = detect_device_type(user_agent)
    
    if device_type == "mobile":
        return f"{browser} on {os_name} Mobile"
    elif device_type == "tablet":
        return f"{browser} on {os_name} Tablet"
    else:
        return f"{browser} on {os_name}"
