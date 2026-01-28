"""
Security event logging utilities
"""
import logging
from datetime import datetime
from typing import Optional

# Configure security logger
security_logger = logging.getLogger("security")
security_logger.setLevel(logging.INFO)


def log_security_event(
    event_type: str,
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    details: Optional[dict] = None
):
    """
    Log security-relevant events.

    Args:
        event_type: Type of security event (e.g., "login_success", "login_failed")
        user_id: User ID if available
        email: User email if available
        details: Additional event details
    """
    log_data = {
        "event": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "email": email,
        "details": details or {}
    }

    security_logger.info(f"SECURITY_EVENT: {log_data}")
