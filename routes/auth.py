import re

from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from models import db, User

auth_bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[0-9+\-\s()]{7,20}$")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("profile.dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = []
        if len(name) < 2:
            errors.append("Please enter your full name.")
        if not EMAIL_RE.match(email):
            errors.append("Please enter a valid email address.")
        if phone and not PHONE_RE.match(phone):
            errors.append("Please enter a valid phone number.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters long.")
        if password != confirm_password:
            errors.append("Passwords do not match.")
        if User.query.filter_by(email=email).first():
            errors.append("An account with this email already exists.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("register.html", form=request.form)

        user = User(name=name, email=email, phone=phone, role="user")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", form={})


# ==============================================================================
# DEFENSIVE SECURITY CONTROL 3: IP-Based Sliding-Window Rate Limiting
# ==============================================================================
# [INSECURE / BYPASSABLE CODE PATTERN]:
#   No rate limiting on login endpoint:
#   `user = User.query.filter_by(email=email).first()` without checking attempt counts.
#   ATTACK VECTOR: Automated brute-force / dictionary attack tools (Hydra, Burp Intruder)
#   can test thousands of password combinations per second until the account is compromised.
#
# [SECURED & HARDENED CODE PATTERN]:
#   Sliding-window IP tracking (`LOGIN_ATTEMPTS`) blocking client IP with HTTP 429
#   after 5 failed attempts within 60 seconds.
# ==============================================================================
LOGIN_ATTEMPTS = {}
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_WINDOW_SECONDS = 300  # 5 Minutes Lockout
REVOKE_REQUESTS = {}  # Tracks IP lockout revoke requests for Admin approval


def check_rate_limit(ip_address):
    import time
    now = time.time()
    if ip_address in LOGIN_ATTEMPTS:
        attempts = [t for t in LOGIN_ATTEMPTS[ip_address] if now - t < LOCKOUT_WINDOW_SECONDS]
        LOGIN_ATTEMPTS[ip_address] = attempts
        if len(attempts) >= MAX_FAILED_ATTEMPTS:
            return False
    return True


def record_failed_attempt(ip_address):
    import time
    now = time.time()
    if ip_address not in LOGIN_ATTEMPTS:
        LOGIN_ATTEMPTS[ip_address] = []
    LOGIN_ATTEMPTS[ip_address].append(now)


@auth_bp.route("/request-lockout-revoke", methods=["POST"])
def request_lockout_revoke():
    client_ip = request.remote_addr or "127.0.0.1"
    email = request.form.get("email", "").strip()
    REVOKE_REQUESTS[client_ip] = {
        "ip": client_ip,
        "email": email or "Unknown User",
        "status": "Pending Admin Approval",
        "timestamp": datetime.utcnow()
    }
    flash("🔓 Your 5-minute lockout revoke request has been submitted to the Administrator for approval.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        user = User.query.get(session.get("user_id"))
        if user and user.is_admin():
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("profile.dashboard"))

    if request.method == "POST":
        client_ip = request.remote_addr or "127.0.0.1"
        security_mode = session.get("security_mode", "ON")
        email = request.form.get("email", "").strip().lower()

        # Rate Limiting check (Bypassed when Security Mode is OFF)
        if security_mode == "ON" and not check_rate_limit(client_ip):
            has_requested = client_ip in REVOKE_REQUESTS
            revoke_status = REVOKE_REQUESTS.get(client_ip, {}).get("status")
            return render_template(
                "login.html",
                is_locked_out=True,
                client_ip=client_ip,
                email=email,
                has_requested=has_requested,
                revoke_status=revoke_status
            ), 429

        password = request.form.get("password", "")
        remember = request.form.get("remember")

        user = None
        # VULNERABLE DEMO MODE EXECUTION: If security_mode is OFF, execute raw vulnerable SQL string interpolation
        if security_mode == "OFF" and ("'" in email or "OR" in email.upper()):
            try:
                raw_sql = f"SELECT * FROM users WHERE email='{email}'"
                result = db.session.execute(db.text(raw_sql)).first()
                if result:
                    user = User.query.get(result.id)
                    session["user_id"] = user.id
                    if user.is_admin():
                        session["admin_id"] = user.id
                    flash("⚠️ DEMO MODE: SQL Injection payload successfully executed! Logged in without password validation.", "warning")
                    return redirect(url_for("admin.dashboard" if user.is_admin() else "profile.dashboard"))
            except Exception as ex:
                flash(f"⚠️ DEMO MODE: SQL Execution Error: {ex}", "danger")

        # SECURED CODE EXECUTION: Parameterized ORM lookup
        if user is None:
            user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if not user.is_active:
                from routes.utils import log_security_event
                log_security_event("LOGIN_INACTIVE", f"Login attempt on inactive account: {email}")
                flash("Your account has been deactivated. Please contact support.", "danger")
                return render_template("login.html")

            # Clear failed attempts on success, preserving security_mode state
            LOGIN_ATTEMPTS.pop(client_ip, None)
            sec_mode = session.get("security_mode", "ON")
            session.clear()
            session["security_mode"] = sec_mode
            session["user_id"] = user.id
            if user.is_admin():
                session["admin_id"] = user.id

            if remember:
                session.permanent = True

            from routes.utils import log_security_event
            log_security_event("LOGIN_SUCCESS", f"User logged in successfully: {email} (User ID: {user.id})")
            flash(f"Welcome back, {user.name}!", "success")
            
            next_url = request.args.get("next")
            if user.is_admin():
                return redirect(next_url or url_for("admin.dashboard"))
            return redirect(next_url or url_for("profile.dashboard"))

        record_failed_attempt(client_ip)
        from routes.utils import log_security_event
        log_security_event("LOGIN_FAILED", f"Failed login attempt for email: {email}")
        flash("Invalid email or password.", "danger")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("main.home"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        # This is a UI-only stub as requested — no email is actually sent.
        flash(
            "If an account exists for that email, password reset instructions "
            "have been sent.",
            "info",
        )
        return redirect(url_for("auth.login"))
    return render_template("forgot_password.html")
