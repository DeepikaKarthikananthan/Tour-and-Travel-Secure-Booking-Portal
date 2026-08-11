import hmac
import logging
import os
from datetime import datetime
from functools import wraps

from flask import session, redirect, url_for, flash, request

from models import db, User

# Configure Security Audit Logger
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "instance")
os.makedirs(LOG_DIR, exist_ok=True)
SECURITY_LOG_FILE = os.path.join(LOG_DIR, "security_audit.log")

security_logger = logging.getLogger("security_audit")
security_logger.setLevel(logging.INFO)
if not security_logger.handlers:
    handler = logging.FileHandler(SECURITY_LOG_FILE, encoding="utf-8")
    formatter = logging.Formatter("[%(asctime)s] [SECURITY] [%(levelname)s] IP: %(client_ip)s - %(message)s")
    handler.setFormatter(formatter)
    security_logger.addHandler(handler)


# ==============================================================================
# DEFENSIVE SECURITY CONTROL 1: SIEM Security Audit Logging
# ==============================================================================
# [INSECURE / BYPASSABLE CODE PATTERN]:
#   No audit logging or logging sensitive operations without IP tracking:
#   `logging.info("User logged in")` or completely omitting logging.
#   ATTACK VECTOR: Attackers can perform brute-force attacks, unauthorized privilege
#   escalation, or data exfiltration undetected without IP/timestamp attribution.
#
# [SECURED & HARDENED CODE PATTERN]:
#   Active SIEM audit logger capturing client IP (`request.remote_addr`), timestamp,
#   event type (e.g. LOGIN_SUCCESS, UNAUTHORIZED_ACCESS), and exact context.
# ==============================================================================
def log_security_event(event_type, details):
    """Logs security audit events with client IP and context."""
    client_ip = request.remote_addr or "127.0.0.1"
    extra = {"client_ip": client_ip}
    security_logger.info(f"[{event_type}] {details}", extra=extra)


# ==============================================================================
# DEFENSIVE SECURITY CONTROL 2: Timing Side-Channel Attack Mitigation
# ==============================================================================
# [INSECURE / BYPASSABLE CODE PATTERN]:
#   Standard string equality operator comparison:
#   `if token == input_token:` or `if secret_key == user_secret:`
#   ATTACK VECTOR: Standard string comparison (`==`) evaluates character by character
#   and returns `False` immediately on the first non-matching character. An attacker
#   can measure response latency in microseconds (Timing Attack) to guess tokens one
#   character at a time.
#
# [SECURED & HARDENED CODE PATTERN]:
#   `hmac.compare_digest(val1, val2)` performs constant-time string comparison,
#   taking the exact same CPU duration regardless of where non-matching characters lie.
# ==============================================================================
def safe_str_cmp(val1, val2):
    """
    Constant-time string comparison preventing Timing Side-Channel Attacks.
    Uses hmac.compare_digest to prevent microsecond execution time leaks.
    """
    if not isinstance(val1, str) or not isinstance(val2, str):
        return False
    return hmac.compare_digest(val1.encode("utf-8"), val2.encode("utf-8"))


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            log_security_event("UNAUTHORIZED_ACCESS", f"Attempted to access protected endpoint {request.path} without login.")
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        user = get_current_user()
        if user is None or not user.is_active:
            log_security_event("ACCOUNT_INACTIVE", f"User account inactive or missing for ID {session.get('user_id')}.")
            sec_mode = session.get("security_mode", "ON")
            session.clear()
            session["security_mode"] = sec_mode
            flash("Your account is not available. Please log in again.", "danger")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)
    return wrapped


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            log_security_event("ADMIN_UNAUTHORIZED", f"Unauthorized attempt to access admin route {request.path}.")
            flash("Please log in as an administrator.", "warning")
            return redirect(url_for("admin.login"))
        admin = db.session.get(User, session["admin_id"])
        if admin is None or not admin.is_admin() or not admin.is_active:
            log_security_event("ADMIN_SESSION_INVALID", f"Invalid admin session for user {session.get('admin_id')}.")
            session.pop("admin_id", None)
            flash("Admin session invalid. Please log in again.", "danger")
            return redirect(url_for("admin.login"))
        return view_func(*args, **kwargs)
    return wrapped
