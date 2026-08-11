import os
from datetime import timedelta

from flask import Flask, render_template

from config import Config
from extensions import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    print(f"\n[STARTUP DB URI] SQLALCHEMY_DATABASE_URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}\n")
    app.permanent_session_lifetime = timedelta(days=14)

    # Make sure the instance folder exists for the SQLite file.
    os.makedirs(os.path.join(os.path.dirname(__file__), "instance"), exist_ok=True)

    db.init_app(app)

    # Import models so they're registered before create_all() runs.
    import models  # noqa: F401

    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.tours import tours_bp
    from routes.bookings import bookings_bp
    from routes.profile import profile_bp
    from routes.admin import admin_bp
    from routes.api import api_bp
    from routes.tools import tools_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(tours_bp)
    app.register_blueprint(bookings_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(tools_bp)

    @app.route("/debug/counts")
    def debug_counts():
        from models import Tour, Booking, Feedback
        return {
            "tours": Tour.query.count(),
            "bookings": Booking.query.count(),
            "feedback": Feedback.query.count()
        }

    @app.route("/debug/booking/<int:booking_id>")
    def debug_booking(booking_id):
        from models import Booking
        from flask import session
        security_mode = session.get("security_mode", "ON")

        # DEFENSIVE CONTROL (IDOR Prevention): Require admin session when Security Mode is ON
        if security_mode == "ON" and not session.get("admin_id"):
            return {"error": "Unauthorized Access - IDOR Defense Active. Login required as administrator."}, 403

        b = Booking.query.get(booking_id)
        if not b:
            return {"error": "Booking not found"}, 404
        return {
            "id": b.id,
            "reference": b.reference,
            "status": b.status,
            "user_id": b.user_id,
            "total_amount": b.total_amount,
            "warning": "VULNERABLE DEMO MODE ACTIVE - Unauthenticated IDOR Data Exposure" if security_mode == "OFF" else "Secured Admin Access"
        }

    # ==========================================================================
    # DEFENSIVE SECURITY CONTROL 5: HTTP Security Headers & Anti-Caching Control
    # ==========================================================================
    # [INSECURE / BYPASSABLE CODE PATTERN]:
    #   Omitting security headers:
    #   Response returned without setting X-Frame-Options, CSP, or Cache-Control headers.
    #   ATTACK VECTORS:
    #   - Clickjacking: Attacker embeds site in an invisible <iframe> to trick user actions.
    #   - MIME-Sniffing: Browser interprets text files as executable JavaScript.
    #   - Browser Cache Leak: Sensitive account details remain in browser history on shared PCs.
    #
    # [SECURED & HARDENED CODE PATTERN]:
    #   Enforces X-Frame-Options (SAMEORIGIN), Content-Security-Policy, X-Content-Type-Options (nosniff),
    #   and Anti-Caching headers (no-store, max-age=0) on all HTTP responses.
    # ==========================================================================
    @app.after_request
    def add_header(response):
        from flask import session
        if session.get("security_mode", "ON") == "ON":
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
                "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
                "img-src 'self' data: https:;"
            )
        return response

    @app.template_filter("currency")
    def currency_filter(value):
        try:
            return f"${value:,.2f}"
        except (TypeError, ValueError):
            return value

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    with app.app_context():
        db.create_all()
        # Seed initial promo coupons if missing
        from models import Coupon
        if Coupon.query.count() == 0:
            default_coupons = [
                Coupon(code="SUMMER20", discount_percent=20.0, max_discount=250.0),
                Coupon(code="WELCOME10", discount_percent=10.0, max_discount=100.0),
                Coupon(code="EARLYBIRD", discount_percent=15.0, max_discount=150.0),
                Coupon(code="WAYFARER15", discount_percent=15.0, max_discount=200.0),
            ]
            db.session.add_all(default_coupons)
            db.session.commit()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
