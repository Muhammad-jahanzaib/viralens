"""
Security utilities for VIRALENS
Handles input sanitization, validation, and security checks
"""

import re
import html
from typing import Optional


def sanitize_text(text: str, max_length: int = 500) -> str:
    """
    Generic text sanitization - removes dangerous characters
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text string
    """
    if not text:
        return ""
    
    # HTML escape to prevent XSS
    text = html.escape(text)
    
    # Remove null bytes and control characters
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Trim and limit length
    return text.strip()[:max_length]


def sanitize_keyword(keyword: str) -> str:
    """
    Sanitize keyword while allowing useful special characters.
    
    Allows:
    - Alphanumeric (a-z, A-Z, 0-9)
    - Spaces
    - Common punctuation (- _ . , ! ? # & + @)
    - Emojis and unicode characters
    
    Blocks:
    - SQL injection patterns (', ", --, ;)
    - XSS patterns (<, >, script)
    
    Returns:
        Sanitized keyword or empty string if invalid
    """
    if not keyword:
        return ""
    
    # Check for dangerous SQL injection patterns first
    dangerous_sql = [
        r"('\s*OR\s+'[^']*'\s*=\s*'[^']*)",  # ' OR '1'='1
        r"(\"\s*OR\s+\"[^\"]*\"\s*=\s*\"[^\"]*)",  # " OR "1"="1
        r"(--\s*)",                    # SQL comments
        r"(;\s*DROP\s+TABLE)",         # DROP TABLE
        r"(;\s*DELETE\s+FROM)",        # DELETE FROM
        r"(UNION\s+SELECT)",           # UNION SELECT
    ]
    
    for pattern in dangerous_sql:
        if re.search(pattern, keyword, re.IGNORECASE):
            return ""  # Block entirely if SQL injection detected
    
    # Check for XSS patterns
    dangerous_xss = [
        r"<script[^>]*>",              # <script> tags
        r"javascript:",                # javascript: protocol
        r"onerror\s*=",                # onerror= attribute
        r"onload\s*=",                 # onload= attribute
    ]
    
    for pattern in dangerous_xss:
        if re.search(pattern, keyword, re.IGNORECASE):
            return ""  # Block if XSS detected
    
    # HTML escape is handled on the client-side/frontend to prevent double escaping
    # keyword = html.escape(keyword)
    
    # Remove ONLY truly dangerous characters
    # Keep: letters, numbers, spaces, emojis, and useful punctuation
    # Remove: < > " ' ; | \
    # We remove these to prevent persistent XSS storage vectors and SQLi issues
    keyword = re.sub(r'[<>"\';\|\\]', '', keyword)
    
    # Trim whitespace and limit length
    keyword = keyword.strip()[:100]
    
    # Minimum length check (at least 2 characters)
    if len(keyword) < 2:
        return ""
    
    return keyword


def sanitize_channel_id(channel_id: str) -> str:
    """
    Sanitize YouTube channel ID.
    
    Valid format: UC followed by 22 alphanumeric characters
    Example: UCuAXFkgsw1L7xaCfnd5JJOw
    
    Returns:
        Sanitized channel ID or empty string if invalid
    """
    if not channel_id:
        return ""
    
    # Remove whitespace
    channel_id = channel_id.strip()
    
    # YouTube channel IDs should be alphanumeric, hyphens, underscores
    # Typically start with "UC" and are 24 characters long
    clean = re.sub(r'[^a-zA-Z0-9_-]', '', channel_id)
    
    # Must be at least 10 characters (some older channels)
    if len(clean) < 10:
        return ""
    
    return clean[:50]  # Cap at 50 chars


def sanitize_email(email: str) -> str:
    """
    Sanitize email address.
    
    Returns:
        Lowercase email or empty string if invalid format
    """
    if not email:
        return ""
    
    # Remove whitespace and convert to lowercase
    email = email.strip().lower()
    
    # Basic email validation pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        return ""
    
    # Additional length checks
    if len(email) < 5 or len(email) > 254:
        return ""
    
    return email


def sanitize_username(username: str) -> str:
    """
    Sanitize username.
    
    Allows: letters, numbers, underscores, hyphens
    Length: 3-30 characters
    
    Returns:
        Sanitized username or empty string if invalid
    """
    if not username:
        return ""
    
    # Remove whitespace
    username = username.strip()
    
    # Only allow alphanumeric, underscores, hyphens
    clean = re.sub(r'[^a-zA-Z0-9_-]', '', username)
    
    # Length requirements
    if len(clean) < 3 or len(clean) > 30:
        return ""
    
    return clean


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets security requirements.
    
    Requirements:
    - At least 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 number
    - At least 1 special character
    
    Returns:
        (is_valid: bool, error_message: str)
    """
    if not password:
        return False, "Password cannot be empty"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least 1 uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least 1 lowercase letter"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least 1 number"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]', password):
        return False, "Password must contain at least 1 special character"
    
    return True, ""


def sanitize_json_input(data: dict, allowed_keys: list) -> dict:
    """
    Sanitize JSON input by filtering allowed keys.
    
    Args:
        data: Input dictionary
        allowed_keys: List of allowed key names
        
    Returns:
        Filtered dictionary with only allowed keys
    """
    if not isinstance(data, dict):
        return {}
    
    return {k: v for k, v in data.items() if k in allowed_keys}


def is_suspicious_input(text: str) -> bool:
    """
    Check if input contains suspicious patterns.
    
    Returns:
        True if suspicious, False otherwise
    """
    if not text:
        return False
    
    suspicious_patterns = [
        r"<script",
        r"javascript:",
        r"onerror\s*=",
        r"onload\s*=",
        r"'\s*OR\s+'",
        r"\"\s*OR\s+\"",
        r"--\s*$",
        r";\s*DROP",
        r";\s*DELETE",
        r"UNION\s+SELECT",
        r"<iframe",
        r"eval\(",
        r"exec\(",
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False


# Rate limiting helpers (simple in-memory implementation)
_rate_limit_store = {}

def is_request_allowed(identifier: str, max_requests: int = 20, window_seconds: int = 3600) -> bool:
    """
    Simple rate limiting check.
    
    Args:
        identifier: Unique identifier (e.g., user_id, IP address)
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds (default 1 hour)
        
    Returns:
        True if request is allowed, False if rate limit exceeded
    """
    import time
    
    current_time = time.time()
    
    if identifier not in _rate_limit_store:
        _rate_limit_store[identifier] = []
    
    # Clean old requests outside the window
    _rate_limit_store[identifier] = [
        req_time for req_time in _rate_limit_store[identifier]
        if current_time - req_time < window_seconds
    ]
    
    # Check if under limit
    if len(_rate_limit_store[identifier]) >= max_requests:
        return False
    
    # Add current request
    _rate_limit_store[identifier].append(current_time)
    return True
